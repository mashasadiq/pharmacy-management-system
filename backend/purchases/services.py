
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError

from datetime import date
from decimal import Decimal, InvalidOperation

from .models import Purchase
from inventory.models import Drug
from audit_logs.models import AuditLog
from notifications.services import check_low_stock


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
    idempotency_key,
    remarks="",
):
    """
    Create a purchase exactly once for a given idempotency key.
    """

    if not idempotency_key:
        raise ValidationError("An idempotency key is required.")

    if quantity <= 0:
        raise ValidationError(
            "Purchase quantity must be greater than zero."
        )



    # Convert and validate the cost price independently of the API view.
    try:
        cost_price = Decimal(str(cost_price))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("Enter a valid cost price.")

    # Reject NaN and infinity.
    if not cost_price.is_finite():
        raise ValidationError("Cost price must be a valid finite number.")

    # A purchase must have a positive unit cost.
    if cost_price <= 0:
        raise ValidationError("Cost price must be greater than zero.")

    # The database field allows a maximum of two decimal places.
    if cost_price.as_tuple().exponent < -2:
        raise ValidationError(
            "Cost price cannot have more than two decimal places."
        )

    # DecimalField(max_digits=10, decimal_places=2).
    if cost_price > Decimal("99999999.99"):
        raise ValidationError(
            "Cost price cannot exceed 99,999,999.99."
        )



    # Ensure the purchase date is a Python date object.
    if isinstance(purchase_date, str):
        try:
            purchase_date = date.fromisoformat(purchase_date)
        except ValueError:
            raise ValidationError("Enter a valid purchase date.")

    if not isinstance(purchase_date, date):
        raise ValidationError("Enter a valid purchase date.")

    # Return the original purchase if this request was already processed.
    existing_purchase = Purchase.objects.filter(
        idempotency_key=idempotency_key
    ).first()

    if existing_purchase:
        return existing_purchase, False

    try:
        # Use a savepoint so a uniqueness conflict does not break
        # the surrounding purchase transaction.
        with transaction.atomic():
            purchase = Purchase.objects.create(
                drug=drug,
                supplier=supplier,
                received_by=received_by,
                quantity=quantity,
                cost_price=cost_price,
                purchase_date=purchase_date,
                invoice_number=invoice_number,
                idempotency_key=idempotency_key,
                remarks=remarks,
            )

    except IntegrityError:
        # Another simultaneous request may have created this purchase.
        existing_purchase = Purchase.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        if existing_purchase:
            return existing_purchase, False

        # The database error was caused by something else.
        raise

    # Generate the internal reference using the saved purchase ID.
    purchase.purchase_reference = (
        f"PUR-{purchase.purchase_date.strftime('%Y%m%d')}-{purchase.id:06d}"
    )

    purchase.save(update_fields=["purchase_reference"])

    # Lock the drug row to prevent concurrent stock updates from overwriting each other.
    drug = Drug.objects.select_for_update().get(pk=drug.pk)

    # Increase inventory only for a newly created purchase.
    drug.quantity_in_stock += quantity
    drug.save(update_fields=["quantity_in_stock"])

    # Refresh or resolve the drug's low-stock alert after replenishment.
    check_low_stock(drug)

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

    return purchase, True