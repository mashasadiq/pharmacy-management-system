from django.contrib import admin

from django.db import transaction
from django.core.exceptions import ValidationError


from .models import Sale, SaleItem
from inventory.models import Drug

from audit_logs.models import AuditLog


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


    def has_delete_permission(self, request, obj=None):
        if request.user.role == "PHARMACIST":
            return False

        return super().has_delete_permission(request, obj)


    def save_model(self, request, obj, form, change):
        """
        Store the Sale's previous status before saving changes.
        This is used to detect status transitions, such as
        Pending → Completed and Completed → Cancelled.
        """
        old_status = None

        if change:
            old_sale = Sale.objects.get(pk=obj.pk)
            old_status = old_sale.status
            obj._old_status = old_status

            # A cancelled sale cannot be completed again
            if (
                old_sale.status == Sale.Status.CANCELLED
                and obj.status == Sale.Status.COMPLETED
            ):
                raise ValidationError(
                    "A cancelled sale cannot be completed again."
                )

        super().save_model(request, obj, form, change)

        # Record Sale status changes in the audit log
        if change and old_status != obj.status:
            AuditLog.objects.create(
                user=request.user,
                action="UPDATE",
                table_name="sales_sale",
                record_id=obj.id,
                description=(
                    f"Sale #{obj.id} changed from "
                    f"{old_status} to {obj.status}."
                ),
            )


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
        """
        Handle SaleItem stock changes when a Sale is completed,
        edited, or cancelled.
        """
        if formset.model != SaleItem:
            super().save_formset(request, form, formset, change)
            return

        # Restore stock when a completed sale is cancelled
        if (
            getattr(form.instance, "_old_status", None) == Sale.Status.COMPLETED
            and form.instance.status == Sale.Status.CANCELLED
        ):
            with transaction.atomic():
                for item in form.instance.items.all():
                    item.drug.quantity_in_stock += item.quantity
                    item.drug.save()

            formset.save()
            return

        # Deduct stock when a pending sale becomes completed
        if (
            getattr(form.instance, "_old_status", None) == Sale.Status.PENDING
            and form.instance.status == Sale.Status.COMPLETED
        ):
            stock_changes = {}

            for item_form in formset.forms:
                if not item_form.cleaned_data:
                    continue

                if item_form.cleaned_data.get("DELETE"):
                    continue

                drug = item_form.cleaned_data["drug"]
                quantity = item_form.cleaned_data["quantity"]

                stock_changes[drug.id] = (
                    stock_changes.get(drug.id, 0)
                    + quantity
                )

            # Check stock BEFORE changing anything
            for drug_id, change_amount in stock_changes.items():
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