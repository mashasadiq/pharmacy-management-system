
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardSecurityTests(TestCase):
    """Test role-based access to the dashboard."""

    def setUp(self):
        """Create administrator and pharmacist accounts."""

        self.admin = User.objects.create_user(
            username="dashboard_admin",
            password="TestPassword123!",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="dashboard_pharmacist",
            password="TestPassword123!",
            role="PHARMACIST",
        )

        self.dashboard_url = reverse("dashboard")

    def test_anonymous_user_cannot_access_dashboard(self):
        """Unauthenticated users must be redirected to login."""

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 302)

    def test_pharmacist_receives_pharmacist_dashboard(self):
        """Pharmacists must receive their role-specific dashboard."""

        self.client.force_login(self.pharmacist)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "dashboard/pharmacist_dashboard.html",
        )

    def test_admin_receives_admin_dashboard(self):
        """Administrators must receive their role-specific dashboard."""

        self.client.force_login(self.admin)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "dashboard/admin_dashboard.html",
        )

    def test_unsupported_role_is_denied_dashboard_access(self):
        """Users with unsupported roles must receive HTTP 403."""

        user = User.objects.create_user(
            username="dashboard_unknown",
            password="TestPassword123!",
            role="PHARMACIST",
        )

        user.role = "UNKNOWN"
        user.save(update_fields=["role"])

        self.client.force_login(user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)
