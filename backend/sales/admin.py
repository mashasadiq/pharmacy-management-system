from django.contrib import admin

from django.db import transaction
from django.core.exceptions import ValidationError


from .models import Sale, SaleItem
from inventory.models import Drug


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "pharmacist",
        "sale_date",
        "total_amount",
        "payment_method",
        "status",
    )

    list_filter = (
        "payment_method",
        "status",
        "sale_date",
    )

    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "pharmacist__username",
    )

    date_hierarchy = "sale_date"

    inlines = [SaleItemInline]

    def save_related(self, request, form, formsets, change):
        """
        Automatically calculate the Sale total from its SaleItems
        after the inline items have been saved.
        """
        super().save_related(request, form, formsets, change)

        sale = form.instance

        total = sum(
            item.subtotal
            for item in sale.items.all()
        )

        sale.total_amount = total
        sale.save(update_fields=["total_amount"])

    def save_formset(self, request, form, formset, change):
        if formset.model != SaleItem:
            super().save_formset(request, form, formset, change)
            return

        if form.instance.status == Sale.Status.COMPLETED:
            stock_changes = {}

            for item_form in formset.forms:
                if not item_form.has_changed():
                    continue

                # Existing SaleItem
                if item_form.instance.pk:
                    old_item = SaleItem.objects.get(pk=item_form.instance.pk)
                    old_drug = old_item.drug
                    old_quantity = old_item.quantity

                    # Item is being deleted
                    if item_form.cleaned_data.get("DELETE"):
                        stock_changes[old_drug.id] = (
                            stock_changes.get(old_drug.id, 0)
                            - old_quantity
                        )
                        continue

                    new_drug = item_form.cleaned_data["drug"]
                    new_quantity = item_form.cleaned_data["quantity"]

                    # Drug was changed
                    if old_drug.id != new_drug.id:
                        stock_changes[old_drug.id] = (
                            stock_changes.get(old_drug.id, 0)
                            - old_quantity
                        )

                        stock_changes[new_drug.id] = (
                            stock_changes.get(new_drug.id, 0)
                            + new_quantity
                        )

                    # Same drug, quantity was changed
                    else:
                        difference = new_quantity - old_quantity

                        stock_changes[old_drug.id] = (
                            stock_changes.get(old_drug.id, 0)
                            + difference
                        )

                # New SaleItem
                else:
                    new_drug = item_form.cleaned_data["drug"]
                    new_quantity = item_form.cleaned_data["quantity"]

                    stock_changes[new_drug.id] = (
                        stock_changes.get(new_drug.id, 0)
                        + new_quantity
                    )

            # Check stock BEFORE changing anything
            for drug_id, change_amount in stock_changes.items():
                if change_amount > 0:
                    drug = Drug.objects.get(id=drug_id)
                    
                    if change_amount > drug.quantity_in_stock:
                        raise ValidationError(
                            f"Insufficient stock for {drug.name}."
                        )

            # Apply stock changes and save SaleItems
            with transaction.atomic():
                for drug_id, change_amount in stock_changes.items():
                    drug = Drug.objects.get(id=drug_id)
                    
                    drug.quantity_in_stock -= change_amount
                    drug.save()

                formset.save()

        else:
            formset.save()


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "drug",
        "quantity",
        "unit_price",
        "subtotal",
    )

    search_fields = (
        "drug__name",
    )