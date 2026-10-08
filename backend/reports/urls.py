from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_home, name="reports_home"),

    path(
        "inventory/",
        views.inventory_report,
        name="inventory_report",
    ),

    path(
        "low-stock/",
        views.low_stock_report,
        name="low_stock_report",
    ),

    path(
        "expired/",
        views.expired_drugs_report,
        name="expired_drugs_report",
    ),

    path(
        "patients/",
        views.patient_report,
        name="patient_report",
    ),

    path(
        "purchases/",
        views.purchase_report,
        name="purchase_report",
    ),

    path(
        "sales/daily/",
        views.daily_sales_report,
        name="daily_sales_report",
    ),

    path(
        "sales/monthly/",
        views.monthly_sales_report,
        name="monthly_sales_report",
    ),
]
