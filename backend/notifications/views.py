from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """Display the logged-in user's notifications."""
    notifications = Notification.objects.filter(
        user=request.user
    )

    return render(
        request,
        "notifications/notification_list.html",
        {"notifications": notifications},
    )
