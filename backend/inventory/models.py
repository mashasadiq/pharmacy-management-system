from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from suppliers.models import Supplier
from audit_logs.models import AuditLog


class Drug(models.Model):
    """Represents a drug in the pharmacy inventory."""

    CATEGORY_CHOICES = [
        ("Tablet", "Tablet"),
        ("Capsule", "Capsule"),
        ("Syrup", "Syrup"),
        ("Injection", "Injection"),
        ("Cream", "Cream"),
        ("Drops", "Drops"),
        ("Ointment", "Ointment"),
        ("Other", "Other"),
    ]

    UNIT_CHOICES = [
        ("Box", "Box"),
        ("Bottle", "Bottle"),
        ("Strip", "Strip"),
        ("Tube", "Tube"),
        ("Vial", "Vial"),
        ("Piece", "Piece"),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="drugs"
    )

    name = models.CharField(max_length=150)
    generic_name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100)

    barcode = models.CharField(max_length=100, unique=True)
    batch_number = models.CharField(max_length=100)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES
    )

    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity_in_stock = models.PositiveIntegerField(default=0)

    minimum_stock = models.PositiveIntegerField(default=10)

    expiry_date = models.DateField()

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Drug"
        verbose_name_plural = "Drugs"

    def __str__(self):
        return f"{self.name} ({self.brand})"


class StockAdjustment(models.Model):
    """Records a manual adjustment made to a drug's stock."""

    drug = models.ForeignKey(
        Drug,
        on_delete=models.PROTECT,
        related_name="stock_adjustments"
    )

    quantity_change = models.IntegerField()

    reason = models.TextField()

    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_adjustments"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Stock Adjustment"
        verbose_name_plural = "Stock Adjustments"

    def save(self, *args, **kwargs):
        """Apply the stock adjustment and create an audit record."""

        if not self.pk:
            new_stock = self.drug.quantity_in_stock + self.quantity_change

            if new_stock < 0:
                raise ValidationError(
                    f"Stock adjustment would make {self.drug.name} negative. "
                    f"Current stock: {self.drug.quantity_in_stock}."
                )

            self.drug.quantity_in_stock = new_stock
            self.drug.save()

            super().save(*args, **kwargs)

            AuditLog.objects.create(
                user=self.adjusted_by,
                action="UPDATE",
                table_name="inventory_drug",
                record_id=self.drug.id,
                description=(
                    f"Stock adjusted by {self.quantity_change}. "
                    f"Reason: {self.reason}."
                ),
            )

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.drug.name} ({self.quantity_change})"