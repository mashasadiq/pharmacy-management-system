import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from suppliers.models import Supplier
from inventory.models import Drug
from purchases.models import Purchase
from audit_logs.models import AuditLog

from purchases.services import create_purchase
import json
from django.core.exceptions import ValidationError


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

    def test_purchase_api_returns_updated_stock(self):
        """Verify the API returns the actual inventory after receiving stock."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock

        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "drug_id": self.drug.id,
            "supplier_id": self.supplier.id,
            "quantity": 5,
            "cost_price": "100.00",
            "purchase_date": "2026-11-27",
            "invoice_number": "API-TEST-001",
            "remarks": "API stock verification",
        }

        response = self.client.post(
            reverse("create_purchase"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        response_data = response.json()

        self.assertTrue(response_data["created"])
        self.assertEqual(
            response_data["new_stock"],
            original_stock + 5,
        )

        # Independently verify the actual database stock.
        self.drug.refresh_from_db()

        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock + 5,
        )


    def test_purchase_increases_stock_successfully(self):
        """Verify a new purchase increases inventory exactly once."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        purchase, created = create_purchase(
            drug=self.drug,
            supplier=self.supplier,
            received_by=self.user,
            quantity=5,
            cost_price=Decimal("100.00"),
            purchase_date=date(2026, 11, 27),
            invoice_number="SUCCESS-001",
            idempotency_key=uuid.uuid4(),
        )

        self.assertTrue(created)

        self.drug.refresh_from_db()

        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock + 5,
        )

        self.assertEqual(
            Purchase.objects.count(),
            original_purchase_count + 1,
        )

        self.assertTrue(purchase.purchase_reference)

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                action="CREATE",
                table_name="purchases_purchase",
                record_id=purchase.id,
            ).exists()
        )

    def test_purchase_api_prevents_duplicate_submission(self):
        """Ensure repeated API requests do not record the same purchase twice."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        idempotency_key = str(uuid.uuid4())

        payload = {
            "idempotency_key": idempotency_key,
            "drug_id": self.drug.id,
            "supplier_id": self.supplier.id,
            "quantity": 5,
            "cost_price": "100.00",
            "purchase_date": "2026-11-27",
            "invoice_number": "DUPLICATE-TEST-001",
            "remarks": "Idempotency verification",
        }

        url = reverse("create_purchase")

        first_response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        second_response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)

        first_data = first_response.json()
        second_data = second_response.json()

        self.assertTrue(first_data["created"])
        self.assertFalse(second_data["created"])

        self.assertEqual(
            first_data["purchase_id"],
            second_data["purchase_id"],
        )

        self.drug.refresh_from_db()

        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock + 5,
        )

        self.assertEqual(
            Purchase.objects.count(),
            original_purchase_count + 1,
        )


    def test_purchase_api_rejects_invalid_quantities(self):
        """Invalid quantities must not create purchases or change stock."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_quantities = [0, -1, 1.5, "abc", True]

        for quantity in invalid_quantities:
            with self.subTest(quantity=quantity):
                payload = {
                    "idempotency_key": str(uuid.uuid4()),
                    "drug_id": self.drug.id,
                    "supplier_id": self.supplier.id,
                    "quantity": quantity,
                    "cost_price": "100.00",
                    "purchase_date": "2026-11-27",
                    "invoice_number": "INVALID-QUANTITY",
                }

                response = self.client.post(
                    reverse("create_purchase"),
                    data=json.dumps(payload),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)


    def test_purchase_api_rejects_invalid_cost_prices(self):
        """Invalid cost prices must not create purchases or change stock."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_prices = [
            "0",
            "-10.00",
            "abc",
            "NaN",
            "Infinity",
            "10.999",
            "100000000.00",
        ]

        for cost_price in invalid_prices:
            with self.subTest(cost_price=cost_price):
                payload = {
                    "idempotency_key": str(uuid.uuid4()),
                    "drug_id": self.drug.id,
                    "supplier_id": self.supplier.id,
                    "quantity": 5,
                    "cost_price": cost_price,
                    "purchase_date": "2026-11-27",
                    "invoice_number": "INVALID-PRICE",
                }

                response = self.client.post(
                    reverse("create_purchase"),
                    data=json.dumps(payload),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)


    def test_purchase_api_rejects_invalid_dates(self):
        """Invalid purchase dates must not create records or change stock."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_dates = [
            "27-11-2026",
            "2026/11/27",
            "not-a-date",
            "2026-13-01",
            "2026-02-30",
            "",
        ]

        for purchase_date in invalid_dates:
            with self.subTest(purchase_date=purchase_date):
                payload = {
                    "idempotency_key": str(uuid.uuid4()),
                    "drug_id": self.drug.id,
                    "supplier_id": self.supplier.id,
                    "quantity": 5,
                    "cost_price": "100.00",
                    "purchase_date": purchase_date,
                    "invoice_number": "INVALID-DATE",
                }

                response = self.client.post(
                    reverse("create_purchase"),
                    data=json.dumps(payload),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)

    def test_purchase_service_rejects_invalid_dates(self):
        """The service must independently validate purchase dates."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_dates = [
            "27-11-2026",
            "2026/11/27",
            "not-a-date",
            "2026-13-01",
            "2026-02-30",
            "",
            None,
            12345,
        ]

        for purchase_date in invalid_dates:
            with self.subTest(purchase_date=purchase_date):
                with self.assertRaises(ValidationError):
                    create_purchase(
                        drug=self.drug,
                        supplier=self.supplier,
                        received_by=self.user,
                        quantity=5,
                        cost_price=Decimal("100.00"),
                        purchase_date=purchase_date,
                        invoice_number="SERVICE-DATE-VALIDATION",
                        idempotency_key=uuid.uuid4(),
                    )

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)

    def test_purchase_api_requires_idempotency_key(self):
        """Reject purchase requests with missing or empty idempotency keys."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        payload = {
            "drug_id": self.drug.id,
            "supplier_id": self.supplier.id,
            "quantity": 5,
            "cost_price": "100.00",
            "purchase_date": "2026-11-27",
            "invoice_number": "MISSING-KEY-TEST",
        }

        test_payloads = [
            payload.copy(),
            {**payload, "idempotency_key": ""},
        ]

        for test_data in test_payloads:
            with self.subTest(idempotency_key=test_data.get("idempotency_key")):
                response = self.client.post(
                    reverse("create_purchase"),
                    data=json.dumps(test_data),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)


    def test_duplicate_purchase_does_not_increase_stock_twice(self):
        """Verify retrying a purchase does not duplicate stock or records."""

        idempotency_key = uuid.uuid4()

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        purchase_data = {
            "drug": self.drug,
            "supplier": self.supplier,
            "received_by": self.user,
            "quantity": 5,
            "cost_price": Decimal("100.00"),
            "purchase_date": date(2026, 11, 27),
            "invoice_number": "DUPLICATE-001",
            "idempotency_key": idempotency_key,
        }

        first_purchase, first_created = create_purchase(**purchase_data)
        second_purchase, second_created = create_purchase(**purchase_data)

        self.drug.refresh_from_db()

        self.assertTrue(first_created)
        self.assertFalse(second_created)

        self.assertEqual(first_purchase.id, second_purchase.id)

        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock + 5,
        )

        self.assertEqual(
            Purchase.objects.count(),
            original_purchase_count + 1,
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

    @patch(
        "purchases.services.check_low_stock",
        side_effect=RuntimeError("Simulated notification failure"),
    )
    def test_purchase_rolls_back_when_notification_fails(
        self,
        mock_check_low_stock,
    ):
        """A notification failure must roll back purchase and stock changes."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()
        original_audit_count = AuditLog.objects.count()

        with self.assertRaisesRegex(
            RuntimeError,
            "Simulated notification failure",
        ):
            create_purchase(
                drug=self.drug,
                supplier=self.supplier,
                received_by=self.user,
                quantity=5,
                cost_price=Decimal("100.00"),
                purchase_date=date(2026, 11, 27),
                invoice_number="NOTIFICATION-FAIL-001",
                idempotency_key=uuid.uuid4(),
            )

        self.drug.refresh_from_db()

        self.assertEqual(
            self.drug.quantity_in_stock,
            original_stock,
        )

        self.assertEqual(
            Purchase.objects.count(),
            original_purchase_count,
        )

        self.assertEqual(
            AuditLog.objects.count(),
            original_audit_count,
        )

        mock_check_low_stock.assert_called_once()


    def test_purchase_service_rejects_invalid_quantities(self):
        """The service must independently enforce whole-number quantities."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_quantities = [0, -1, 1.5, "5", "abc", True, None]

        for quantity in invalid_quantities:
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValidationError):
                    create_purchase(
                        drug=self.drug,
                        supplier=self.supplier,
                        received_by=self.user,
                        quantity=quantity,
                        cost_price=Decimal("100.00"),
                        purchase_date=date(2026, 11, 27),
                        invoice_number="SERVICE-VALIDATION",
                        idempotency_key=uuid.uuid4(),
                    )

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)

    def test_purchase_api_rejects_malformed_idempotency_keys(self):
        """Malformed UUID keys must not create purchases or change stock."""

        self.client.force_login(self.user)

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_keys = ["not-a-uuid", "12345", "invalid-key"]

        for key in invalid_keys:
            with self.subTest(key=key):
                payload = {
                    "idempotency_key": key,
                    "drug_id": self.drug.id,
                    "supplier_id": self.supplier.id,
                    "quantity": 5,
                    "cost_price": "100.00",
                    "purchase_date": "2026-11-27",
                }

                response = self.client.post(
                    reverse("create_purchase"),
                    data=json.dumps(payload),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)


    def test_purchase_service_rejects_invalid_cost_prices(self):
        """The service must independently validate purchase cost prices."""

        original_stock = self.drug.quantity_in_stock
        original_purchase_count = Purchase.objects.count()

        invalid_prices = [
            "0",
            "-10.00",
            "abc",
            "NaN",
            "Infinity",
            "10.999",
            "100000000.00",
        ]

        for cost_price in invalid_prices:
            with self.subTest(cost_price=cost_price):
                with self.assertRaises(ValidationError):
                    create_purchase(
                        drug=self.drug,
                        supplier=self.supplier,
                        received_by=self.user,
                        quantity=5,
                        cost_price=cost_price,
                        purchase_date=date(2026, 11, 27),
                        invoice_number="SERVICE-PRICE-VALIDATION",
                        idempotency_key=uuid.uuid4(),
                    )

        self.drug.refresh_from_db()

        self.assertEqual(self.drug.quantity_in_stock, original_stock)
        self.assertEqual(Purchase.objects.count(), original_purchase_count)


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