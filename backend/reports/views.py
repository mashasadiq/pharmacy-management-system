from django.shortcuts import render, redirect

# Create your views here.
from django.contrib import messages

from .models import Purchase
from .forms import PurchaseForm


def create_purchase(request):
    if request.method == "POST":
        form = PurchaseForm(request.POST)

        if form.is_valid():
            purchase = form.save()

            # Update inventory
            drug = purchase.drug
            drug.quantity_in_stock += purchase.quantity
            drug.save()

            messages.success(request, "Purchase recorded successfully.")
            return redirect("purchase_list")

    else:
        form = PurchaseForm()

    return render(request, "purchases/create_purchase.html", {"form": form})