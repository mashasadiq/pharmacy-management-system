from django.contrib import admin

# Register your models here.



from .models import Purchase


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "drug",
        "supplier",
        "quantity",
        "cost_price",
        "purchase_date",
        "received_by",
    )

    list_filter = (
        "supplier",
        "purchase_date",
    )

    search_fields = (
        "drug__name",
        "supplier__company_name",
        "invoice_number",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-purchase_date",
    )