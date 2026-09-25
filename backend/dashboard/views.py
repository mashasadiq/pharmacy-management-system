from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone

from audit_logs.models import AuditLog
from inventory.models import Drug
from patients.models import Patient
from sales.models import Sale


@login_required
def dashboard(request):
    if request.user.role == "ADMIN":
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)

        completed_sales_today = Sale.objects.filter(
            sale_date__date=today,
            status=Sale.Status.COMPLETED,
        )

        context = {
            "total_drugs": Drug.objects.count(),
            "low_stock_drugs": Drug.objects.filter(
                quantity_in_stock__lte=F("minimum_stock")
            ).count(),
            "expired_drugs": Drug.objects.filter(
                expiry_date__lt=today
            ).count(),
            "expiring_soon": Drug.objects.filter(
                expiry_date__gte=today,
                expiry_date__lte=thirty_days_from_now,
            ).count(),
            "total_patients": Patient.objects.count(),
            "total_sales": Sale.objects.count(),
            "today_sales": completed_sales_today.count(),
            "today_revenue": completed_sales_today.aggregate(
                total=Sum("total_amount")
            )["total"] or 0,
            "recent_sales": Sale.objects.select_related(
                "patient", "pharmacist"
            ).order_by("-sale_date")[:5],
            "recent_activity": AuditLog.objects.select_related(
                "user"
            ).order_by("-timestamp")[:5],
        }

        return render(
            request,
            "dashboard/admin_dashboard.html",
            context,
        )

    if request.user.role == "PHARMACIST":
        today = timezone.localdate()

        completed_sales_today = Sale.objects.filter(
            sale_date__date=today,
            status=Sale.Status.COMPLETED,
        )

        context = {
            "today_sales": completed_sales_today.count(),
            "today_revenue": completed_sales_today.aggregate(
                total=Sum("total_amount")
            )["total"] or 0,
            "low_stock_drugs": Drug.objects.filter(
                quantity_in_stock__lte=F("minimum_stock")
            ).count(),
            "expired_drugs": Drug.objects.filter(
                expiry_date__lt=today
            ).count(),
            "recent_sales": Sale.objects.select_related(
                "patient", "pharmacist"
            ).order_by("-sale_date")[:5],
        }

        return render(
            request,
            "dashboard/pharmacist_dashboard.html",
            context,
        )

    return render(request, "dashboard/dashboard.html")