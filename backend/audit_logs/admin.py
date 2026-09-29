from django.contrib import admin

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

    def has_add_permission(self, request):
        """
        Prevent users from manually creating audit log records.
        Audit logs should only be created by the system.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Prevent users from modifying existing audit log records.
        Audit history must remain unchanged.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Prevent users from deleting audit log records.
        Historical audit records must be preserved.
        """
        return False