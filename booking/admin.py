from datetime import date, timedelta

from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse

from booking.services import generate_sessions_for_rule, preview_sessions_for_rule

from .models import ClassSession, FitnessClass, RecurrenceRule

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


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    form = ClassSessionForm

    change_list_template = "admin/booking/classsession/change_list.html"

    list_display = (
        "fitness_class",
        "formatted_date",
        "formatted_time",
        "status",
    )
    list_filter = ("fitness_class", "status", "date")
    autocomplete_fields = ("fitness_class", "created_from_rule")
    ordering = ("fitness_class__name", "date", "start_time")

    def formatted_date(self, obj):
        return obj.date.strftime("%A, %d %b %Y")

    formatted_date.short_description = "Date"

    def formatted_time(self, obj):
        start = obj.start_time.strftime("%I:%M %p")
        end = obj.end_time.strftime("%I:%M %p")
        return f"{start} → {end}"

    formatted_time.short_description = "Time"

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
