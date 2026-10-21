from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite

from .admin import AuditLogAdmin
from .models import AuditLog

User = get_user_model()


class AuditLogAdminSecurityTests(TestCase):
    """Verify audit records cannot be manually changed through admin."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="audit_admin",
            password="test-password",
            email="audit@example.com",
        )

        self.audit_admin = AuditLogAdmin(AuditLog, AdminSite())

    def test_audit_log_cannot_be_manually_added(self):
        self.assertFalse(
            self.audit_admin.has_add_permission(
                request=self._admin_request()
            )
        )

    def test_audit_log_cannot_be_modified(self):
        self.assertFalse(
            self.audit_admin.has_change_permission(
                request=self._admin_request()
            )
        )

    def test_audit_log_cannot_be_deleted(self):
        self.assertFalse(
            self.audit_admin.has_delete_permission(
                request=self._admin_request()
            )
        )

    def _admin_request(self):
        from django.test import RequestFactory

        request = RequestFactory().get("/admin/")
        request.user = self.admin_user
        return request