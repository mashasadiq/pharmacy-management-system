
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from suppliers.models import Supplier
from inventory.models import Drug
from purchases.models import Purchase
from audit_logs.models import AuditLog

from purchases.services import create_purchase
import json


User = get_user_model()


class PurchaseTransactionTests(TestCase):
    """Tests transaction integrity when purchase creation fails."""

    def setUp(self):
        # Create a supplier for the test purchase.
        self.supplier = Supplier.objects.create(
            company_name="Test Pharmaceuticals",
            contact_person="Test Contact",
            phone="0712345678",
            email="test.supplier@example.com",
            address="Test Address",
            city="Mombasa",
        )

        # Create an administrator who records the purchase.
        self.user = User.objects.create_user(
            username="purchase_tester",
            password="test-password",
            role="ADMIN",
        )

            #pharmacist
        self.pharmacist = User.objects.create_user(
            username="purchase_pharmacist",
            password="test-password",
            role="PHARMACIST",
        )


        # Create a drug with a known starting stock.
        self.drug = Drug.objects.create(
            supplier=self.supplier,
            name="Test Amoxicillin",
            generic_name="Amoxicillin",
            brand="Test Brand",
            batch_number="TEST-BATCH-001",
            category="Capsule",
            unit="Box",
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
            quantity_in_stock=20,
            minimum_stock=10,
            expiry_date=date(2028, 12, 31),
        )

        # Create a purchase record for purchase-detail access tests.
        self.purchase = Purchase.objects.create(
            drug=self.drug,
            supplier=self.supplier,
            received_by=self.user,
            quantity=5,
            cost_price=Decimal("100.00"),
            purchase_date=date(2026, 10, 14),
            invoice_number="TEST-INV-001",
            idempotency_key=uuid.uuid4(),
            remarks="Test purchase",
        )    

    @patch(
        "purchases.services.AuditLog.objects.create",
        side_effect=RuntimeError("Simulated audit-log failure"),
    )
    def test_purchase_rolls_back_when_audit_creation_fails(
        self,
        mock_audit_create,
    ):
        """Verify that a failed audit log rolls back purchase and stock."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()
        original_audit_count = AuditLog.objects.count()

        with self.assertRaisesRegex(
            RuntimeError,
            "Simulated audit-log failure",
        ):
            create_purchase(
                drug=self.drug,
                supplier=self.supplier,
                received_by=self.user,
                quantity=5,
                cost_price=Decimal("100.00"),
                purchase_date=date(2026, 10, 14),
                invoice_number="TEST-INV-001",
                idempotency_key=uuid.uuid4(),
            )

        # Reload the drug from the database.
        self.drug.refresh_from_db()

        # The stock increment must have been rolled back.
        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock,
        )

        # The newly created purchase must not exist.
        self.assertEqual(
            Purchase.objects.count(),
            original_purchase_count,
        )

        # No audit record should have been committed.
        self.assertEqual(
            AuditLog.objects.count(),
            original_audit_count,
        )

        # Confirm that the audit creation failure was triggered.
        mock_audit_create.assert_called_once()

    
    def test_pharmacist_cannot_access_purchase_creation_page(self):
        """Only administrators can access the purchase creation page."""

        self.client.force_login(self.pharmacist)

        response = self.client.get(
            "/purchases/create/"
        )

        self.assertEqual(response.status_code, 403)

    def test_pharmacist_cannot_submit_purchase_through_api(self):
        """Pharmacists cannot create purchases through the API."""

        self.client.force_login(self.pharmacist)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "drug_id": self.drug.id,
            "supplier_id": self.supplier.id,
            "quantity": 5,
            "cost_price": "100.00",
            "purchase_date": "2026-10-14",
            "invoice_number": "UNAUTHORIZED-001",
            "remarks": "Security test",
        }

        response = self.client.post(
            "/purchases/api/create/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.drug.refresh_from_db()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)

    
    def test_pharmacist_cannot_access_purchase_list(self):
        self.client.force_login(self.pharmacist)

        response = self.client.get("/purchases/")

        self.assertEqual(response.status_code, 403)


    def test_pharmacist_cannot_access_purchase_detail(self):
        self.client.force_login(self.pharmacist)

        response = self.client.get(f"/purchases/{self.purchase.id}/")

        self.assertEqual(response.status_code, 403)


    def test_admin_can_access_purchase_list(self):
        self.client.force_login(self.user)

        response = self.client.get("/purchases/")

        self.assertEqual(response.status_code, 200)


    def test_admin_can_access_purchase_detail(self):
        self.client.force_login(self.user)

        response = self.client.get(f"/purchases/{self.purchase.id}/")

        self.assertEqual(response.status_code, 200)
    
    
    def test_admin_can_access_purchase_creation_page(self):
        """Administrators can access the purchase creation page."""

        self.client.force_login(self.user)

        response = self.client.get(
            "/purchases/create/"
        )

        self.assertEqual(response.status_code, 200)