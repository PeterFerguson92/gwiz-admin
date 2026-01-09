import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django_resized import ResizedImageField
from storages.backends.s3boto3 import S3Boto3Storage

from events.upload import event_cover_upload_image_path

s3_storage = S3Boto3Storage()


class Event(models.Model):
    """
    Public event that members can buy tickets for.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cover_image = ResizedImageField(
        "Cover Image",
        upload_to=event_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Price per ticket; set to 0 for free events.",
    )
    payment_link = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional external payment link for this event.",
    )
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total number of tickets available.",
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Featured events surface first in lists.",
    )
    featured_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers show earlier among featured events.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive events are hidden from users."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_featured", "featured_order", "start_datetime", "name")

    def __str__(self):
        return self.name

    @property
    def tickets_reserved(self) -> int:
        """
        Count tickets in reserved/confirmed states (capacity is based on this).
        """
        total = (
            self.tickets.filter(status__in=EventTicket.ACTIVE_STATUSES)
            .aggregate(total=Sum("quantity"))
            .get("total")
        )
        return total or 0

    @property
    def remaining_tickets(self) -> int:
        return max(0, self.capacity - self.tickets_reserved)

    @property
    def is_sold_out(self) -> bool:
        return self.remaining_tickets <= 0


class EventTicket(models.Model):
    """
    A user's ticket purchase for an event.
    """

    STATUS_RESERVED = "reserved"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_RESERVED, "Reserved"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_INCLUDED = "included"  # free events or comped tickets
    PAYMENT_PENDING = "pending"  # awaiting Stripe payment
    PAYMENT_PAID = "paid"  # Stripe payment completed
    PAYMENT_VOID = "void"  # cancelled before payment

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_INCLUDED, "Included/Free"),
        (PAYMENT_PENDING, "Pending payment"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_VOID, "Voided/No payment due"),
    ]

    ACTIVE_STATUSES = (STATUS_RESERVED, STATUS_CONFIRMED)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        related_name="tickets",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="event_tickets",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_guest_purchase = models.BooleanField(default=False)
    guest_name = models.CharField(max_length=255, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RESERVED,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID for paid tickets.",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Tickets purchased in this order.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} → {self.event} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE_STATUSES

    @property
    def is_paid(self) -> bool:
        return self.payment_status in {self.PAYMENT_INCLUDED, self.PAYMENT_PAID}
