#services.py  core stock business logic centralized, is responsible for understanding the actual stock operation.
from django.db import transaction
from django.core.exceptions import ValidationError

from inventory.models import Drug


def complete_sale(sale, items):
    """
    Deduct stock for a sale being completed.

    Checks that enough stock exists before making
    any stock changes.
    """
    stock_changes = {}

    for drug, quantity in items:
        stock_changes[drug.id] = (
            stock_changes.get(drug.id, 0)
            + quantity
        )

    # Check stock BEFORE changing anything
    for drug_id, change_amount in stock_changes.items():
        drug = Drug.objects.get(id=drug_id)

        if change_amount > drug.quantity_in_stock:
            raise ValidationError(
                f"Insufficient stock for {drug.name}."
            )

    # Apply stock changes
    with transaction.atomic():
        for drug_id, change_amount in stock_changes.items():
            drug = Drug.objects.get(id=drug_id)

            drug.quantity_in_stock -= change_amount
            drug.save()


def cancel_sale(sale):
    """
    Restore stock for a completed sale that is being cancelled.
    """
    with transaction.atomic():
        for item in sale.items.select_related("drug"):
            item.drug.quantity_in_stock += item.quantity
            item.drug.save()

def update_completed_sale(changes):
    """
    Apply inventory changes caused by editing a completed sale.

    Positive values deduct stock, while negative values
    return stock to inventory.
    """
    # Check stock BEFORE changing anything
    for drug_id, change_amount in changes.items():
        if change_amount > 0:
            drug = Drug.objects.get(id=drug_id)

            if change_amount > drug.quantity_in_stock:
                raise ValidationError(
                    f"Insufficient stock for {drug.name}."
                )

    # Apply the inventory changes
    with transaction.atomic():
        for drug_id, change_amount in changes.items():
            drug = Drug.objects.get(id=drug_id)

            drug.quantity_in_stock -= change_amount
            drug.save()