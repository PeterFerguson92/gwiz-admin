from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Event, EventTicket


class EventTicketInline(admin.TabularInline):
    model = EventTicket
    extra = 0
    fields = (
        "user",
        "quantity",
        "status",
        "payment_status",
        "stripe_payment_intent_id",
        "created_at",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


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
        "user",
        "event",
        "quantity",
        "status",
        "payment_status",
        "created_at",
    )
    list_filter = ("status", "payment_status", "event")
    search_fields = (
        "id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__name",
    )
    autocomplete_fields = ("user", "event")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
