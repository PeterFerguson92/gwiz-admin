# booking/admin.py

from django.contrib import admin

from .models import ClassSession, FitnessClass, RecurrenceRule


@admin.register(FitnessClass)
class FitnessClassAdmin(admin.ModelAdmin):
    list_display = ("name", "genre", "capacity", "base_price", "is_active")
    list_filter = ("genre", "is_active")
    search_fields = ("name", "description")
    filter_horizontal = ("instructors",)


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
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


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "fitness_class",
        "date",
        "start_time",
        "end_time",
        "status",
    )
    list_filter = ("status", "date")
    autocomplete_fields = ("fitness_class", "created_from_rule")
    ordering = ("-date",)
