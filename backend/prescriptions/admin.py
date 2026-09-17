from django.contrib import admin

# Register your models here.


from .models import Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "prescription_number",
        "patient",
        "doctor_name",
        "pharmacist",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "prescription_number",
        "doctor_name",
        "patient__first_name",
        "patient__last_name",
    )

    ordering = ("-created_at",)

    inlines = [PrescriptionItemInline]


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = (
        "prescription",
        "drug",
        "quantity",
        "dosage",
        "duration",
    )

    search_fields = (
        "prescription__prescription_number",
        "drug__name",
    )