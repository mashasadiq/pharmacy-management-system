from django.utils import timezone

from django.db.models import F, Sum

from inventory.models import Drug
from patients.models import Patient
from purchases.models import Purchase
from sales.models import Sale

from decimal import Decimal


class ReportService:
    """Provides reusable queries for generating pharmacy reports."""

    
    @staticmethod
    def daily_sales_report(report_date):
        """Return completed sales and total revenue for a specific date."""
        sales = Sale.objects.select_related(
            "patient",
            "pharmacist",
        ).filter(
            sale_date__date=report_date,
            status=Sale.Status.COMPLETED,
        )

        
        total_revenue = sales.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        return sales, total_revenue


    @staticmethod
    def monthly_sales_report(year, month):
        """Return completed sales and total revenue for a specific month."""
        sales = Sale.objects.select_related(
            "patient",
            "pharmacist",
        ).filter(
            sale_date__year=year,
            sale_date__month=month,
            status=Sale.Status.COMPLETED,
        )

        total_revenue = sales.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        return sales, total_revenue


    @staticmethod
    def inventory_report():
        """Return all drugs currently recorded in inventory."""
        return Drug.objects.all()

    @staticmethod
    def low_stock_report():
        """Return drugs whose stock is at or below the minimum level."""
        return Drug.objects.filter(
            quantity_in_stock__lte=F("minimum_stock")
        )

    @staticmethod
    def expired_drugs_report():
        return Drug.objects.select_related("supplier").filter(
            expiry_date__lt=timezone.localdate()
        )

    @staticmethod
    def patient_report():
        """Return all registered patients."""
        return Patient.objects.all()

    
    @staticmethod
    def purchase_report():
        """Return purchases with total units and total purchase cost."""

        purchases = Purchase.objects.select_related(
            "drug",
            "supplier",
            "received_by",
        ).annotate(
            total_cost=F("quantity") * F("cost_price")
        )

        totals = purchases.aggregate(
            total_units=Sum("quantity"),
            total_cost=Sum(F("quantity") * F("cost_price")),
        )

        total_units = totals["total_units"] or 0
        total_cost = totals["total_cost"] or Decimal("0.00")

        return purchases, total_units, total_cost