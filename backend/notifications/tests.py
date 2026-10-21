
from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal
from datetime import date

from .models import Notification
from inventory.models import Drug
from suppliers.models import Supplier
from notifications.services import check_low_stock

User = get_user_model()


class NotificationSecurityTests(TestCase):
    """Test notification access and ownership restrictions."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="notification_admin",
            password="test-password",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="notification_pharmacist",
            password="test-password",
            role="PHARMACIST",
        )

        self.admin_notification = Notification.objects.create(
            title="Admin Alert",
            message="Admin notification test.",
            type=Notification.NotificationType.GENERAL,
            user=self.admin,
        )

        self.pharmacist_notification = Notification.objects.create(
            title="Pharmacist Alert",
            message="Pharmacist notification test.",
            type=Notification.NotificationType.LOW_STOCK,
            user=self.pharmacist,
        )

    def test_anonymous_user_cannot_access_notifications(self):
        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 302)

    def test_user_can_only_view_their_own_notifications(self):
        self.client.force_login(self.pharmacist)

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pharmacist Alert")
        self.assertNotContains(response, "Admin Alert")

    def test_notifications_are_displayed_without_read_status_or_actions(self):
        self.client.force_login(self.pharmacist)

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pharmacist Alert")
        self.assertNotContains(response, "Status: Read")
        self.assertNotContains(response, "Status: Unread")
        self.assertNotContains(response, "Mark as read")

    def test_read_notifications_remain_visible(self):
        self.pharmacist_notification.is_read = True
        self.pharmacist_notification.save(update_fields=["is_read"])

        self.client.force_login(self.pharmacist)

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pharmacist Alert")


class LowStockNotificationTests(TestCase):
    """Test low-stock notification creation and resolution."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="stock_admin",
            password="test-password",
            role="ADMIN",
        )

        self.pharmacist = User.objects.create_user(
            username="stock_pharmacist",
            password="test-password",
            role="PHARMACIST",
        )

        self.inactive_user = User.objects.create_user(
            username="inactive_pharmacist",
            password="test-password",
            role="PHARMACIST",
            is_active=False,
        )

        self.supplier = Supplier.objects.create(
            company_name="Test Supplier",
            contact_person="Test Contact",
            phone="0712345678",
            email="supplier@example.com",
            address="Test Address",
            city="Nairobi",
        )

        self.drug = Drug.objects.create(
            supplier=self.supplier,
            name="Paracetamol",
            generic_name="Paracetamol",
            brand="Test Brand",
            batch_number="BATCH001",
            category="Tablet",
            unit="Box",
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
            quantity_in_stock=5,
            minimum_stock=10,
            expiry_date=date(2027, 12, 31),
        )

    def test_low_stock_creates_notifications_for_eligible_users(self):
        check_low_stock(self.drug)

        notifications = Notification.objects.filter(
            drug=self.drug,
            type=Notification.NotificationType.LOW_STOCK,
        )

        self.assertEqual(notifications.count(), 2)

        notified_user_ids = set(
            notifications.values_list("user_id", flat=True)
        )

        self.assertEqual(
            notified_user_ids,
            {self.admin.id, self.pharmacist.id},
        )

    def test_repeated_check_does_not_create_duplicate_notifications(self):
        check_low_stock(self.drug)
        check_low_stock(self.drug)

        notifications = Notification.objects.filter(
            drug=self.drug,
            type=Notification.NotificationType.LOW_STOCK,
        )

        self.assertEqual(notifications.count(), 2)

    def test_inactive_users_do_not_receive_low_stock_notifications(self):
        check_low_stock(self.drug)

        self.assertFalse(
            Notification.objects.filter(
                user=self.inactive_user,
                drug=self.drug,
                type=Notification.NotificationType.LOW_STOCK,
            ).exists()
        )

    def test_existing_notification_message_is_updated(self):
        check_low_stock(self.drug)

        self.drug.quantity_in_stock = 3
        self.drug.save(update_fields=["quantity_in_stock"])

        check_low_stock(self.drug)

        notification = Notification.objects.get(
            user=self.admin,
            drug=self.drug,
            type=Notification.NotificationType.LOW_STOCK,
        )

        self.assertIn("Current stock: 3", notification.message)

    def test_stock_recovery_deletes_low_stock_notifications(self):
        check_low_stock(self.drug)

        self.assertEqual(
            Notification.objects.filter(
                drug=self.drug,
                type=Notification.NotificationType.LOW_STOCK,
            ).count(),
            2,
        )

        # Replenish stock above the minimum level.
        self.drug.quantity_in_stock = 20
        self.drug.save(update_fields=["quantity_in_stock"])

        check_low_stock(self.drug)

        self.assertFalse(
            Notification.objects.filter(
                drug=self.drug,
                type=Notification.NotificationType.LOW_STOCK,
            ).exists()
        )

    def test_stock_recovery_does_not_delete_unrelated_notifications(self):
        general_notification = Notification.objects.create(
            title="General Alert",
            message="General notification.",
            type=Notification.NotificationType.GENERAL,
            user=self.admin,
            drug=self.drug,
        )

        self.drug.quantity_in_stock = 20
        self.drug.save(update_fields=["quantity_in_stock"])

        check_low_stock(self.drug)

        self.assertTrue(
            Notification.objects.filter(
                id=general_notification.id
            ).exists()
        )
