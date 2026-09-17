from django.shortcuts import get_object_or_404, render
from django.db.models import F, Q
from django.utils import timezone

from .models import Drug



def inventory_list(request):
    """
    Display all drugs in the inventory.
    Allow users to search by name, generic name,
    brand, or barcode.
    """

    query = request.GET.get("q", "")

    drugs = Drug.objects.all()

    if query:
        drugs = drugs.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(brand__icontains=query)
            | Q(barcode__icontains=query)
        )

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "drugs": drugs,
            "query": query,
        },
    )

def drug_detail(request, drug_id):
    """
    Display details of one drug.
    """

    drug = get_object_or_404(Drug, id=drug_id)

    return render(
        request,
        "inventory/drug_detail.html",
        {"drug": drug},
    )


def low_stock_drugs(request):
    """
    Display drugs whose stock is at or below
    their minimum stock level.
    """

    drugs = Drug.objects.filter(
        quantity_in_stock__lte=F("minimum_stock")
    )

    return render(
        request,
        "inventory/low_stock.html",
        {"drugs": drugs},
    )


def expired_drugs(request):
    """
    Display drugs that have already expired.
    """

    drugs = Drug.objects.filter(
        expiry_date__lt=timezone.now().date()
    )

    return render(
        request,
        "inventory/expired_drugs.html",
        {"drugs": drugs},
    )

def check_stock_availability(request, drug_id):
    """
    Check whether a drug has enough stock
    for the requested quantity.
    """

    drug = get_object_or_404(Drug, id=drug_id)

    requested_quantity = int(request.GET.get("quantity", 0))

    available = requested_quantity <= drug.quantity_in_stock

    return render(
        request,
        "inventory/stock_availability.html",
        {
            "drug": drug,
            "requested_quantity": requested_quantity,
            "current_stock": drug.quantity_in_stock,
            "available": available,
        },
    )