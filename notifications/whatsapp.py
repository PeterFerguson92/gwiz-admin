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
    return getattr(user, "full_name", "") or user.get_full_name() or user.get_username()


def _format_session_details(booking) -> tuple[str, str, str]:
    session = booking.class_session
    class_name = session.fitness_class.name
    date_str = session.date.strftime("%a %d %b %Y")
    time_str = session.start_time.strftime("%H:%M")
    return class_name, date_str, time_str


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
    template_sid = getattr(settings, "TWILIO_WHATSAPP_CONFIRM_TEMPLATE_SID", "")
    template_vars = {
        "1": _format_user_name(user),
        "2": class_name,
        "3": date_str,
        "4": time_str,
    }
    # Provide a simple body fallback for sandbox/dev testing.
    body = (
        f"Hi {_format_user_name(user)}, your spot for {class_name} on "
        f"{date_str} at {time_str} is confirmed. See you soon!"
    )
    return send_whatsapp_message(
        to_number=user.phone_number,
        body=body,
        template_sid=template_sid or None,
        template_vars=template_vars,
    )


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
    class_name, date_str, time_str = _format_session_details(booking)
    template_sid = getattr(settings, "TWILIO_WHATSAPP_CANCEL_TEMPLATE_SID", "")
    template_vars = {
        "1": _format_user_name(user),
        "2": class_name,
        "3": date_str,
        "4": time_str,
    }
    body = (
        f"Hi {_format_user_name(user)}, your booking for {class_name} on "
        f"{date_str} at {time_str} has been cancelled. "
        "Reach out if you need help booking another session."
    )
    return send_whatsapp_message(
        to_number=user.phone_number,
        body=body,
        template_sid=template_sid or None,
        template_vars=template_vars,
    )
