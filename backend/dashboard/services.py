from django.db.models import Sum, F
from django.utils import timezone
from datetime import date

from sales.models import Sale
from inventory.models import Drug
from patients.models import Patient


class DashboardService:

    @staticmethod
    def get_statistics():
        today = date.today()

        return {
            "today_sales": Sale.objects.filter(
                sale_date__date=today
            ).count(),

            "today_revenue": Sale.objects.filter(
                sale_date__date=today
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0,

            "patients": Patient.objects.count(),

            "drugs": Drug.objects.count(),

            "low_stock": Drug.objects.filter(
                quantity_in_stock__lte=F("reorder_level")
            ).count(),

            "expired_drugs": Drug.objects.filter(
                expiry_date__lt=today
            ).count(),
        }