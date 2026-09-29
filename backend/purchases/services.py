from django.db import transaction
from django.core.exceptions import ValidationError

from inventory.models import Drug
from .models import Purchase
from audit_logs.models import AuditLog


@transaction.atomic
def create_purchase(
    *,
    drug,
    supplier,
    received_by,
    quantity,
    cost_price,
    purchase_date,
    invoice_number,
    remarks="",
):
    """
    Record a received purchase, increase drug stock,
    and create an audit record as one transaction.
    """

    if quantity <= 0:
        raise ValidationError(
            "Purchase quantity must be greater than zero."
        )

    if cost_price < 0:
        raise ValidationError(
            "Cost price cannot be negative."
        )

    purchase = Purchase.objects.create(
        drug=drug,
        supplier=supplier,
        received_by=received_by,
        quantity=quantity,
        cost_price=cost_price,
        purchase_date=purchase_date,
        invoice_number=invoice_number,
        remarks=remarks,
    )

    drug.quantity_in_stock += quantity
    drug.save(update_fields=["quantity_in_stock"])

    AuditLog.objects.create(
        user=received_by,
        action="CREATE",
        table_name="purchases_purchase",
        record_id=purchase.id,
        description=(
            f"Purchase #{purchase.id} recorded: "
            f"{quantity} units of {drug.name} received; "
            f"inventory stock increased."
        ),
    )

    return purchase