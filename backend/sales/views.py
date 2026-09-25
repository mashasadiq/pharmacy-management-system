import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from inventory.models import Drug
from patients.models import Patient
from .models import Sale, SaleItem


@login_required
@ensure_csrf_cookie
def create_sale_page(request):
    patients = Patient.objects.all()

    drugs = Drug.objects.filter(
        quantity_in_stock__gt=0
    )

    return render(
        request,
        "sales/create_sale.html",
        {
            "patients": patients,
            "drugs": drugs,
            "payment_methods": Sale.PaymentMethod.choices,
        },
    )


@login_required
@transaction.atomic
def create_sale(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    try:
        data = json.loads(request.body)

        patient = get_object_or_404(
            Patient,
            id=data["patient"]
        )

        payment_method = data["payment_method"]
        items = data["items"]

        if not items:
            return JsonResponse(
                {"error": "A sale must contain at least one item."},
                status=400,
            )

        sale = Sale.objects.create(
            patient=patient,
            pharmacist=request.user,
            payment_method=payment_method,
            status=Sale.Status.COMPLETED,
        )

        total_amount = Decimal("0.00")

        for item in items:

            drug = get_object_or_404(
                Drug,
                id=item["drug_id"]
            )

            quantity = int(item["quantity"])

            if quantity <= 0:
                raise ValueError(
                    f"Invalid quantity for {drug.name}."
                )

            if quantity > drug.quantity_in_stock:
                raise ValueError(
                    f"Insufficient stock for {drug.name}."
                )

            SaleItem.objects.create(
                sale=sale,
                drug=drug,
                quantity=quantity,
                unit_price=drug.selling_price,
            )

            drug.quantity_in_stock -= quantity
            drug.save()

            total_amount += quantity * drug.selling_price

        sale.total_amount = total_amount
        sale.save()

        return JsonResponse(
            {
                "message": "Sale completed successfully.",
                "sale_id": sale.id,
                "total_amount": str(total_amount),
            }
        )

    except ValueError as e:
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
def sales_list(request):
    sales = Sale.objects.select_related(
        "patient",
        "pharmacist",
    ).order_by("-sale_date")

    return render(
        request,
        "sales/sales_list.html",
        {"sales": sales},
    )

@login_required
def sale_detail(request, sale_id):
    """
    Display the details of a single sale and its items.
    """
    sale = get_object_or_404(
        Sale.objects.select_related(
            "patient",
            "pharmacist",
        ),
        id=sale_id,
    )

    items = sale.items.select_related("drug")

    return render(
        request,
        "sales/sale_detail.html",
        {
            "sale": sale,
            "items": items,
        },
    )