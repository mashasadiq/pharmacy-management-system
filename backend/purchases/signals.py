from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Purchase


@receiver(post_save, sender=Purchase)
def update_inventory_on_purchase(sender, instance, created, **kwargs):
    if created:
        drug = instance.drug
        drug.quantity_in_stock += instance.quantity
        drug.save()