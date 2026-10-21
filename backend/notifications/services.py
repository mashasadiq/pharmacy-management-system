from django.db import transaction

from notifications.models import Notification
from accounts.models import User


@transaction.atomic
def check_low_stock(drug):
    """
    Maintain active low-stock alerts for a drug.

    Create or update alerts when stock is at or below
    the minimum level. Delete them when stock recovers.
    """

    low_stock_alerts = Notification.objects.filter(
        drug=drug,
        type=Notification.NotificationType.LOW_STOCK,
    )

    # Remove all low-stock alerts when stock recovers.
    if drug.quantity_in_stock > drug.minimum_stock:
        low_stock_alerts.delete()
        return

    users = User.objects.filter(
        is_active=True,
        role__in=["ADMIN", "PHARMACIST"],
    )

    message = (
        f"{drug.name} is at or below its minimum stock level. "
        f"Current stock: {drug.quantity_in_stock}. "
        f"Minimum stock: {drug.minimum_stock}."
    )

    for user in users:
        notification, created = Notification.objects.get_or_create(
            user=user,
            drug=drug,
            type=Notification.NotificationType.LOW_STOCK,
            defaults={
                "title": "Low Stock Alert",
                "message": message,
            },
        )

        # Keep an existing alert's message up to date.
        if not created:
            notification.message = message
            notification.title = "Low Stock Alert"
            notification.save(update_fields=["message", "title"])