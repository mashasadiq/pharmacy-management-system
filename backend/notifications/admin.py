from django.contrib import admin

# Register your models here.

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "type",
        "user",
        "is_read",
        "created_at",
    )

    list_filter = (
        "type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "user__username",
        "user__email",
    )

    autocomplete_fields = ("user",)

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)