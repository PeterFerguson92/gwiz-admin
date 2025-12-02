from datetime import date, timedelta

from django import forms
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse

from booking.services import generate_sessions_for_rule, preview_sessions_for_rule

from .models import Booking, ClassSession, FitnessClass, RecurrenceRule

# ---------- FitnessClass ---------- #


@admin.register(FitnessClass)
class FitnessClassAdmin(admin.ModelAdmin):
    list_display = ("name", "genre", "capacity", "base_price", "is_active")
    list_filter = ("genre", "is_active")
    search_fields = ("name", "description")
    filter_horizontal = ("instructors",)


# ---------- RecurrenceRule ---------- #


class RecurrenceRuleForm(forms.ModelForm):
    DAYS = [
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
        ("sun", "Sunday"),
    ]

    # nice checkbox UI
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Days of week",
    )

    class Meta:
        model = RecurrenceRule
        fields = "__all__"
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(self.instance.days_of_week, list):
            self.fields["days_of_week"].initial = self.instance.days_of_week

    def clean_days_of_week(self):
        return self.cleaned_data["days_of_week"] or []

    def clean(self):
        cleaned = super().clean()
        rtype = cleaned.get("recurrence_type")
        days = cleaned.get("days_of_week") or []

        # For weekly / multiple days per week, require at least one day
        if rtype in ("weekly", "multi_weekly") and not days:
            self.add_error(
                "days_of_week",
                "Please select at least one day for a weekly recurrence.",
            )

        # For one-off / daily, clear days_of_week
        if rtype in ("one_off", "daily"):
            cleaned["days_of_week"] = []

        return cleaned


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    form = RecurrenceRuleForm
    change_form_template = "admin/booking/recurrencerule/change_form.html"

    list_display = (
        "fitness_class",
        "recurrence_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "is_active",
    )
    list_filter = ("recurrence_type", "is_active")
    search_fields = ("fitness_class__name",)
    autocomplete_fields = ("fitness_class",)

    # --- custom URL for "Generate sessions" button --- #

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/generate-sessions/",
                self.admin_site.admin_view(self.generate_sessions_view),
                name="booking_recurrencerule_generate_sessions",
            ),
        ]
        return custom_urls + urls

    def generate_sessions_view(self, request, object_id, *args, **kwargs):
        """
        Custom admin view that shows a confirmation screen,
        then generates sessions for this rule.
        """
        rule = get_object_or_404(RecurrenceRule, pk=object_id)
        from_date = date.today()
        to_date = from_date + timedelta(days=90)

        preview_create, preview_skip = preview_sessions_for_rule(
            rule, from_date, to_date
        )

        if request.method == "POST":
            created, skipped = generate_sessions_for_rule(rule, from_date, to_date)

            self.message_user(
                request,
                f"Generated {created} sessions (skipped {skipped} existing).",
                level=messages.SUCCESS,
            )
            url = reverse("admin:booking_recurrencerule_change", args=[object_id])
            return HttpResponseRedirect(url)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "rule": rule,
            "from_date": from_date,
            "to_date": to_date,
            "preview_create": preview_create,
            "preview_skip": preview_skip,
            "title": "Generate sessions",
        }
        return TemplateResponse(
            request,
            "admin/booking/recurrencerule/generate_sessions_confirm.html",
            context,
        )


# ---------- ClassSession ---------- #


class ClassSessionForm(forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = "__all__"
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    autocomplete_fields = ("user",)

    # Replace "user" with our custom field
    fields = (
        "user_full_name",
        "status",
        "payment_status",
        "attendance_status",
        "created_at",
    )

    readonly_fields = ("user_full_name", "created_at")

    def user_full_name(self, obj):
        if obj.user:
            full = obj.user.get_full_name()
            return full if full else obj.user.email
        return "—"

    user_full_name.short_description = "User"


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    form = ClassSessionForm

    change_list_template = "admin/booking/classsession/change_list.html"

    list_display = (
        "fitness_class",
        "formatted_date",
        "formatted_time",
        "status",
        "effective_capacity",
        "booked_count",
        "remaining_spots",
    )
    list_filter = ("fitness_class", "status", "date")
    autocomplete_fields = ("fitness_class", "created_from_rule")
    ordering = ("fitness_class__name", "date", "start_time")
    inlines = [BookingInline]

    search_fields = ("fitness_class__name", "date", "start_time")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate number of active (booked) bookings for each session
        qs = qs.annotate(
            _booked_count=Count(
                "bookings",
                filter=Q(bookings__status=Booking.STATUS_BOOKED),
            )
        )
        return qs

    def formatted_date(self, obj):
        return obj.date.strftime("%A, %d %b %Y")

    formatted_date.short_description = "Date"

    def formatted_time(self, obj):
        start = obj.start_time.strftime("%I:%M %p")
        end = obj.end_time.strftime("%I:%M %p")
        return f"{start} → {end}"

    formatted_time.short_description = "Time"

    def effective_capacity(self, obj):
        # Use the same logic as your model property
        return obj.capacity_override or obj.fitness_class.capacity

    effective_capacity.short_description = "Capacity"

    def booked_count(self, obj):
        # Use the annotated value when present; fall back to a query
        if hasattr(obj, "_booked_count"):
            return obj._booked_count
        return obj.bookings.filter(status=Booking.STATUS_BOOKED).count()

    booked_count.short_description = "Booked"

    def remaining_spots(self, obj):
        return self.effective_capacity(obj) - self.booked_count(obj)

    remaining_spots.short_description = "Remaining"

    # --- custom URLs for grouped view --- #

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "grouped/",
                self.admin_site.admin_view(self.grouped_view),
                name="booking_classsession_grouped",
            ),
        ]
        return custom_urls + urls

    def grouped_view(self, request):
        """
        Custom read-only view that shows sessions grouped by FitnessClass,
        with simple search + status filter.
        """
        qs = self.get_queryset(request).select_related("fitness_class")

        # Simple search: filter by fitness class name
        query = request.GET.get("q") or ""
        if query:
            qs = qs.filter(Q(fitness_class__name__icontains=query))

        # Status filter
        status_filter = request.GET.get("status") or ""
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Final ordering: class name ASC, date/time DESC
        qs = qs.order_by("fitness_class__name", "date", "start_time")

        # Build grouped data: [(class_name, [sessions]), ...]
        groups = []
        current_class = None
        current_list = []

        for session in qs:
            class_name = session.fitness_class.name if session.fitness_class else "—"
            if class_name != current_class:
                if current_list:
                    groups.append((current_class, current_list))
                current_class = class_name
                current_list = []
            current_list.append(session)

        if current_list:
            groups.append((current_class, current_list))

        # For status dropdown
        status_choices = self.model._meta.get_field("status").choices

        context = {
            **self.admin_site.each_context(request),
            "title": "Class sessions grouped by Fitness class",
            "groups": groups,
            "opts": self.model._meta,
            "query": query,
            "status_filter": status_filter,
            "status_choices": status_choices,
        }
        return TemplateResponse(
            request,
            "admin/booking/classsession/grouped.html",
            context,
        )


# ---------- Booking ---------- #


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_full_name",
        "fitness_class_name",
        "class_date",
        "class_time",
        "status",
        "payment_status",
        "attendance_status",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_status",
        "attendance_status",
        "class_session__fitness_class",
        "class_session__date",
    )
    search_fields = (
        "id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "class_session__fitness_class__name",
    )
    autocomplete_fields = ("user", "class_session")
    date_hierarchy = "class_session__date"
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Booking",
            {
                "fields": (
                    "user",
                    "class_session",
                    "status",
                    "payment_status",
                    "stripe_payment_intent_id",
                    "attendance_status",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def user_full_name(self, obj):
        # Prefer full name; fall back to email
        full = obj.user.get_full_name()
        return full if full else obj.user.email

    user_full_name.short_description = "User"

    def fitness_class_name(self, obj):
        return obj.class_session.fitness_class.name

    fitness_class_name.short_description = "Class"

    def class_date(self, obj):
        return obj.class_session.date

    def class_time(self, obj):
        return obj.class_session.start_time
