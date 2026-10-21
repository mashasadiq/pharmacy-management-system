from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal

from suppliers.models import Supplier
from inventory.models import Drug
from purchases.models import Purchase
from unittest.mock import patch

from django.utils import timezone
from datetime import date

from patients.models import Patient
from sales.models import Sale
from reports.services import ReportService

User = get_user_model()


class ReportAccessTests(TestCase):
    """Test role-based access to pharmacy reports."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="report_admin",
            password="test-password",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="report_pharmacist",
            password="test-password",
            role="PHARMACIST",
        )

    def test_anonymous_user_cannot_access_reports(self):
        report_urls = [
            "/reports/",
            "/reports/inventory/",
            "/reports/low-stock/",
            "/reports/expired/",
            "/reports/patients/",
            "/reports/purchases/",
            "/reports/sales/daily/",
            "/reports/sales/monthly/",
        ]

        for url in report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_pharmacist_can_access_general_reports(self):
        self.client.force_login(self.pharmacist)

        report_urls = [
            "/reports/",
            "/reports/inventory/",
            "/reports/low-stock/",
            "/reports/expired/",
        ]

        for url in report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_pharmacist_cannot_access_admin_reports(self):
        self.client.force_login(self.pharmacist)

        report_urls = [
            "/reports/patients/",
            "/reports/purchases/",
            "/reports/sales/daily/",
            "/reports/sales/monthly/",
        ]

        for url in report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_admin_can_access_all_reports(self):
        self.client.force_login(self.admin)

        report_urls = [
            "/reports/",
            "/reports/inventory/",
            "/reports/low-stock/",
            "/reports/expired/",
            "/reports/patients/",
            "/reports/purchases/",
            "/reports/sales/daily/",
            "/reports/sales/monthly/",
        ]

        for url in report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

class ReportCalculationTests(TestCase):
    """Test revenue calculations in pharmacy reports."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="report_tester",
            password="test-password",
            role="ADMIN",
        )

        self.patient = Patient.objects.create(
            first_name="Report",
            last_name="Patient",
            gender="Male",
            date_of_birth=date(1995, 5, 10),
            created_by=self.user,
        )

        self.report_date = timezone.localdate()

    def create_sale(self, amount, status):
        """Create a sale with a specified amount and status."""

        return Sale.objects.create(
            patient=self.patient,
            pharmacist=self.user,
            payment_method=Sale.PaymentMethod.CASH,
            total_amount=Decimal(amount),
            status=status,
        )

    def create_sample_sales(self):
        """Create sales with different statuses for testing."""

        self.create_sale("100.00", Sale.Status.COMPLETED)
        self.create_sale("250.00", Sale.Status.COMPLETED)
        self.create_sale("500.00", Sale.Status.PENDING)
        self.create_sale("700.00", Sale.Status.CANCELLED)

    def test_daily_report_calculates_completed_revenue(self):
        """Daily revenue should include completed sales only."""

        self.create_sample_sales()

        sales, total_revenue = ReportService.daily_sales_report(
            self.report_date
        )

        self.assertEqual(sales.count(), 2)
        self.assertEqual(total_revenue, Decimal("350.00"))

    def test_monthly_report_calculates_completed_revenue(self):
        """Monthly revenue should include completed sales only."""

        self.create_sample_sales()

        sales, total_revenue = ReportService.monthly_sales_report(
            self.report_date.year,
            self.report_date.month,
        )

        self.assertEqual(sales.count(), 2)
        self.assertEqual(total_revenue, Decimal("350.00"))

    def test_empty_reports_return_zero_revenue(self):
        """Reports should return zero when no completed sales exist."""

        _, daily_revenue = ReportService.daily_sales_report(
            self.report_date
        )

        _, monthly_revenue = ReportService.monthly_sales_report(
            self.report_date.year,
            self.report_date.month,
        )

        self.assertEqual(daily_revenue, 0)
        self.assertEqual(monthly_revenue, 0)

class PurchaseReportCalculationTests(TestCase):
    """Test database aggregation of purchase reports."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="purchase_report_tester",
            password="test-password",
            role="ADMIN",
        )

        self.supplier = Supplier.objects.create(
            company_name="Report Test Pharmaceuticals",
            contact_person="Test Contact",
            phone="0712345678",
            email="report.test@example.com",
            address="Test Address",
            city="Mombasa",
        )

        self.drug = Drug.objects.create(
            supplier=self.supplier,
            name="Report Test Paracetamol",
            generic_name="Paracetamol",
            brand="Test Brand",
            batch_number="REPORT-TEST-001",
            category="Tablet",
            unit="Box",
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
            quantity_in_stock=20,
            minimum_stock=10,
            expiry_date=date(2028, 12, 31),
        )

    def create_purchase(self, quantity, cost_price):
        """Create a purchase with a known quantity and cost."""

        return Purchase.objects.create(
            drug=self.drug,
            supplier=self.supplier,
            received_by=self.user,
            quantity=quantity,
            cost_price=Decimal(cost_price),
            purchase_date=date(2026, 10, 19),
        )

    def test_purchase_report_calculates_correct_totals(self):
        """Calculate total units and total purchase cost correctly."""

        self.create_purchase(5, "100.00")
        self.create_purchase(3, "200.00")

        purchases, total_units, total_cost = (
            ReportService.purchase_report()
        )

        self.assertEqual(purchases.count(), 2)
        self.assertEqual(total_units, 8)
        self.assertEqual(total_cost, Decimal("1100.00"))

        purchase_costs = {
            purchase.quantity: purchase.total_cost
            for purchase in purchases
        }

        self.assertEqual(
            purchase_costs,
            {
                5: Decimal("500.00"),
                3: Decimal("600.00"),
            },
        )

    def test_empty_purchase_report_returns_zero_totals(self):
        """An empty purchase report should return zero totals."""

        purchases, total_units, total_cost = (
            ReportService.purchase_report()
        )

        self.assertEqual(purchases.count(), 0)
        self.assertEqual(total_units, 0)
        self.assertEqual(total_cost, Decimal("0.00"))

class MonthlySalesReportValidationTests(TestCase):
    """Test validation of monthly sales report inputs."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="monthly_report_admin",
            password="test-password",
            role="ADMIN",
        )
        self.client.force_login(self.admin)

    @patch("reports.views.ReportService.monthly_sales_report")
    def test_valid_month_and_year_generate_report(self, mock_report):
        mock_report.return_value = ([], Decimal("0.00"))

        current_year = timezone.localdate().year

        response = self.client.get(
            "/reports/sales/monthly/",
            {"year": str(current_year), "month": "10"},
        )

        self.assertEqual(response.status_code, 200)
        mock_report.assert_called_once_with(current_year, 10)
        self.assertIsNone(response.context["error"])

    def test_invalid_inputs_do_not_generate_report(self):
        invalid_inputs = [
            {"year": "2026", "month": "0"},
            {"year": "2026", "month": "13"},
            {"year": "abc", "month": "10"},
            {"year": "2026", "month": "abc"},
            {"year": "1999", "month": "10"},
            {
                "year": str(timezone.localdate().year + 1),
                "month": "10",
            },
            {"year": "2026"},
            {"month": "10"},
        ]

        for params in invalid_inputs:
            with self.subTest(params=params):
                with patch(
                    "reports.views.ReportService.monthly_sales_report"
                ) as mock_report:
                    response = self.client.get(
                        "/reports/sales/monthly/",
                        params,
                    )

                    self.assertEqual(response.status_code, 200)
                    self.assertIsNotNone(response.context["error"])
                    mock_report.assert_not_called()