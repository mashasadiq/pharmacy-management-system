from django.db import models

# Create your models here.

from django.conf import settings

from inventory.models import Drug
from suppliers.models import Supplier


class Purchase(models.Model):
    drug = models.ForeignKey(
        Drug,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_purchases"
    )

    quantity = models.PositiveIntegerField()

    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    purchase_date = models.DateField()

    invoice_number = models.CharField(
        max_length=100
    )

    remarks = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-purchase_date"]
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"

    def __str__(self):
        return f"{self.drug.name} - {self.quantity} units"