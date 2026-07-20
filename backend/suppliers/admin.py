from django.contrib import admin

# Register your models here.


from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "contact_person",
        "phone",
        "email",
        "city",
        "country",
        "is_active",
    )

    list_filter = (
        "country",
        "city",
        "is_active",
    )

    search_fields = (
        "company_name",
        "contact_person",
        "email",
        "phone",
    )

    ordering = (
        "company_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Supplier Information",
            {
                "fields": (
                    "company_name",
                    "contact_person",
                    "phone",
                    "email",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "address",
                    "city",
                    "country",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
