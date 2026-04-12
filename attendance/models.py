from django.conf import settings
from django.db import models


class AttendanceLog(models.Model):
    TARGET_TICKET = "ticket"
    TARGET_BOOKING = "booking"
    TARGET_TYPE_CHOICES = [
        (TARGET_TICKET, "Ticket"),
        (TARGET_BOOKING, "Booking"),
    ]

    ACTION_CHECKED_IN = "checked_in"
    ACTION_REVERTED = "reverted"
    ACTION_CHOICES = [
        (ACTION_CHECKED_IN, "Checked in"),
        (ACTION_REVERTED, "Reverted"),
    ]

    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual"),
    ]

    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
    )
    target_id = models.CharField(max_length=64)
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attendance_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"{self.target_type}:{self.target_id} {self.action}"
