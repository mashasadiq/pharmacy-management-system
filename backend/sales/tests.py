
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
from django.urls import reverse

from datetime import datetime, time, timedelta
from django.utils import timezone

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


    def test_pharmacist_cannot_cancel_completed_sale(self):
        """Ensure pharmacists cannot cancel completed sales."""

        # Prepare a completed sale with stock already deducted.
        self.sale.status = Sale.Status.COMPLETED
        self.sale.invoice_number = (
            f"INV-{self.sale.sale_date:%Y%m%d}-{self.sale.id:06d}"
        )
        self.sale.save(update_fields=["status", "invoice_number"])

        self.drug.quantity_in_stock = 38
        self.drug.save(update_fields=["quantity_in_stock"])

        original_audit_count = AuditLog.objects.count()

        # The logged-in user is still a pharmacist.
        response = self.client.post(
            f"/sales/{self.sale.id}/cancel/"
        )

        self.assertEqual(response.status_code, 403)

        # Verify that nothing was changed.
        self.sale.refresh_from_db()
        self.drug.refresh_from_db()

        self.assertEqual(self.sale.status, Sale.Status.COMPLETED)
        self.assertEqual(self.drug.quantity_in_stock, 38)
        self.assertEqual(AuditLog.objects.count(), original_audit_count)


    def test_admin_can_delete_pending_sale(self):
        """Ensure administrators can delete pending sales."""

        admin = User.objects.create_user(
            username="sale_admin",
            password="test-password",
            role="ADMIN",
        )
        self.client.force_login(admin)

        response = self.client.post(
            f"/sales/{self.sale.id}/delete/"
        )

        self.assertEqual(response.status_code, 200)

        # Confirm the sale was deleted.
        self.assertFalse(
            Sale.objects.filter(id=self.sale.id).exists()
        )

        # Confirm the deletion was recorded.
        self.assertTrue(
            AuditLog.objects.filter(
                user=admin,
                action="DELETE",
                table_name="sales_sale",
                record_id=self.sale.id,
            ).exists()
        )



    def test_pharmacist_cannot_delete_pending_sale(self):
        """Ensure pharmacists cannot delete pending sales."""

        original_audit_count = AuditLog.objects.count()

        response = self.client.post(
            f"/sales/{self.sale.id}/delete/"
        )

        self.assertEqual(response.status_code, 403)

        # Confirm the pending sale still exists.
        self.assertTrue(
            Sale.objects.filter(id=self.sale.id).exists()
        )

        # Confirm no audit record was created.
        self.assertEqual(
            AuditLog.objects.count(),
            original_audit_count,
        )

    
    def test_anonymous_user_cannot_view_sale_detail(self):
        """Unauthenticated users must be redirected to login."""
        self.client.logout()

        response = self.client.get(
            reverse("sale_detail", args=[self.sale.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_pharmacist_can_view_sale_detail(self):
        """Pharmacists can access individual sale details."""
        response = self.client.get(
            reverse("sale_detail", args=[self.sale.id])
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_sale_detail(self):
        """Administrators can access individual sale details."""
        admin = User.objects.create_user(
            username="detail_admin",
            password="test-password",
            role="ADMIN",
        )

        self.client.force_login(admin)

        response = self.client.get(
            reverse("sale_detail", args=[self.sale.id])
        )

        self.assertEqual(response.status_code, 200)


class SalesTimezoneTests(TestCase):
    """Test daily sales filtering against Nairobi date boundaries."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="timezone_tester",
            password="test-password",
            role="PHARMACIST",
        )

        self.patient = Patient.objects.create(
            first_name="Timezone",
            last_name="Patient",
            gender="Male",
            date_of_birth=date(1995, 5, 10),
            created_by=self.user,
        )

        self.report_date = date(2026, 10, 19)

        self.start = timezone.make_aware(
            datetime.combine(self.report_date, time.min)
        )

        self.end = timezone.make_aware(
            datetime.combine(
                self.report_date + timedelta(days=1),
                time.min,
            )
        )

    def create_sale_at(self, sale_datetime):
        """Create a sale and override its automatic timestamp."""

        sale = Sale.objects.create(
            patient=self.patient,
            pharmacist=self.user,
            payment_method=Sale.PaymentMethod.CASH,
            total_amount=Decimal("100.00"),
            status=Sale.Status.COMPLETED,
        )

        Sale.objects.filter(id=sale.id).update(
            sale_date=sale_datetime
        )

        return sale

    def test_daily_filter_respects_nairobi_midnight_boundaries(self):
        """Only sales within the Nairobi calendar day should match."""

        before_midnight = self.create_sale_at(
            self.start - timedelta(seconds=1)
        )

        at_midnight = self.create_sale_at(self.start)

        before_next_midnight = self.create_sale_at(
            self.end - timedelta(seconds=1)
        )

        after_midnight = self.create_sale_at(self.end)

        sales = Sale.objects.filter(
            sale_date__date=self.report_date,
            status=Sale.Status.COMPLETED,
        )

        self.assertQuerySetEqual(
            sales.order_by("id"),
            [at_midnight, before_next_midnight],
            transform=lambda sale: sale,
        )

        self.assertNotIn(before_midnight, sales)
        self.assertNotIn(after_midnight, sales)

    def test_monthly_filter_respects_nairobi_month_boundaries(self):
        """Only sales within the Nairobi calendar month should match."""

        november_start = timezone.make_aware(
            datetime(2026, 11, 1, 0, 0)
        )

        december_start = timezone.make_aware(
            datetime(2026, 12, 1, 0, 0)
        )

        # Sales immediately around the November boundaries.
        before_november = self.create_sale_at(
            november_start - timedelta(seconds=1)
        )

        at_november_start = self.create_sale_at(november_start)

        before_december = self.create_sale_at(
            december_start - timedelta(seconds=1)
        )

        at_december_start = self.create_sale_at(december_start)

        sales = Sale.objects.filter(
            sale_date__year=2026,
            sale_date__month=11,
            status=Sale.Status.COMPLETED,
        )

        self.assertCountEqual(
            list(sales),
            [at_november_start, before_december],
        )
