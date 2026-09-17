from django.db import models

# Create your models here.

from decimal import Decimal

from django.conf import settings

from inventory.models import Drug
from patients.models import Patient


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "Cash", "Cash"
        MPESA = "MPesa", "MPesa"
        CARD = "Card", "Card"

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="sales",
    )

    pharmacist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales_processed",
    )

    sale_date = models.DateTimeField(auto_now_add=True)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        ordering = ["-sale_date"]
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        return f"Sale #{self.id}"
        

class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )

    drug = models.ForeignKey(
        Drug,
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )

    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.drug.name} x {self.quantity}"