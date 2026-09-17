from django.db import models

# Create your models here.

from django.conf import settings


from inventory.models import Drug
from patients.models import Patient


class PrescriptionStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    DISPENSED = "Dispensed", "Dispensed"
    CANCELLED = "Cancelled", "Cancelled"
    EXPIRED = "Expired", "Expired"


class Prescription(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )

    pharmacist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prescriptions",
    )

    prescription_number = models.CharField(
        max_length=30,
        unique=True,
    )

    doctor_name = models.CharField(
        max_length=150,
    )

    notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PrescriptionStatus.choices,
        default=PrescriptionStatus.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"

    def __str__(self):
        return self.prescription_number


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items",
    )

    drug = models.ForeignKey(
        Drug,
        on_delete=models.PROTECT,
        related_name="prescription_items",
    )

    quantity = models.PositiveIntegerField()

    dosage = models.CharField(
        max_length=100,
    )

    duration = models.CharField(
        max_length=100,
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Prescription Item"
        verbose_name_plural = "Prescription Items"

    def __str__(self):
        return f"{self.drug.name} ({self.quantity})"