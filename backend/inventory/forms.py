from django import forms

from .models import Drug


class DrugForm(forms.ModelForm):
    """Form for registering a new drug in the pharmacy inventory."""

    class Meta:
        model = Drug
        fields = [
            "supplier",
            "name",
            "generic_name",
            "brand",
            "batch_number",
            "category",
            "unit",
            "cost_price",
            "selling_price",
            "quantity_in_stock",
            "minimum_stock",
            "expiry_date",
            "description",
        ]
        widgets = {
            "expiry_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }