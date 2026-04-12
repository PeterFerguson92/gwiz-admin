from __future__ import annotations

from typing import Any

ALLOWED_PAYMENT_STATUSES = {"paid", "included"}
BLOCKED_PAYMENT_STATUSES = {"pending", "void"}
BLOCKED_STATUSES = {"cancelled"}


def _is_staff_user(obj: Any) -> bool:
    user = getattr(obj, "user", None)
    return bool(user and getattr(user, "is_staff", False))


def _already_checked_in(obj: Any) -> bool:
    return getattr(obj, "checked_in_at", None) is not None


def _can_check_in(
    obj: Any,
    *,
    required_status: str,
    kind: str,
) -> tuple[bool, str | None]:
    if _already_checked_in(obj):
        return False, f"{kind} has already been checked in."

    if _is_staff_user(obj):
        return True, None

    status = getattr(obj, "status", None)
    payment_status = getattr(obj, "payment_status", None)

    if status in BLOCKED_STATUSES:
        return False, f"{kind} is cancelled."

    if status != required_status:
        return False, f"{kind} must have status={required_status}."

    if payment_status in BLOCKED_PAYMENT_STATUSES:
        return False, f"{kind} payment is {payment_status}."

    if payment_status not in ALLOWED_PAYMENT_STATUSES:
        allowed_values = ",".join(sorted(ALLOWED_PAYMENT_STATUSES))
        return False, f"{kind} payment_status must be one of {allowed_values}."

    return True, None


def can_check_in_ticket(ticket: Any) -> tuple[bool, str | None]:
    return _can_check_in(ticket, required_status="confirmed", kind="Ticket")


def can_check_in_booking(booking: Any) -> tuple[bool, str | None]:
    return _can_check_in(booking, required_status="booked", kind="Booking")
