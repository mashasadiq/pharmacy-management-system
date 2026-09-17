from django.contrib import admin

# Register your models here.

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "table_name",
        "record_id",
        "ip_address",
        "timestamp",
    )

    list_filter = (
        "action",
        "table_name",
        "timestamp",
    )

    search_fields = (
        "description",
        "table_name",
        "user__username",
    )

    ordering = ("-timestamp",)

    readonly_fields = (
        "timestamp",
    )