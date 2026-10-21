
from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Drug
from suppliers.models import Supplier


User = get_user_model()


class DrugCreationSecurityTests(TestCase):
    """Test administrator-only access to drug creation."""

    def setUp(self):
        """Create admin and pharmacist accounts and a supplier."""

        self.admin = User.objects.create_user(
            username="inventory_admin",
            password="TestPassword123!",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="inventory_pharmacist",
            password="TestPassword123!",
            role="PHARMACIST",
        )

        self.supplier = Supplier.objects.create(
            company_name="Test Medical Supplies",
            contact_person="Test Contact",
            phone="0712345678",
            email="supplier@test.com",
            address="Test Address",
            city="Mombasa",
            country="Kenya",
        )

        self.create_url = reverse("create_drug")

    def test_pharmacist_cannot_access_drug_creation_page(self):
        """Pharmacists must not access the drug creation page."""

        self.client.force_login(self.pharmacist)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 403)

    def test_pharmacist_cannot_create_drug_using_post(self):
        """Pharmacists must not create drugs through POST requests."""

        self.client.force_login(self.pharmacist)

        initial_count = Drug.objects.count()

        response = self.client.post(
            self.create_url,
            {
                "supplier": self.supplier.id,
                "name": "Test Paracetamol",
                "generic_name": "Paracetamol",
                "brand": "Test Brand",
                "batch_number": "TEST001",
                "category": "Tablet",
                "unit": "Box",
                "cost_price": "100.00",
                "selling_price": "150.00",
                "quantity_in_stock": 50,
                "minimum_stock": 10,
                "expiry_date": date(2028, 12, 31),
                "description": "Security test drug",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Drug.objects.count(), initial_count)

    def test_admin_can_access_drug_creation_page(self):
        """Administrators must be allowed to access drug creation."""

        self.client.force_login(self.admin)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)