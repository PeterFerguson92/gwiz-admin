import base64
import logging
from io import BytesIO

from django.conf import settings
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

from attendance.display import get_attendance_display_name
from attendance.qr import build_check_in_qr_context, draw_check_in_qr
from notifications.email import _format_from_email, _get_sendgrid_client
from services.email.router import send_booking_email_via_provider

logger = logging.getLogger(__name__)


def build_booking_pdf_lines(booking) -> list[str]:
    session = booking.class_session
    fitness_class = session.fitness_class
    attendee_name = get_attendance_display_name(booking)
    user_email = booking.guest_email or getattr(booking.user, "email", "")

    return [
        f"Booking for: {fitness_class.name}",
        f"Date: {session.date.isoformat()}",
        f"Time: {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
        f"Booking ID: {booking.id}",
        f"Session ID: {session.id}",
        f"Class ID: {fitness_class.id}",
        f"Name: {attendee_name}",
        f"User: {user_email}",
        f"Status: {booking.status} / {booking.payment_status}",
    ]


def build_booking_pdf(booking) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    qr_context = build_check_in_qr_context(booking.check_in_token)

    context = {
        "title": "Class Booking",
        "lines": build_booking_pdf_lines(booking),
        **qr_context,
    }

    qr_size = 132
    qr_x = width - 72 - qr_size
    qr_y = height - 72 - qr_size
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, context["title"])
    y -= 24
    c.setFont("Helvetica", 12)
    for line in context["lines"]:
        c.drawString(72, y, line)
        y -= 18

    draw_check_in_qr(c, booking.check_in_token, x=qr_x, y=qr_y, size=qr_size)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(qr_x, qr_y - 14, "Scan for check-in")

    c.showPage()
    c.save()
    return buf.getvalue()


def send_booking_confirmation_email(booking, cancel_token: str | None = None) -> bool:
    template_id = getattr(settings, "SENDGRID_BOOKING_TEMPLATE_ID", "")

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
        "header_banner_url": getattr(settings, "HEADER_BANNER_URL", ""),
        "subject": subject,
    }

    logger.info(
        "Preparing booking email | booking=%s | to=%s",
        booking.id,
        to_email,
    )
    pdf_bytes = build_booking_pdf(booking)

    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <p>Booking {status_label}</p>
        <p><strong>Class:</strong> {fc.name}</p>
        <p><strong>Date:</strong> {session.date.isoformat()}</p>
        <p><strong>Time:</strong> {data['start_time']} - {data['end_time']}</p>
        <p><strong>Payment:</strong> {payment_label}</p>
        <p><a href="{class_url}">View class details</a></p>
      </body>
    </html>
    """
    brevo_template_id = getattr(settings, "BREVO_TEMPLATE_ID_BOOKING", 0) or 0

    def _send_via_sendgrid() -> bool:
        client = _get_sendgrid_client()
        if client is None or not template_id:
            logger.error("SendGrid booking template not configured; skipping email.")
            return False

        encoded_pdf = base64.b64encode(pdf_bytes).decode()
        attachment = Attachment(
            FileContent(encoded_pdf),
            FileName(f"booking-{booking.id}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment"),
        )

        message = Mail(
            from_email=_format_from_email(),
            to_emails=to_email,
            subject=subject,
        )
        message.template_id = template_id
        message.dynamic_template_data = data
        if message.personalizations:
            message.personalizations[0].subject = subject
        message.attachment = attachment

        logger.info(
            "Sending booking email via SendGrid | booking=%s | to=%s | data=%s | pdf_bytes=%s",
            booking.id,
            to_email,
            data,
            len(pdf_bytes),
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

    return send_booking_email_via_provider(
        recipient_email=to_email,
        subject=subject,
        html_content=html_message,
        sendgrid_sender=_send_via_sendgrid,
        sender_email=_format_from_email(),
        brevo_template_id=int(brevo_template_id) if brevo_template_id else None,
        brevo_params=data,
        attachments=[
            {
                "name": f"booking-{booking.id}.pdf",
                "content": pdf_bytes,
            }
        ],
    )


def send_membership_renewal_email(
    membership,
    *,
    reminder_type: str,
    renew_url: str,
) -> bool:
    user = membership.user
    to_email = getattr(user, "email", "")
    if not to_email:
        logger.warning(
            "Membership %s has no user email; skipping renewal reminder.",
            membership.id,
        )
        return False

    reset_label = (
        membership.next_reset_at.strftime("%Y-%m-%d %H:%M")
        if membership.next_reset_at
        else ""
    )
    plan_name = membership.plan.name
    user_name = user.first_name or user.full_name or user.email

    if reminder_type == "renew_7_days":
        subject = f"FSXCG | Membership renewal due in 7 days ({plan_name})"
        lead_text = "Your membership renews in 7 days."
    elif reminder_type == "renew_3_days":
        subject = f"FSXCG | Membership renewal due in 3 days ({plan_name})"
        lead_text = "Your membership renews in 3 days."
    elif reminder_type == "renew_1_day":
        subject = f"FSXCG | Membership renewal due tomorrow ({plan_name})"
        lead_text = "Your membership renews tomorrow."
    else:
        subject = f"FSXCG | Membership expired ({plan_name})"
        lead_text = "Your membership has expired."

    plain_message = (
        f"Hi {user_name},\n\n"
        f"{lead_text}\n"
        f"Plan: {plan_name}\n"
        f"Renewal date: {reset_label}\n\n"
        f"Renew now: {renew_url}\n\n"
        "If you already renewed, you can ignore this message.\n\n"
        "The FSXCG Team"
    )

    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <p>Hi {user_name},</p>
        <p>{lead_text}</p>
        <p><strong>Plan:</strong> {plan_name}<br />
           <strong>Renewal date:</strong> {reset_label}</p>
        <p>
          <a href="{renew_url}" style="display:inline-block;padding:10px 16px;background:#111827;color:#fff;text-decoration:none;border-radius:6px;">
            Renew membership
          </a>
        </p>
        <p>If you already renewed, you can ignore this message.</p>
        <p>The FSXCG Team</p>
      </body>
    </html>
    """

    brevo_template_id = getattr(settings, "BREVO_TEMPLATE_ID_MEMBERSHIP", 0) or 0
    brevo_params = {
        "user_name": user_name,
        "lead_text": lead_text,
        "plan_name": plan_name,
        "reset_label": reset_label,
        "renew_url": renew_url,
        "subject": subject,
    }

    def _send_via_sendgrid() -> bool:
        client = _get_sendgrid_client()
        if client is None:
            return False

        message = Mail(
            from_email=_format_from_email(),
            to_emails=to_email,
            subject=subject,
            plain_text_content=plain_message,
            html_content=html_message,
        )

        try:
            response = client.send(message)
            logger.info(
                "Sent membership reminder email | membership=%s | type=%s | status=%s",
                membership.id,
                reminder_type,
                getattr(response, "status_code", "?"),
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send membership reminder email | membership=%s | type=%s",
                membership.id,
                reminder_type,
            )
            return False

    return send_booking_email_via_provider(
        recipient_email=to_email,
        subject=subject,
        html_content=html_message,
        sendgrid_sender=_send_via_sendgrid,
        sender_email=_format_from_email(),
        brevo_template_id=int(brevo_template_id) if brevo_template_id else None,
        brevo_params=brevo_params,
    )
