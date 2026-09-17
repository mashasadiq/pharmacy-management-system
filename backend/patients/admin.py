from django.contrib import admin

# Register your models here.


from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_number",
        "first_name",
        "last_name",
        "gender",
        "phone",
        "created_by",
        "created_at",
    )

    search_fields = (
        "patient_number",
        "first_name",
        "last_name",
        "phone",
        "email",
    )

    list_filter = (
        "gender",
        "created_at",
    )

    ordering = (
        "last_name",
        "first_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )