from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from attendance.models import AttendanceLog
from attendance.rules import can_check_in_booking, can_check_in_ticket

User = get_user_model()


class AttendanceError(Exception):
    pass


class CheckInNotAllowed(AttendanceError):
    pass


class AlreadyCheckedIn(AttendanceError):
    pass


class NotCheckedIn(AttendanceError):
    pass


def _update_check_in_fields(
    obj: Any, *, checked_in_at: Any, checked_in_by: User | None
) -> None:
    obj.checked_in_at = checked_in_at
    obj.checked_in_by = checked_in_by

    update_fields = ["checked_in_at", "checked_in_by"]
    if hasattr(obj, "updated_at"):
        update_fields.append("updated_at")

    obj.save(update_fields=update_fields)


def _create_log(
    *,
    target_type: str,
    target_id: Any,
    action: str,
    actor: User | None,
    source: str,
    notes: str,
) -> AttendanceLog:
    return AttendanceLog.objects.create(
        target_type=target_type,
        target_id=str(target_id),
        action=action,
        actor=actor,
        source=source,
        notes=notes,
    )


def _raise_check_in_exception(obj: Any, reason: str | None) -> None:
    if getattr(obj, "checked_in_at", None) is not None:
        raise AlreadyCheckedIn(reason or "Already checked in.")
    raise CheckInNotAllowed(reason or "Check-in is not allowed.")


@transaction.atomic
def check_in_ticket(
    ticket: Any, *, actor: User | None, source: str = "manual", notes: str = ""
) -> Any:
    allowed, reason = can_check_in_ticket(ticket)
    if not allowed:
        _raise_check_in_exception(ticket, reason)

    checked_in_at = timezone.now()
    _update_check_in_fields(
        ticket,
        checked_in_at=checked_in_at,
        checked_in_by=actor,
    )
    _create_log(
        target_type=AttendanceLog.TARGET_TICKET,
        target_id=ticket.pk,
        action=AttendanceLog.ACTION_CHECKED_IN,
        actor=actor,
        source=source,
        notes=notes,
    )
    return ticket


@transaction.atomic
def revert_ticket_check_in(
    ticket: Any,
    *,
    actor: User | None,
    source: str = "manual",
    notes: str = "",
) -> Any:
    if getattr(ticket, "checked_in_at", None) is None:
        raise NotCheckedIn("Ticket is not checked in.")

    _update_check_in_fields(
        ticket,
        checked_in_at=None,
        checked_in_by=None,
    )
    _create_log(
        target_type=AttendanceLog.TARGET_TICKET,
        target_id=ticket.pk,
        action=AttendanceLog.ACTION_REVERTED,
        actor=actor,
        source=source,
        notes=notes,
    )
    return ticket


@transaction.atomic
def check_in_booking(
    booking: Any,
    *,
    actor: User | None,
    source: str = "manual",
    notes: str = "",
) -> Any:
    allowed, reason = can_check_in_booking(booking)
    if not allowed:
        _raise_check_in_exception(booking, reason)

    checked_in_at = timezone.now()
    _update_check_in_fields(
        booking,
        checked_in_at=checked_in_at,
        checked_in_by=actor,
    )
    _create_log(
        target_type=AttendanceLog.TARGET_BOOKING,
        target_id=booking.pk,
        action=AttendanceLog.ACTION_CHECKED_IN,
        actor=actor,
        source=source,
        notes=notes,
    )
    return booking


@transaction.atomic
def revert_booking_check_in(
    booking: Any,
    *,
    actor: User | None,
    source: str = "manual",
    notes: str = "",
) -> Any:
    if getattr(booking, "checked_in_at", None) is None:
        raise NotCheckedIn("Booking is not checked in.")

    _update_check_in_fields(
        booking,
        checked_in_at=None,
        checked_in_by=None,
    )
    _create_log(
        target_type=AttendanceLog.TARGET_BOOKING,
        target_id=booking.pk,
        action=AttendanceLog.ACTION_REVERTED,
        actor=actor,
        source=source,
        notes=notes,
    )
    return booking
