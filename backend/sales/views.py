import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from inventory.models import Drug
from patients.models import Patient
from .models import Sale, SaleItem


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