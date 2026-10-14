import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.db import transaction

from inventory.models import Drug
from suppliers.models import Supplier

from .models import Purchase

from .services import create_purchase as create_purchase_service

from accounts.decorators import admin_required

@admin_required
def create_purchase_page(request):
    """
    Display the page used to record a new purchase.
    """
    drugs = Drug.objects.all()
    suppliers = Supplier.objects.all()

    return render(
        request,
        "purchases/create_purchase.html",
        {
            "drugs": drugs,
            "suppliers": suppliers,
        },
    )


@admin_required
@transaction.atomic
def create_purchase(request):
    """
    Record a purchase while preventing duplicate submissions.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    try:
        data = json.loads(request.body)

        # Every purchase request must have an idempotency key.
        idempotency_key = data["idempotency_key"]

        drug = get_object_or_404(
            Drug,
            id=data["drug_id"],
        )

        supplier = get_object_or_404(
            Supplier,
            id=data["supplier_id"],
        )

        raw_quantity = data["quantity"]

        if isinstance(raw_quantity, bool):
            raise ValidationError("Quantity must be a whole number.")

        try:
            quantity = int(raw_quantity)
        except (ValueError, TypeError):
            raise ValidationError("Quantity must be a valid whole number.")

        if str(quantity) != str(raw_quantity).strip():
            raise ValidationError("Quantity must be a whole number.")

        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")


        # Convert the submitted cost price into a Decimal safely.
        try:
            cost_price = Decimal(str(data["cost_price"]))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Enter a valid cost price.")



        # The service tells us whether this is a new purchase or a retry.
        purchase, created = create_purchase_service(
            drug=drug,
            supplier=supplier,
            received_by=request.user,
            quantity=quantity,
            cost_price=cost_price,
            purchase_date=data["purchase_date"],
            invoice_number=(data.get("invoice_number") or "").strip(),
            remarks=data.get("remarks", ""),
            idempotency_key=idempotency_key,
        )

        return JsonResponse(
            {
                "message": (
                    "Purchase recorded successfully."
                    if created
                    else "This purchase was already recorded."
                ),
                "purchase_id": purchase.id,
                "purchase_reference": purchase.purchase_reference,
                "supplier_invoice_number": purchase.invoice_number,
                "drug": purchase.drug.name,
                "quantity": purchase.quantity,
                "new_stock": purchase.drug.quantity_in_stock,
                "created": created,
            },
            status=201 if created else 200,
        )

    except (KeyError, ValueError, TypeError, ValidationError) as e:
        transaction.set_rollback(True)

        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    except Exception as e:
        transaction.set_rollback(True)

        return JsonResponse(
            {"error": str(e)},
            status=500,
        )


@admin_required
def purchase_list(request):
    """Display all recorded purchases as historical records."""
    purchases = Purchase.objects.select_related(
        "drug",
        "supplier",
        "received_by",
    )

    return render(
        request,
        "purchases/purchase_list.html",
        {"purchases": purchases},
    )

@admin_required
def purchase_detail(request, purchase_id):
    """Display the complete details of one recorded purchase."""
    purchase = get_object_or_404(
        Purchase.objects.select_related(
            "drug",
            "supplier",
            "received_by",
        ),
        id=purchase_id,
    )

    return render(
        request,
        "purchases/purchase_detail.html",
        {"purchase": purchase},
    )