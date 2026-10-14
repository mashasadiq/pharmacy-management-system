
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from suppliers.models import Supplier
from inventory.models import Drug
from patients.models import Patient
from sales.models import Sale, SaleItem
from audit_logs.models import AuditLog


User = get_user_model()


class SaleTransactionTests(TestCase):
    """Test transaction integrity during sale completion."""

    def setUp(self):
        # Create a supplier.
        self.supplier = Supplier.objects.create(
            company_name="Sale Test Pharmaceuticals",
            contact_person="Test Contact",
            phone="0712345678",
            email="sale.test@example.com",
            address="Test Address",
            city="Mombasa",
        )

        # Create a pharmacist.
        self.user = User.objects.create_user(
            username="sale_tester",
            password="test-password",
            role="PHARMACIST",
        )

        # Create a patient.
        self.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            gender="Male",
            date_of_birth=date(1995, 5, 10),
            phone="0712345678",
            created_by=self.user,
        )

        # Create a drug with known starting stock.
        self.drug = Drug.objects.create(
            supplier=self.supplier,
            name="Test Paracetamol",
            generic_name="Paracetamol",
            brand="Test Brand",
            batch_number="SALE-TEST-001",
            category="Tablet",
            unit="Box",
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
            quantity_in_stock=40,
            minimum_stock=10,
            expiry_date=date(2028, 12, 31),
        )

        # Create a pending sale.
        self.sale = Sale.objects.create(
            patient=self.patient,
            pharmacist=self.user,
            payment_method=Sale.PaymentMethod.CASH,
            total_amount=Decimal("300.00"),
            status=Sale.Status.PENDING,
        )

        # Add two units to the sale.
        SaleItem.objects.create(
            sale=self.sale,
            drug=self.drug,
            quantity=2,
            unit_price=Decimal("150.00"),
        )

        self.client.login(
            username="sale_tester",
            password="test-password",
        )

    @patch(
        "sales.views.AuditLog.objects.create",
        side_effect=RuntimeError("Simulated audit-log failure"),
    )
    def test_sale_completion_rolls_back_when_audit_fails(
        self,
        mock_audit_create,
    ):
        """Verify stock and sale details roll back after audit failure."""

        original_stock = self.drug.quantity_in_stock
        original_audit_count = AuditLog.objects.count()

        # Attempt to complete the sale while forcing audit creation to fail.
        response = self.client.post(
            f"/sales/{self.sale.id}/complete/"
        )

        # The unexpected failure should produce HTTP 500.
        self.assertEqual(response.status_code, 500)

        # Reload the sale and drug from the database.
        self.sale.refresh_from_db()
        self.drug.refresh_from_db()

        # Sale status must remain Pending.
        self.assertEqual(
            self.sale.status,
            Sale.Status.PENDING,
        )

        # Invoice number must remain unset.
        self.assertIsNone(self.sale.invoice_number)

        # Stock must return to its original quantity.
        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock,
        )

        # No audit record should have been committed.
        self.assertEqual(
            AuditLog.objects.count(),
            original_audit_count,
        )

        # Confirm that audit creation was attempted.
        mock_audit_create.assert_called_once()



    @patch(
        "sales.views.AuditLog.objects.create",
        side_effect=RuntimeError("Simulated audit-log failure"),
    )
    def test_sale_cancellation_rolls_back_when_audit_fails(
        self,
        mock_audit_create,
    ):
        """Verify stock restoration and cancellation roll back on failure."""

        # Prepare a completed sale.
        self.sale.status = Sale.Status.COMPLETED
        self.sale.invoice_number = (
            f"INV-{self.sale.sale_date:%Y%m%d}-{self.sale.id:06d}"
        )
        self.sale.save(
            update_fields=["status", "invoice_number"]
        )

        # The sale already deducted two units from the original stock.
        self.drug.quantity_in_stock = 38
        self.drug.save(update_fields=["quantity_in_stock"])

        # Cancellation is restricted to administrators.
        self.user.role = "ADMIN"
        self.user.save(update_fields=["role"])
        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_invoice = self.sale.invoice_number
        original_audit_count = AuditLog.objects.count()

        # Attempt cancellation while forcing audit creation to fail.
        response = self.client.post(
            f"/sales/{self.sale.id}/cancel/"
        )

        self.assertEqual(response.status_code, 500)

        # Reload database records.
        self.sale.refresh_from_db()
        self.drug.refresh_from_db()

        # Sale must remain Completed.
        self.assertEqual(
            self.sale.status,
            Sale.Status.COMPLETED,
        )

        # Invoice must remain unchanged.
        self.assertEqual(
            self.sale.invoice_number,
            original_invoice,
        )

        # Restored stock must be rolled back.
        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock,
        )

        # No partial audit record should remain.
        self.assertEqual(
            AuditLog.objects.count(),
            original_audit_count,
        )

        mock_audit_create.assert_called_once()