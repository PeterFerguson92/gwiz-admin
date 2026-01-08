import json
import logging
from functools import lru_cache

from django.conf import settings

try:
    from twilio.base.exceptions import TwilioException
    from twilio.rest import Client
except ImportError:  # pragma: no cover - handled gracefully if deps missing
    Client = None  # type: ignore
    TwilioException = Exception  # type: ignore

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    enabled = getattr(settings, "WHATSAPP_NOTIFICATIONS_ENABLED", False)
    if not enabled:
        logger.debug("WhatsApp notifications disabled via settings.")
    return enabled


@lru_cache(maxsize=1)
def _get_client():
    if Client is None:
        logger.warning(
            "Twilio client not available while WhatsApp notifications are enabled. "
            "Make sure the 'twilio' package is installed."
        )
        return None

    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    if not (account_sid and auth_token):
        logger.warning("Twilio credentials missing; WhatsApp messaging disabled.")
        return None

    return Client(account_sid, auth_token)


def _format_user_name(user) -> str:
    if not user:
        return "Guest"
    return getattr(user, "full_name", "") or user.get_full_name() or user.get_username()


def _format_session_details(booking) -> tuple[str, str, str]:
    session = booking.class_session
    class_name = session.fitness_class.name
    date_str = session.date.strftime("%a %d %b %Y")
    time_str = session.start_time.strftime("%H:%M")
    return class_name, date_str, time_str


def _get_admin_recipients() -> list[str]:
    raw = getattr(settings, "TWILIO_WHATSAPP_ADMIN_RECIPIENTS", [])
    if isinstance(raw, str):
        raw = [raw]
    recipients = []
    for number in raw:
        if number:
            recipients.append(number.strip())
    return recipients


def _session_capacity_summary(booking) -> tuple[int, int]:
    session = booking.class_session
    capacity = session.capacity_override or session.fitness_class.capacity
    booked_count = session.bookings.filter(status=booking.STATUS_BOOKED).count()
    return booked_count, capacity


def _notify_admins_of_booking_event(booking, event: str) -> None:
    recipients = _get_admin_recipients()
    if not recipients:
        logger.debug(
            "No admin WhatsApp recipients configured; skipping %s alert.", event
        )
        return

    event_label = event
    user_name = _format_user_name(booking.user)
    class_name, date_str, time_str = _format_session_details(booking)
    booked_count, capacity = _session_capacity_summary(booking)
    summary = f"{booked_count}/{capacity}"
    body = (
        f"Booking {event_label}: {user_name} for {class_name} on "
        f"{date_str} at {time_str}. Currently {summary} spots booked."
    )

    template_sid = getattr(settings, "TWILIO_WHATSAPP_ADMIN_TEMPLATE_SID", "")

    template_vars = {
        "1": event_label,
        "2": user_name,
        "3": class_name,
        "4": date_str,
        "5": time_str,
        "6": summary,
    }

    for number in recipients:
        success = send_whatsapp_message(
            to_number=number,
            body=body,
            template_sid=template_sid or None,
            template_vars=template_vars if template_sid else None,
        )
        logger.info(
            "Sent admin WhatsApp %s notification for booking %s to %s: %s",
            event,
            booking.id,
            number,
            "ok" if success else "failed",
        )


def send_whatsapp_message(
    *,
    to_number: str,
    body: str | None = None,
    template_sid: str | None = None,
    template_vars: dict | None = None,
) -> bool:
    """Send the WhatsApp payload via Twilio.

    Returns True on success, False if skipped due to configuration issues or if
    Twilio raises an exception.
    """
    if not _is_enabled():
        logger.info("Skipping WhatsApp send because the feature is disabled.")
        return False

    if not to_number:
        logger.info("Skipping WhatsApp send because the user has no phone number.")
        return False

    from_number = getattr(settings, "TWILIO_WHATSAPP_FROM", "")
    client = _get_client()
    if not from_number or client is None:
        logger.warning("Twilio WhatsApp sender or client missing.")
        return False

    payload: dict[str, str] = {
        "from_": f"whatsapp:{from_number}",
        "to": f"whatsapp:{to_number}",
    }

    if template_sid:
        payload["content_sid"] = template_sid
        if template_vars:
            payload["content_variables"] = json.dumps(template_vars)
    else:
        payload["body"] = body or ""

    try:
        client.messages.create(**payload)
        return True
    except TwilioException:
        logger.exception("Failed to send WhatsApp message to %s", to_number)
        return False


def send_booking_confirmation(booking) -> bool:
    """
    Notify the user that the booking is confirmed.
    """
    if not _is_enabled():
        logger.info(
            "Skipping WhatsApp confirmation for booking %s because notifications are disabled.",
            booking.id,
        )
        return False

    user = booking.user
    class_name, date_str, time_str = _format_session_details(booking)
    template_sid = getattr(settings, "TWILIO_WHATSAPP_TEMPLATE_SID", "")
    event_label = "confirmed"
    template_vars = {
        "1": event_label,
        "2": _format_user_name(user),
        "3": class_name,
        "4": date_str,
        "5": time_str,
    }
    # Provide a simple body fallback for sandbox/dev testing.
    body = (
        f"Hi {_format_user_name(user)}, your booking for {class_name} on "
        f"{date_str} at {time_str} is {event_label}. See you soon!"
    )
    result = send_whatsapp_message(
        to_number=user.phone_number,
        body=body,
        template_sid=template_sid or None,
        template_vars=template_vars,
    )
    _notify_admins_of_booking_event(booking, "confirmed")
    return result


def send_booking_cancellation(booking) -> bool:
    """
    Notify the user that the booking is cancelled.
    """
    if not _is_enabled():
        logger.info(
            "Skipping WhatsApp cancellation for booking %s because notifications are disabled.",
            booking.id,
        )
        return False

    user = booking.user
    if not user:
        logger.info(
            "Skipping WhatsApp cancellation for guest booking %s (no user).",
            booking.id,
        )
        _notify_admins_of_booking_event(booking, "cancelled")
        return False
    class_name, date_str, time_str = _format_session_details(booking)
    template_sid = getattr(settings, "TWILIO_WHATSAPP_TEMPLATE_SID", "")
    event_label = "cancelled"
    template_vars = {
        "1": event_label,
        "2": _format_user_name(user),
        "3": class_name,
        "4": date_str,
        "5": time_str,
    }
    body = (
        f"Hi {_format_user_name(user)}, your booking for {class_name} on "
        f"{date_str} at {time_str} has been {event_label}. "
        "Reach out if you need help booking another session."
    )
    result = send_whatsapp_message(
        to_number=user.phone_number,
        body=body,
        template_sid=template_sid or None,
        template_vars=template_vars,
    )
    _notify_admins_of_booking_event(booking, "cancelled")
    return result
