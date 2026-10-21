from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LogoutSecurityTests(TestCase):
#Test logout security and session termination.

    def setUp(self):
        """Create an authenticated user and a CSRF-enforcing client."""

        self.user = User.objects.create_user(
            username="logout_test_user",
            password="TestPassword123!",
            role="PHARMACIST",
        )

        self.client = Client(enforce_csrf_checks=True)

        self.client.force_login(self.user)

        self.logout_url = reverse("logout")

    def test_logout_rejects_get_request(self):
        """GET requests must not log users out."""

        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.user.is_authenticated)

    def test_logout_rejects_post_without_csrf_token(self):
        """POST requests without a valid CSRF token must be rejected."""

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 403)

        self.assertIn("_auth_user_id", self.client.session)


    def test_logout_succeeds_with_valid_csrf_token(self):
        """Valid POST requests must terminate the authenticated session."""

        self.client.get(reverse("login"))

        csrf_token = self.client.cookies["csrftoken"].value

        response = self.client.post(
            self.logout_url,
            {"csrfmiddlewaretoken": csrf_token},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotIn("_auth_user_id", self.client.session)
    
