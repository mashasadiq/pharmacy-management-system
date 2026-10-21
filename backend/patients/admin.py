from django.contrib import admin
from django.http import request

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
        "patient_number",
        "created_at",
        "updated_at",
    )
    #retrieves the patient records and their associated users in one joined query(optimizing database access 
    # and reducing the number of queries executed).
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")