from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):
    """Form for registering a patient without exposing system-managed fields."""

    class Meta:
        model = Patient
        fields = (
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "phone",
            "email",
            "address",
        )