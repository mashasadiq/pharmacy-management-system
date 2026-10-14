#core stock business logic centralized for reusability, is responsible for understanding the actual stock operation.
from django.db import transaction
from django.core.exceptions import ValidationError
from sales.models import Sale

from inventory.models import Drug


def complete_sale(sale, items):
    """
    Validate and deduct stock for a completed sale.

    Combines duplicate drug items and locks stock rows
    to prevent concurrent sales from overselling inventory.
    """
    stock_changes = {}

    # Combine quantities for duplicate drugs.
    for drug, quantity in items:
        stock_changes[drug.id] = (
            stock_changes.get(drug.id, 0) + quantity
        )

    # Validate and update stock within one transaction.
    with transaction.atomic():

        # Lock all affected drug rows in a consistent order.
        drugs = {
            drug.id: drug
            for drug in Drug.objects.select_for_update()
            .filter(id__in=stock_changes)
            .order_by("id")
        }

        # Check that every drug has sufficient stock.
        for drug_id, change_amount in stock_changes.items():
            drug = drugs.get(drug_id)

            if drug is None:
                raise ValidationError("A selected drug no longer exists.")

            if change_amount > drug.quantity_in_stock:
                raise ValidationError(
                    f"Insufficient stock for {drug.name}."
                )

        # Deduct stock only after all checks pass.
        for drug_id, change_amount in stock_changes.items():
            drug = drugs[drug_id]
            drug.quantity_in_stock -= change_amount
            drug.save(update_fields=["quantity_in_stock"])


def cancel_sale(sale):
    """
    Restore inventory stock for a completed sale being cancelled.
    """
    if sale.status != Sale.Status.COMPLETED:
        raise ValidationError(
            "Only completed sales can have stock restored."
        )

    with transaction.atomic():

        # Combine quantities for duplicate drugs.
        stock_changes = {}

        for item in sale.items.all():
            stock_changes[item.drug_id] = (
                stock_changes.get(item.drug_id, 0)
                + item.quantity
            )

        # Lock affected drug rows in a consistent order.
        drugs = {
            drug.id: drug
            for drug in Drug.objects.select_for_update()
            .filter(id__in=stock_changes)
            .order_by("id")
        }

        # Restore the quantities previously deducted.
        for drug_id, quantity in stock_changes.items():
            drug = drugs.get(drug_id)

            if drug is None:
                raise ValidationError(
                    "A drug associated with this sale no longer exists."
                )

            drug.quantity_in_stock += quantity
            drug.save(update_fields=["quantity_in_stock"])

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