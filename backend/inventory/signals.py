# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from purchases.models import Purchase
# from inventory.models import Drug


# @receiver(post_save, sender=Purchase)
# def update_inventory_after_purchase(sender, instance, created, **kwargs):
#     """
#     Increase inventory when a new purchase is created.
#     """

#     if created:
#         drug = instance.drug
#         drug.quantity_in_stock += instance.quantity
#         drug.save()