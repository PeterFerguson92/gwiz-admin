import uuid

from django.db import models
from django.db.models import Q  # make sure this import exists at the top
from django.utils import timezone
from django_resized import ResizedImageField
from storages.backends.s3boto3 import S3Boto3Storage

from booking.upload import fitness_class_cover_upload_image_path
from gwiz_admin import settings
from homepage.models import Trainer

s3_storage = S3Boto3Storage()

BOOKING_PAYMENT_COUNTED = ("included", "paid")


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
    payment_link = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional external payment/booking link.",
    )
    payment_link = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional external payment/booking link.",
    )
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


class Booking(models.Model):
    """
    A user's booking for a specific ClassSession.
    Handles membership-included bookings, PAYG bookings (via Stripe),
    and attendance tracking.
    """

    # --- Status choices ---
    STATUS_BOOKED = "booked"
    STATUS_CANCELLED = "cancelled"
    STATUS_NO_SHOW = "no_show"

    STATUS_CHOICES = [
        (STATUS_BOOKED, "Booked"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_NO_SHOW, "No-show"),
    ]

    # --- Payment status choices ---
    PAYMENT_INCLUDED = "included"  # covered by membership / credits
    PAYMENT_PENDING = "pending"  # awaiting Stripe payment
    PAYMENT_PAID = "paid"  # Stripe payment completed
    PAYMENT_VOID = "void"  # added for cancelled pending payments

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_INCLUDED, "Included in membership"),
        (PAYMENT_PENDING, "Pending payment"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_VOID, "Voided/No payment due"),
    ]
    PAYMENT_COUNTED = BOOKING_PAYMENT_COUNTED

    # --- Attendance choices ---
    ATTENDANCE_UNKNOWN = "unknown"
    ATTENDANCE_PRESENT = "present"
    ATTENDANCE_ABSENT = "absent"
    ATTENDANCE_NO_SHOW = "no_show"

    ATTENDANCE_CHOICES = [
        (ATTENDANCE_UNKNOWN, "Not marked"),
        (ATTENDANCE_PRESENT, "Present"),
        (ATTENDANCE_ABSENT, "Absent"),
        (ATTENDANCE_NO_SHOW, "No-show"),
    ]

    # --- Fields ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bookings",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_guest_purchase = models.BooleanField(default=False)
    guest_name = models.CharField(max_length=255, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=50, blank=True)

    class_session = models.ForeignKey(
        "booking.ClassSession",
        related_name="bookings",
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_BOOKED,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_INCLUDED,
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID for PAYG bookings.",
    )

    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_CHOICES,
        default=ATTENDANCE_UNKNOWN,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Meta / constraints ---
    class Meta:
        # You can’t have two *active* bookings for the same session
        constraints = [
            models.UniqueConstraint(
                fields=["user", "class_session"],
                condition=Q(status="booked")
                & Q(user__isnull=False)
                & Q(payment_status__in=BOOKING_PAYMENT_COUNTED),
                name="unique_active_booking_per_session",
            )
        ]
        ordering = ("-created_at",)

    # --- Helpers ---
    def __str__(self) -> str:
        return f"{self.user} → {self.class_session} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status == self.STATUS_BOOKED

    @property
    def is_included(self) -> bool:
        """True if this booking was covered by membership/credits."""
        return self.payment_status == self.PAYMENT_INCLUDED

    @property
    def is_paid(self) -> bool:
        """True if payment has been completed (membership or Stripe)."""
        return self.payment_status in {self.PAYMENT_INCLUDED, self.PAYMENT_PAID}

    @property
    def attendance_marked(self) -> bool:
        """True if attendance has been explicitly set."""
        return self.attendance_status != self.ATTENDANCE_UNKNOWN

    @property
    def is_present(self) -> bool:
        return self.attendance_status == self.ATTENDANCE_PRESENT

    @property
    def is_no_show(self) -> bool:
        return self.attendance_status == self.ATTENDANCE_NO_SHOW


class MembershipPlan(models.Model):
    TYPE_SESSION_BASED = "session_based"
    TYPE_CHOICES = [
        (TYPE_SESSION_BASED, "Session based"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    plan_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=TYPE_SESSION_BASED,
    )
    included_class_sessions = models.PositiveIntegerField(default=0)
    included_events = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class UserMembership(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    plan = models.ForeignKey(
        MembershipPlan,
        related_name="memberships",
        on_delete=models.PROTECT,
    )
    remaining_class_sessions = models.PositiveIntegerField(default=0)
    remaining_events = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} – {self.plan.name} ({self.status})"

    @property
    def is_active_membership(self) -> bool:
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class MembershipUsage(models.Model):
    KIND_CLASS = "class"
    KIND_EVENT = "event"
    KIND_CHOICES = [
        (KIND_CLASS, "Class session"),
        (KIND_EVENT, "Event ticket"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membership = models.ForeignKey(
        UserMembership,
        related_name="usages",
        on_delete=models.CASCADE,
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    amount = models.PositiveIntegerField(default=1)
    reference_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Booking or ticket id this usage is tied to.",
    )
    reversed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.kind} usage ({self.amount}) for {self.membership}"


class MembershipPurchase(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="membership_purchases",
        on_delete=models.CASCADE,
    )
    plan = models.ForeignKey(
        MembershipPlan,
        related_name="purchases",
        on_delete=models.PROTECT,
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID for membership purchase.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.plan.name} for {self.user} ({self.status})"
