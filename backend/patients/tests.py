from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from patients.models import Patient
from audit_logs.models import AuditLog


User = get_user_model()


class PatientAccessTests(TestCase):
    """Test access to patient records according to user roles."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_test",
            password="testpassword123",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="pharmacist_test",
            password="testpassword123",
            role="PHARMACIST",
        )

        self.patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            gender="Male",
            date_of_birth="1995-05-10",
            phone="0712345678",
            created_by=self.admin,
        )

    def test_anonymous_user_cannot_view_patient(self):
        """Unauthenticated users must be redirected to login."""
        response = self.client.get(
            reverse("patient_detail", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_pharmacist_can_view_patient_history(self):
        """Pharmacists can access patient details and medication history."""
        self.client.login(
            username="pharmacist_test",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("patient_detail", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sales History")

    def test_admin_can_view_patient_history(self):
        """Administrators can access patient details and medication history."""
        self.client.login(
            username="admin_test",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("patient_detail", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sales History")


    
    def test_admin_patient_view_creates_audit_log(self):
        """Administrator access to patient history must be audited."""
        self.client.login(
            username="admin_test",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("patient_detail", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 200)

        audit_log = AuditLog.objects.get(
            user=self.admin,
            action="VIEW",
            table_name="Patient",
            record_id=self.patient.id,
        )

        self.assertIn(
            self.patient.patient_number,
            audit_log.description,
        )

        self.assertEqual(
            audit_log.ip_address,
            "127.0.0.1",
        )


    
    def test_pharmacist_patient_view_does_not_create_admin_audit_log(self):
        """Pharmacist access must not create the admin-specific audit event."""
        self.client.login(
            username="pharmacist_test",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("patient_detail", args=[self.patient.id])
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            AuditLog.objects.filter(
                user=self.pharmacist,
                action="VIEW",
                table_name="Patient",
                record_id=self.patient.id,
            ).exists()
        )
