from django.db import models

# Create your models here.



from django.db import models


class Supplier(models.Model):
    company_name = models.CharField(
        max_length=150,
        unique=True,
    )

    contact_person = models.CharField(
        max_length=100,
    )

    phone = models.CharField(
        max_length=20,
    )

    email = models.EmailField(
        unique=True,
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100,
    )

    country = models.CharField(
        max_length=100,
        default="Kenya",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.company_name