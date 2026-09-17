from django.db import models

# Create your models here.

from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Low Stock"
        EXPIRY = "EXPIRY", "Drug Expiry"
        PURCHASE = "PURCHASE", "Purchase"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"
        SALE = "SALE", "Sale"
        GENERAL = "GENERAL", "General"

    title = models.CharField(max_length=150)
    message = models.TextField()

    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )

    is_read = models.BooleanField(default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} ({self.user})"