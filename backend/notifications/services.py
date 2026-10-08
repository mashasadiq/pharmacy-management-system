from notifications.models import Notification
from accounts.models import User


def check_low_stock(drug):
    """
    Check whether a drug has reached its minimum stock level.

    If the drug is at or below its minimum stock level,
    create an unread notification for each active admin
    and pharmacist, unless one already exists.
    """
    if drug.quantity_in_stock > drug.minimum_stock:
        return

    users = User.objects.filter(
        is_active=True,
        role__in=["ADMIN", "PHARMACIST"],
    )

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
