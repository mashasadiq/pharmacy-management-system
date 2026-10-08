import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from django.db.models import Q

from inventory.models import Drug
from patients.models import Patient
from .models import Sale, SaleItem
from audit_logs.models import AuditLog
from .services import complete_sale, cancel_sale

from django.utils import timezone




@login_required
@ensure_csrf_cookie
def create_sale_page(request):
    patients = Patient.objects.all()

    return render(
        request,
        "sales/create_sale.html",
        {
            "patients": patients,
            "payment_methods": Sale.PaymentMethod.choices,
        },
    )


@login_required
@transaction.atomic
def create_sale(request):
    """
    Create a new pending sale without changing inventory stock.
    """
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
            status=Sale.Status.PENDING,
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

            total_amount += quantity * drug.selling_price

        sale.total_amount = total_amount
        sale.save()

        AuditLog.objects.create(
            user=request.user,
            action="CREATE",
            table_name="sales_sale",
            record_id=sale.id,
            description=f"Sale #{sale.id} was created as Pending.",
        )

        return JsonResponse(
            {
                "message": "Sale created successfully.",
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
def search_products(request):
    """
    Search in-stock drugs by name, generic name, brand, or barcode.
    The database performs the filtering.
    """
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse(
            {"products": []}
        )

    # Find an exact barcode match first.
    exact_barcode = Drug.objects.filter(
        quantity_in_stock__gt=0,
        barcode=query,
    ).first()

    if exact_barcode:
        drugs = [exact_barcode]

    else:
        # Search by name, generic name, brand, or partial barcode, thats the use of Q
        drugs = Drug.objects.filter(
            quantity_in_stock__gt=0
        ).filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(brand__icontains=query)
            | Q(barcode__icontains=query)
        )[:20]

    products = [
        {
            "id": drug.id,
            "name": drug.name,
            "price": str(drug.selling_price),
            "stock": drug.quantity_in_stock,
            "barcode": drug.barcode,
        }
        for drug in drugs
    ]

    return JsonResponse(
        {"products": products}
    )


@login_required
def sales_list(request):
    """
    Display sales and optionally filter them by invoice number or date.
    """
    invoice = request.GET.get("invoice", "").strip()
    date_filter = request.GET.get("date", "").strip()

    sales = Sale.objects.select_related(
        "patient",
        "pharmacist",
    ).order_by("-sale_date")

    if invoice:
        sales = sales.filter(
            invoice_number__icontains=invoice
        )

    if date_filter == "today":
        today = timezone.localdate()

        sales = sales.filter(
            sale_date__date=today,
            status=Sale.Status.COMPLETED,
        )

    return render(
        request,
        "sales/sales_list.html",
        {
            "sales": sales,
            "invoice": invoice,
        },
    )


@login_required
def sale_detail(request, sale_id):
    """
    Display sale details and allow pending sales to be edited.
    """
    sale = get_object_or_404(
        Sale.objects.select_related(
            "patient",
            "pharmacist",
        ),
        id=sale_id,
    )

    items = sale.items.select_related("drug")

    drugs = Drug.objects.filter(
        quantity_in_stock__gt=0
    )

    return render(
        request,
        "sales/sale_detail.html",
        {
            "sale": sale,
            "items": items,
            "drugs": drugs,
        },
    )


@login_required
@transaction.atomic
def complete_sale_view(request, sale_id):
    """
    Complete a pending sale and deduct its items from inventory.
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    sale = get_object_or_404(
        Sale.objects.prefetch_related("items__drug"),
        id=sale_id,
    )

    if sale.status != Sale.Status.PENDING:
        return JsonResponse(
            {"error": "Only pending sales can be completed."},
            status=400,
        )

    items = [
        (item.drug, item.quantity)
        for item in sale.items.all()
    ]

    if not items:
        return JsonResponse(
            {"error": "A sale must contain at least one item."},
            status=400,
        )

    try:
        complete_sale(sale, items)

        sale.invoice_number = f"INV-{sale.sale_date:%Y%m%d}-{sale.id:06d}"
        sale.status = Sale.Status.COMPLETED

        sale.save(
            update_fields=[
                "invoice_number",
                "status",
            ]
        )#after complete_sale(sale, items) succeeds, generate the invoice number and complete the sale.



        AuditLog.objects.create(
            user=request.user,
            action="UPDATE",
            table_name="sales_sale",
            record_id=sale.id,
            description=(
                f"Sale #{sale.id} was completed; "
                "inventory stock was deducted."
            ),
        )

        return JsonResponse(
            {
                "message": "Sale completed successfully.",
                "sale_id": sale.id,
                "invoice_number": sale.invoice_number,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

@login_required
@transaction.atomic
def edit_pending_sale(request, sale_id):
    """
    Update the items of a pending sale without changing inventory.
    """
    sale = get_object_or_404(
        Sale.objects.prefetch_related("items__drug"),
        id=sale_id,
    )

    if sale.status != Sale.Status.PENDING:
        return JsonResponse(
            {"error": "Only pending sales can be edited."},
            status=400,
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    try:
        data = json.loads(request.body)
        items = data["items"]

        if not items:
            return JsonResponse(
                {"error": "A sale must contain at least one item."},
                status=400,
            )

        sale.items.all().delete()

        total_amount = Decimal("0.00")

        for item in items:
            drug = get_object_or_404(
                Drug,
                id=item["drug_id"],
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

            total_amount += quantity * drug.selling_price

        sale.total_amount = total_amount
        sale.save(update_fields=["total_amount"])

        AuditLog.objects.create(
            user=request.user,
            action="UPDATE",
            table_name="sales_sale",
            record_id=sale.id,
            description=(
                f"Pending sale #{sale.id} was edited; "
                f"new total is Ksh {total_amount}."
            ),
        )

        return JsonResponse(
            {
                "message": "Pending sale updated successfully.",
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
@transaction.atomic
def delete_pending_sale(request, sale_id):
    """
    Delete a pending sale and record the deletion in the audit log.
    """

    if request.user.role != "ADMIN":
        return JsonResponse(
            {"error": "Only administrators can delete sales."},
            status=403,
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    sale = get_object_or_404(
        Sale,
        id=sale_id,
    )

    if sale.status != Sale.Status.PENDING:
        return JsonResponse(
            {"error": "Only pending sales can be deleted."},
            status=400,
        )

    AuditLog.objects.create(
        user=request.user,
        action="DELETE",
        table_name="sales_sale",
        record_id=sale.id,
        description=(
            f"Pending sale #{sale.id} was deleted."
        ),
    )

    sale.delete()

    return JsonResponse(
        {
            "message": "Pending sale deleted successfully.",
            "sale_id": sale_id,
        }
    )
    

@login_required
@transaction.atomic
def cancel_sale_view(request, sale_id):
    """
    Allow only administrators to cancel completed sales.
    """
    if request.user.role != "ADMIN":
        return JsonResponse(
            {"error": "Only administrators can cancel sales."},
            status=403,
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    sale = get_object_or_404(
        Sale.objects.prefetch_related("items__drug"),
        id=sale_id,
    )

    if sale.status != Sale.Status.COMPLETED:
        return JsonResponse(
            {"error": "Only completed sales can be cancelled."},
            status=400,
        )

    try:
        cancel_sale(sale)

        sale.status = Sale.Status.CANCELLED
        sale.save(update_fields=["status"])

        AuditLog.objects.create(
            user=request.user,
            action="UPDATE",
            table_name="sales_sale",
            record_id=sale.id,
            description=(
                f"Sale #{sale.id} was cancelled; "
                "inventory stock was restored."
            ),
        )

        return JsonResponse(
            {
                "message": "Sale cancelled successfully.",
                "sale_id": sale.id,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )