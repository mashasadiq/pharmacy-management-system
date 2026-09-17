from django.db import models

# Create your models here.

from django.conf import settings


class AuditLog(models.Model):
    """
    Stores a historical record of important actions
    performed within the system.
    """

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("VIEW", "View"),
        ("PRINT", "Print"),
        ("EXPORT", "Export"),
    ]

    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    table_name = models.CharField(max_length=100)

    record_id = models.PositiveBigIntegerField()

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user = self.user.username if self.user else "System"
        return f"{self.action} - {self.table_name} ({user})"