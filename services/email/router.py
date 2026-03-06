import logging
from collections.abc import Callable
from email.utils import parseaddr

from django.conf import settings

from services.email.brevo import send_brevo_template_email

logger = logging.getLogger(__name__)


def _resolve_provider(flow_setting: str) -> str:
    flow_provider = getattr(settings, flow_setting, "") or ""
    global_provider = getattr(settings, "EMAIL_PROVIDER", "") or ""
    provider = (flow_provider or global_provider or "sendgrid").strip().lower()
    return provider


def _split_sender(
    sender_email: str | None, sender_name: str | None = None
) -> tuple[str, str | None]:
    raw_sender = sender_email or getattr(
        settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"
    )
    parsed_name, parsed_email = parseaddr(raw_sender)
    final_email = parsed_email or raw_sender
    final_name = sender_name if sender_name is not None else (parsed_name or None)
    return final_email, final_name


def send_password_reset_email_via_provider(
    *,
    recipient_email: str,
    subject: str,
    html_content: str,
    sendgrid_sender: Callable[[], bool],
    sender_email: str | None = None,
    sender_name: str | None = None,
    brevo_template_id: int | None = None,
    brevo_params: dict | None = None,
) -> bool:
    provider = _resolve_provider("EMAIL_PROVIDER_PASSWORD_RESET")
    logger.info(
        "Email provider selected for password reset: %s | to=%s | template_id=%s",
        provider,
        recipient_email,
        brevo_template_id,
    )

    if provider == "sendgrid":
        logger.info(
            "Dispatching password reset email via SendGrid callback | to=%s",
            recipient_email,
        )
        return sendgrid_sender()

    if provider == "brevo":
        sender_addr, sender_label = _split_sender(sender_email, sender_name)
        logger.info(
            "Dispatching password reset email via Brevo | to=%s | sender=%s | sender_name=%s",
            recipient_email,
            sender_addr,
            sender_label,
        )
        try:
            if not brevo_template_id:
                logger.error(
                    "Brevo password reset template id is missing; refusing non-template send for %s",
                    recipient_email,
                )
                return False
            message_id = send_brevo_template_email(
                recipient_email=recipient_email,
                template_id=brevo_template_id,
                params=brevo_params or {},
                subject=subject,
                sender_email=sender_addr,
                sender_name=sender_label,
            )
            logger.info(
                "Brevo password reset email accepted for %s (message_id=%s)",
                recipient_email,
                message_id,
            )
            return True
        except Exception:
            logger.exception(
                "Failed sending password reset email via Brevo to %s",
                recipient_email,
            )
            return False

    logger.error(
        "Unknown password reset email provider configured: %s (to=%s)",
        provider,
        recipient_email,
    )
    raise ValueError(f"Unknown email provider '{provider}' for password reset flow.")


def send_booking_email_via_provider(
    *,
    recipient_email: str,
    subject: str,
    html_content: str,
    sendgrid_sender: Callable[[], bool],
    sender_email: str | None = None,
    sender_name: str | None = None,
    brevo_template_id: int | None = None,
    brevo_params: dict | None = None,
) -> bool:
    provider = _resolve_provider("EMAIL_PROVIDER_BOOKING")
    logger.info(
        "Email provider selected for booking flow: %s | to=%s | template_id=%s",
        provider,
        recipient_email,
        brevo_template_id,
    )

    if provider == "sendgrid":
        logger.info(
            "Dispatching booking email via SendGrid callback | to=%s", recipient_email
        )
        return sendgrid_sender()

    if provider == "brevo":
        sender_addr, sender_label = _split_sender(sender_email, sender_name)
        logger.info(
            "Dispatching booking email via Brevo | to=%s | sender=%s | sender_name=%s",
            recipient_email,
            sender_addr,
            sender_label,
        )
        try:
            if not brevo_template_id:
                logger.error(
                    "Brevo booking template id is missing; refusing non-template send for %s",
                    recipient_email,
                )
                return False
            message_id = send_brevo_template_email(
                recipient_email=recipient_email,
                template_id=brevo_template_id,
                params=brevo_params or {},
                subject=subject,
                sender_email=sender_addr,
                sender_name=sender_label,
            )
            logger.info(
                "Brevo booking email accepted for %s (message_id=%s)",
                recipient_email,
                message_id,
            )
            return True
        except Exception:
            logger.exception(
                "Failed sending booking email via Brevo to %s",
                recipient_email,
            )
            return False

    logger.error(
        "Unknown booking email provider configured: %s (to=%s)",
        provider,
        recipient_email,
    )
    raise ValueError(f"Unknown email provider '{provider}' for booking flow.")


def send_event_email_via_provider(
    *,
    recipient_email: str,
    subject: str,
    html_content: str,
    sendgrid_sender: Callable[[], bool],
    sender_email: str | None = None,
    sender_name: str | None = None,
    brevo_template_id: int | None = None,
    brevo_params: dict | None = None,
    attachments: list[dict] | None = None,
) -> bool:
    provider = _resolve_provider("EMAIL_PROVIDER_EVENTS")
    logger.info(
        "Email provider selected for events flow: %s | to=%s | template_id=%s | attachments=%s",
        provider,
        recipient_email,
        brevo_template_id,
        len(attachments or []),
    )

    if provider == "sendgrid":
        logger.info(
            "Dispatching event email via SendGrid callback | to=%s", recipient_email
        )
        return sendgrid_sender()

    if provider == "brevo":
        sender_addr, sender_label = _split_sender(sender_email, sender_name)
        logger.info(
            "Dispatching event email via Brevo | to=%s | sender=%s | sender_name=%s",
            recipient_email,
            sender_addr,
            sender_label,
        )
        try:
            if not brevo_template_id:
                logger.error(
                    "Brevo events template id is missing; refusing non-template send for %s",
                    recipient_email,
                )
                return False
            message_id = send_brevo_template_email(
                recipient_email=recipient_email,
                template_id=brevo_template_id,
                params=brevo_params or {},
                subject=subject,
                sender_email=sender_addr,
                sender_name=sender_label,
                attachments=attachments,
            )
            logger.info(
                "Brevo event email accepted for %s (message_id=%s)",
                recipient_email,
                message_id,
            )
            return True
        except Exception:
            logger.exception(
                "Failed sending event email via Brevo to %s",
                recipient_email,
            )
            return False

    logger.error(
        "Unknown events email provider configured: %s (to=%s)",
        provider,
        recipient_email,
    )
    raise ValueError(f"Unknown email provider '{provider}' for events flow.")
