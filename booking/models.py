import uuid

from django.db import models
from django_resized import ResizedImageField
from storages.backends.s3boto3 import S3Boto3Storage

from booking.upload import fitness_class_cover_upload_image_path
from homepage.models import Trainer

s3_storage = S3Boto3Storage()


class FitnessClass(models.Model):
    """
    High-level class definition, e.g. 'Beginner Yoga', 'Open Gym'
    """

    GENRE_CHOICES = [
        ("yoga", "Yoga"),
        ("strength", "Strength"),
        ("cardio", "Cardio"),
        ("open_gym", "Open Gym"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cover_image = ResizedImageField(
        "Cover Image",
        upload_to=fitness_class_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,  # S3 like the homepage app
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    default_duration_minutes = models.PositiveIntegerField(default=60)
    capacity = models.PositiveIntegerField()
    instructors = models.ManyToManyField(
        Trainer,
        blank=True,
        related_name="fitness_classes",
        help_text="Trainers who can run this class",
    )
    additional_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class RecurrenceRule(models.Model):
    """
    Defines when a FitnessClass recurs.

    We'll later have a task/command that reads these rules and
    generates concrete ClassSession rows for specific dates.
    """

    WEEKDAY_CHOICES = [
        ("mon", "Monday"),
        ("tue", "Tuesday"),
        ("wed", "Wednesday"),
        ("thu", "Thursday"),
        ("fri", "Friday"),
        ("sat", "Saturday"),
        ("sun", "Sunday"),
    ]

    RECURRENCE_TYPE_CHOICES = [
        ("one_off", "One-off"),
        ("weekly", "Weekly"),
        ("multi_weekly", "Multiple days per week"),
        ("daily", "Daily"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fitness_class = models.ForeignKey(
        FitnessClass,
        on_delete=models.CASCADE,
        related_name="recurrence_rules",
    )
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_TYPE_CHOICES,
        default="weekly",
    )

    # For weekly / multi-weekly patterns
    # Example: ["mon", "wed"]
    days_of_week = models.JSONField(
        default=list,
        help_text="List of weekday codes, e.g. ['mon', 'wed']",
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Optional future flexibility (RRULE-like)
    rrule = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("fitness_class__name", "start_date")

    def __str__(self) -> str:
        return f"{self.fitness_class.name} – {self.recurrence_type}"


class ClassSession(models.Model):
    """
    A concrete, bookable class occurrence for a specific date and time.
    These are generated from RecurrenceRule or created manually.
    """

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fitness_class = models.ForeignKey(
        FitnessClass,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    capacity_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If set, overrides FitnessClass.capacity for this session.",
    )
    price_override = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="If set, overrides FitnessClass.base_price for this session.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )

    created_from_rule = models.ForeignKey(
        RecurrenceRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_sessions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("date", "start_time")

    def __str__(self) -> str:
        return f"{self.fitness_class.name} – {self.date} {self.start_time}"

    @property
    def capacity_effective(self) -> int:
        return self.capacity_override or self.fitness_class.capacity

    @property
    def price_effective(self) -> int:
        return self.price_override or self.fitness_class.base_price
