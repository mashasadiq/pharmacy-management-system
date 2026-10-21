from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .services import ReportService

from accounts.decorators import admin_required
from django.utils import timezone

@login_required
def reports_home(request):
    """Display links to all available pharmacy reports."""
    return render(
        request,
        "reports/reports_home.html",
    )

@login_required
def inventory_report(request):
    """Display the current pharmacy inventory report."""
    drugs = ReportService.inventory_report()

    return render(
        request,
        "reports/inventory_report.html",
        {"drugs": drugs},
    )

@login_required
def low_stock_report(request):
    """Display drugs whose stock is at or below the minimum level."""
    drugs = ReportService.low_stock_report()

    return render(
        request,
        "reports/low_stock_report.html",
        {"drugs": drugs},
    )

@login_required
def expired_drugs_report(request):
    """Display drugs that have already expired."""
    drugs = ReportService.expired_drugs_report()

    return render(
        request,
        "reports/expired_drugs_report.html",
        {"drugs": drugs},
    )

@admin_required
def patient_report(request):
    """Display all registered patients."""
    patients = ReportService.patient_report()

    return render(
        request,
        "reports/patient_report.html",
        {"patients": patients},
    )

@admin_required
def purchase_report(request):
    """Display purchase records and purchase summary."""
    purchases, total_units, total_cost = ReportService.purchase_report()

    return render(
        request,
        "reports/purchase_report.html",
        {
            "purchases": purchases,
            "total_units": total_units,
            "total_cost": total_cost,
        },
    )

@admin_required
def daily_sales_report(request):
    """Display completed sales and revenue for a selected date."""
    report_date = request.GET.get("date")

    sales = None
    total_revenue = 0

    if report_date:
        sales, total_revenue = ReportService.daily_sales_report(
            report_date
        )

    return render(
        request,
        "reports/daily_sales_report.html",
        {
            "sales": sales,
            "report_date": report_date,
            "total_revenue": total_revenue,
        },
    )


@admin_required
def monthly_sales_report(request):
    """Display completed sales and revenue for a selected month."""
    year = request.GET.get("year")
    month = request.GET.get("month")

    sales = None
    total_revenue = 0
    error = None

    if year or month:
        try:
            year = int(year)
            month = int(month)

            if year < 2000 or year > timezone.localdate().year:
                raise ValueError

            if month < 1 or month > 12:
                raise ValueError

            sales, total_revenue = ReportService.monthly_sales_report(
                year,
                month,
            )

        except (ValueError, TypeError):
            error = "Please select a valid month and year."

    return render(
        request,
        "reports/monthly_sales_report.html",
        {
            "sales": sales,
            "year": year,
            "month": month,
            "total_revenue": total_revenue,
            "error": error,
        },
    )