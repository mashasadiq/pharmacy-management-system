from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import F, Q
from django.utils import timezone

from accounts.decorators import admin_required
from django.http import JsonResponse

from .models import Drug
from .forms import DrugForm


@login_required
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

@login_required
def search_drugs(request):
    """
    Search all inventory drugs by name, generic name,
    brand, or barcode.
    """

    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"drugs": []})

    drugs = Drug.objects.filter(
        Q(name__icontains=query)
        | Q(generic_name__icontains=query)
        | Q(brand__icontains=query)
        | Q(barcode__icontains=query)
    ).order_by("name")

    results = [
        {
            "id": drug.id,
            "name": drug.name,
            "generic_name": drug.generic_name,
            "brand": drug.brand,
            "barcode": drug.barcode,
            "selling_price": str(drug.selling_price),
            "stock": drug.quantity_in_stock,
            "minimum_stock": drug.minimum_stock,
        }
        for drug in drugs
    ]

    return JsonResponse({"drugs": results})


@login_required
def drug_detail(request, drug_id):
    """
    Display details of one drug.
    """

    drug = get_object_or_404(Drug, id=drug_id)

    return render(
        request,
        "inventory/drug_detail.html",
        {
            "drug": drug,
            "today": timezone.localdate(),
        },
    )



@login_required
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

@login_required
def expired_drugs(request):
    """
    Display drugs that have already expired.
    """

    drugs = Drug.objects.filter(
        expiry_date__lt=timezone.localdate()
    )

    return render(
        request,
        "inventory/expired_drugs.html",
        {"drugs": drugs},
    )


@login_required
def check_stock_availability(request, drug_id):
    """Check stock availability for a valid positive quantity."""
    drug = get_object_or_404(Drug, id=drug_id)
    quantity_input = request.GET.get("quantity", "").strip()

    # Reject missing, non-numeric, zero, and negative quantities.
    try:
        requested_quantity = int(quantity_input)
        if requested_quantity <= 0:
            raise ValueError
    except ValueError:
        return render(
            request,
            "inventory/stock_availability.html",
            {
                "drug": drug,
                "requested_quantity": quantity_input,
                "current_stock": drug.quantity_in_stock,
                "available": False,
                "error": "Enter a valid quantity greater than zero.",
            },
        )

    available = requested_quantity <= drug.quantity_in_stock

    return render(
        request,
        "inventory/stock_availability.html",
        {
            "drug": drug,
            "requested_quantity": requested_quantity,
            "current_stock": drug.quantity_in_stock,
            "available": available,
            "error": "",
        },
    )

@admin_required
def create_drug(request):
    """Display and process the form for registering a new drug."""

    if request.method == "POST":
        form = DrugForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("inventory_list")
    else:
        form = DrugForm()

    return render(
        request,
        "inventory/create_drug.html",
        {"form": form},
    )