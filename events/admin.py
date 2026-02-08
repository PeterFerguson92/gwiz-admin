from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Event, EventTicket


def _format_user_label(user, guest_name: str = "", guest_email: str = "") -> str:
    if user:
        return user.get_full_name() or user.email or "—"
    if guest_name:
        return f"Guest: {guest_name}"
    if guest_email:
        return f"Guest: {guest_email}"
    return "Guest"


class EventTicketInline(admin.TabularInline):
    model = EventTicket
    extra = 0
    fields = (
        "user_display",
        "user",
        "guest_name",
        "guest_email",
        "quantity",
        "status",
        "payment_status",
        "payment_provider",
        "stripe_payment_intent_id",
        "truelayer_payment_id",
        "truelayer_payment_status",
        "created_at",
    )
    readonly_fields = ("user_display", "created_at")
    autocomplete_fields = ("user",)

    def user_display(self, obj):
        return _format_user_label(obj.user, obj.guest_name, obj.guest_email)

    user_display.short_description = "User"


@admin.register(Event)
class EventAdmin(ModelAdmin):
    inlines = [EventTicketInline]
    list_display = (
        "name",
        "start_datetime",
        "location",
        "ticket_price",
        "capacity",
        "remaining_tickets",
        "is_featured",
        "is_active",
    )
    list_filter = ("is_active", "is_featured", "start_datetime")
    search_fields = ("name", "location", "description")
    ordering = ("-is_featured", "featured_order", "start_datetime")
    date_hierarchy = "start_datetime"
    readonly_fields = ("created_at", "updated_at", "remaining_tickets", "is_sold_out")
    fieldsets = (
        (
            "Details",
            {"fields": ("name", "description", "cover_image", "location")},
        ),
        (
            "Schedule",
            {"fields": ("start_datetime", "end_datetime")},
        ),
        (
            "Pricing & capacity",
            {
                "fields": (
                    "ticket_price",
                    "payment_link",
                    "capacity",
                    "remaining_tickets",
                    "is_sold_out",
                )
            },
        ),
        (
            "Visibility",
            {"fields": ("is_active", "is_featured", "featured_order")},
        ),
        (
            "Meta",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(EventTicket)
class EventTicketAdmin(ModelAdmin):
    list_display = (
        "id",
        "user_display",
        "event",
        "quantity",
        "status",
        "payment_status",
        "payment_provider",
        "created_at",
    )
    list_filter = ("status", "payment_status", "payment_provider", "event")
    search_fields = (
        "id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "guest_name",
        "guest_email",
        "event__name",
    )
    autocomplete_fields = ("user", "event")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def user_display(self, obj):
        return _format_user_label(obj.user, obj.guest_name, obj.guest_email)

    user_display.short_description = "User"
