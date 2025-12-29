import base64
import logging
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

from notifications.email import _format_from_email, _get_sendgrid_client

logger = logging.getLogger(__name__)

LOGO_URL = "https://gwiz-prod.s3.us-east-2.amazonaws.com/small_image_80_percent.png"


def _format_dt(dt):
    if dt is None:
        return ""
    if timezone.is_naive(dt):
        value = dt
    else:
        value = timezone.localtime(dt)
    tz_label = value.tzname() or ""
    formatted = value.strftime("%a, %b %d %Y %I:%M %p")
    return f"{formatted} {tz_label}".strip()


def build_ticket_pdf(ticket) -> bytes:
    """
    Generate a simple PDF ticket for the given EventTicket.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    event = ticket.event
    user_email = getattr(ticket.user, "email", "")

    start_dt = _format_dt(event.start_datetime)
    end_dt = _format_dt(event.end_datetime)

    lines = [
        f"Ticket for: {event.name}",
        f"Location: {event.location}",
        f"Starts: {start_dt}",
        f"Ends: {end_dt}" if end_dt else "",
        f"Quantity: {ticket.quantity}",
        f"Ticket ID: {ticket.id}",
        f"Event ID: {event.id}",
        f"User: {user_email}",
        f"Status: {ticket.status} / {ticket.payment_status}",
    ]

    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "Event Ticket")
    y -= 24
    c.setFont("Helvetica", 12)
    for line in lines:
        if not line:
            continue
        c.drawString(72, y, line)
        y -= 18

    c.showPage()
    c.save()
    return buf.getvalue()


def _build_template_data(ticket, to_email: str, status_text: str) -> dict:
    event = ticket.event
    start_dt = _format_dt(event.start_datetime)
    end_dt = _format_dt(event.end_datetime) if event.end_datetime else ""
    location_line = event.location or "TBA"

    return {
        "event_name": event.name,
        "location": location_line,
        "starts_at": start_dt,
        "ends_at": end_dt,
        "quantity": ticket.quantity,
        "ticket_id": str(ticket.id),
        "event_id": str(event.id),
        "user_email": to_email,
        "status": status_text,
        "logo_url": LOGO_URL,
    }


def send_ticket_confirmation_email(ticket) -> bool:
    client = _get_sendgrid_client()
    template_id = getattr(settings, "SENDGRID_TICKET_TEMPLATE_ID", "")
    if client is None or not template_id:
        logger.error("SendGrid ticket template not configured; skipping email.")
        return False

    user = ticket.user
    to_email = getattr(user, "email", "")
    if not to_email:
        logger.warning("Ticket %s has no user email; skipping email send.", ticket.id)
        return False

    pdf_bytes = build_ticket_pdf(ticket)
    encoded_pdf = base64.b64encode(pdf_bytes).decode()
    attachment = Attachment(
        FileContent(encoded_pdf),
        FileName(f"ticket-{ticket.id}.pdf"),
        FileType("application/pdf"),
        Disposition("attachment"),
    )

    from_email = _format_from_email()

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = _build_template_data(
        ticket,
        to_email,
        status_text=f"{ticket.status} / {ticket.payment_status}",
    )
    message.attachment = attachment

    try:
        response = client.send(message)
        logger.info(
            "Sent ticket confirmation email for ticket %s to %s (status %s)",
            ticket.id,
            to_email,
            getattr(response, "status_code", "?"),
        )
        return True
    except Exception:
        logger.exception(
            "Failed to send ticket confirmation email for ticket %s to %s",
            ticket.id,
            to_email,
        )
        return False


def send_ticket_cancellation_email(ticket) -> bool:
    client = _get_sendgrid_client()
    template_id = getattr(settings, "SENDGRID_TICKET_TEMPLATE_ID", "")
    if client is None or not template_id:
        logger.error("SendGrid ticket template not configured; skipping email.")
        return False

    user = ticket.user
    to_email = getattr(user, "email", "")
    if not to_email:
        logger.warning(
            "Ticket %s has no user email; skipping cancellation email.", ticket.id
        )
        return False

    from_email = _format_from_email()

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = _build_template_data(
        ticket,
        to_email,
        status_text="Cancelled / voided",
    )

    try:
        response = client.send(message)
        logger.info(
            "Sent ticket cancellation email for ticket %s to %s (status %s)",
            ticket.id,
            to_email,
            getattr(response, "status_code", "?"),
        )
        return True
    except Exception:
        logger.exception(
            "Failed to send ticket cancellation email for ticket %s to %s",
            ticket.id,
            to_email,
        )
        return False
