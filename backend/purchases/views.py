import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.db import transaction

from inventory.models import Drug
from suppliers.models import Supplier

from .models import Purchase

from .services import create_purchase as create_purchase_service

@login_required
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


@login_required
@transaction.atomic
def create_purchase(request):
    """
    Record a new purchase, increase inventory stock,
    and create the related audit record.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    try:
        data = json.loads(request.body)

        drug = get_object_or_404(
            Drug,
            id=data["drug_id"],
        )

        supplier = get_object_or_404(
            Supplier,
            id=data["supplier_id"],
        )

        quantity = int(data["quantity"])
        cost_price = Decimal(data["cost_price"])

        purchase = create_purchase_service(
            drug=drug,
            supplier=supplier,
            received_by=request.user,
            quantity=quantity,
            cost_price=cost_price,
            purchase_date=data["purchase_date"],
            invoice_number=data["invoice_number"],
            remarks=data.get("remarks", ""),
        )

        return JsonResponse(
            {
                "message": "Purchase recorded successfully.",
                "purchase_id": purchase.id,
                "drug": drug.name,
                "quantity": quantity,
                "new_stock": drug.quantity_in_stock,
            },
            status=201,
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

@login_required
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

@login_required
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