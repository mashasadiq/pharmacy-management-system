from datetime import date

from django.db.models import F

from inventory.models import Drug
from patients.models import Patient
from purchases.models import Purchase
from sales.models import Sale


class ReportService:
    """Provides reusable queries for generating pharmacy reports."""

    
    @staticmethod
    def daily_sales_report(report_date):
        """Return completed sales and total revenue for a specific date."""
        sales = Sale.objects.filter(
            sale_date__date=report_date,
            status=Sale.Status.COMPLETED,
        )

        total_revenue = sum(
            sale.total_amount for sale in sales
        )

        return sales, total_revenue


    @staticmethod
    def monthly_sales_report(year, month):
        """Return completed sales and total revenue for a specific month."""
        sales = Sale.objects.filter(
            sale_date__year=year,
            sale_date__month=month,
            status=Sale.Status.COMPLETED,
        )

        total_revenue = sum(
            sale.total_amount for sale in sales
        )

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
        """Return drugs whose expiry date has already passed."""
        return Drug.objects.filter(
            expiry_date__lt=date.today()
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
        )

        total_units = sum(
            purchase.quantity for purchase in purchases
        )

        total_cost = sum(
            purchase.quantity * purchase.cost_price
            for purchase in purchases
        )

        for purchase in purchases:
            purchase.total_cost = purchase.quantity * purchase.cost_price

        return purchases, total_units, total_cost