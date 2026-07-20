from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.




class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Administrator"),
        ("PHARMACIST", "Pharmacist"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="PHARMACIST",
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username