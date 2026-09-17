from django.contrib import admin

# Register your models here.

from .models import Drug, StockAdjustment


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "generic_name",
        "brand",
        "supplier",
        "quantity_in_stock",
        "selling_price",
        "expiry_date",
    )

    list_filter = (
        "category",
        "supplier",
        "expiry_date",
    )

    search_fields = (
        "name",
        "generic_name",
        "brand",
        "barcode",
        "batch_number",
    )

    ordering = ("name",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drug",
        "quantity_change",
        "adjusted_by",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "drug__name",
        "reason",
        "adjusted_by__username",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)