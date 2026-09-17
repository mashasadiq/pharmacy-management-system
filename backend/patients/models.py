from django.db import models

# Create your models here.
from django.conf import settings


class Patient(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    patient_number = models.CharField(
        max_length=20,
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField()

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients_created"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.patient_number} - {self.first_name} {self.last_name}"