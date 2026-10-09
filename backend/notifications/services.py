from django.db import transaction

from notifications.models import Notification
from accounts.models import User


@transaction.atomic
def check_low_stock(drug):
    """
    Create low-stock alerts or resolve unread alerts when stock recovers.
    """
    users = User.objects.filter(
        is_active=True,
        role__in=["ADMIN", "PHARMACIST"],
    )

    if drug.quantity_in_stock > drug.minimum_stock:
        Notification.objects.filter(
            drug=drug,
            type=Notification.NotificationType.LOW_STOCK,
            is_read=False,
        ).update(is_read=True)
        return

    for user in users:
        notification_exists = Notification.objects.filter(
            user=user,
            drug=drug,
            type=Notification.NotificationType.LOW_STOCK,
            is_read=False,
        ).exists()

        if notification_exists:
            continue

        Notification.objects.create(
            title="Low Stock Alert",
            message=(
                f"{drug.name} is at or below its minimum stock level. "
                f"Current stock: {drug.quantity_in_stock}. "
                f"Minimum stock: {drug.minimum_stock}."
            ),
            type=Notification.NotificationType.LOW_STOCK,
            user=user,
            drug=drug,
        )
