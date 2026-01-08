import logging

from django.conf import settings
from sendgrid.helpers.mail import Mail

from notifications.email import _format_from_email, _get_sendgrid_client

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(booking, cancel_token: str | None = None) -> bool:
    client = _get_sendgrid_client()
    template_id = getattr(settings, "SENDGRID_BOOKING_TEMPLATE_ID", "")
    if client is None or not template_id:
        logger.error("SendGrid booking template not configured; skipping email.")
        return False

    to_email = booking.guest_email or (
        getattr(booking.user, "email", "") if booking.user else ""
    )
    if not to_email:
        logger.warning(
            "Booking %s has no email; skipping booking confirmation.", booking.id
        )
        return False

    session = booking.class_session
    fc = session.fitness_class
    cancel_url = None
    if cancel_token:
        base = getattr(
            settings,
            "PUBLIC_SITE_URL",
            getattr(settings, "FRONTEND_RESET_PASSWORD_URL", ""),
        )
        cancel_url = f"{base}cancel?type=booking&id={booking.id}&token={cancel_token}"

    base_site = getattr(settings, "PUBLIC_SITE_URL", "")
    class_url = f"{base_site}classes/{fc.id}" if base_site else ""

    status_label = booking.status.replace("_", " ").title()
    payment_label = booking.payment_status.replace("_", " ").title()
    subject = f"FSXCG | Booking {status_label} | {fc.name}"

    data = {
        "class_name": fc.name,
        "class_id": str(fc.id),
        "session_date": session.date.isoformat(),
        "start_time": session.start_time.strftime("%H:%M")
        if session.start_time
        else "",
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else "",
        "booking_id": str(booking.id),
        "status": status_label,
        "payment_status": payment_label,
        "cancel_url": cancel_url,
        "class_url": class_url,
        "logo_url": getattr(
            settings,
            "LOGO_URL",
            f"{settings.STATIC_URL}admin/brand/logo.png",
        ),
        "subject": subject,
    }

    message = Mail(
        from_email=_format_from_email(),
        to_emails=to_email,
        subject=subject,
    )
    message.template_id = template_id
    message.dynamic_template_data = data
    # Ensure subject is set even with dynamic templates
    if message.personalizations:
        message.personalizations[0].subject = subject

    logger.info(
        "Sending booking email via SendGrid | booking=%s | to=%s | data=%s",
        booking.id,
        to_email,
        data,
    )

    try:
        response = client.send(message)
        logger.info(
            "Sent booking confirmation email for booking %s to %s (status %s)",
            booking.id,
            to_email,
            getattr(response, "status_code", "?"),
        )
        return True
    except Exception:
        logger.exception(
            "Failed to send booking confirmation email for booking %s to %s",
            booking.id,
            to_email,
        )
        return False
