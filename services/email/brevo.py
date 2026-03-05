import base64
import logging
from email.utils import parseaddr
from typing import Any

import requests
from django.conf import settings

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
logger = logging.getLogger(__name__)


def _brevo_headers() -> dict[str, str]:
    api_key = getattr(settings, "BREVO_API_KEY", "") or ""
    if not api_key:
        raise ValueError("BREVO_API_KEY is not configured.")

    return {
        "api-key": api_key,
        "content-type": "application/json",
        "accept": "application/json",
    }


def _post_brevo(payload: dict[str, Any]) -> str | None:
    recipient = ""
    if payload.get("to"):
        recipient = payload["to"][0].get("email", "")
    logger.info(
        "Brevo API request prepared | to=%s | template_id=%s | has_html=%s | attachments=%s",
        recipient,
        payload.get("templateId"),
        bool(payload.get("htmlContent")),
        len(payload.get("attachment", [])),
    )

    response = requests.post(
        BREVO_ENDPOINT,
        headers=_brevo_headers(),
        json=payload,
        timeout=20,
    )

    if response.status_code < 200 or response.status_code >= 300:
        logger.error(
            "Brevo API request failed | to=%s | status=%s | body=%s",
            recipient,
            response.status_code,
            response.text,
        )
        raise RuntimeError(
            "Brevo API request failed "
            f"(status={response.status_code}, body={response.text})"
        )

    try:
        data = response.json()
    except ValueError:
        return None

    message_id = data.get("messageId")
    logger.info(
        "Brevo API request accepted | to=%s | status=%s | message_id=%s",
        recipient,
        response.status_code,
        message_id,
    )
    return message_id


def _resolve_sender(
    sender_email: str | None = None, sender_name: str | None = None
) -> dict[str, str]:
    raw_sender = sender_email or settings.DEFAULT_FROM_EMAIL
    parsed_name, parsed_email = parseaddr(raw_sender)

    sender_email = parsed_email or raw_sender
    sender_name = (
        sender_name or parsed_name or getattr(settings, "DEFAULT_FROM_NAME", None)
    )

    sender = {
        "email": sender_email,
    }
    if sender_name:
        sender["name"] = sender_name
    return sender


def send_brevo_template_email(
    recipient_email: str,
    template_id: int,
    params: dict,
    subject: str | None = None,
    sender_email: str | None = None,
    sender_name: str | None = None,
    attachments: list[dict] | None = None,
) -> str | None:
    sender = _resolve_sender(sender_email=sender_email, sender_name=sender_name)

    encoded_attachments = []
    for item in attachments or []:
        content = item.get("content", "")
        if isinstance(content, bytes):
            content = base64.b64encode(content).decode("utf-8")
        encoded_attachments.append(
            {
                "name": item.get("name", "attachment.bin"),
                "content": content,
            }
        )

    payload: dict[str, Any] = {
        "to": [{"email": recipient_email}],
        "templateId": int(template_id),
        "params": params or {},
        "sender": sender,
    }
    if encoded_attachments:
        payload["attachment"] = encoded_attachments

    if subject:
        payload["subject"] = subject

    return _post_brevo(payload)


def send_brevo_html_email(
    recipient_email: str,
    subject: str,
    html_content: str,
    sender_email: str,
    sender_name: str | None = None,
) -> str | None:
    sender = _resolve_sender(sender_email=sender_email, sender_name=sender_name)

    payload: dict[str, Any] = {
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content,
        "sender": sender,
    }

    return _post_brevo(payload)


def send_brevo_email_with_attachment(
    recipient_email: str,
    subject: str,
    html_content: str,
    sender_email: str,
    attachments: list[dict],
) -> str | None:
    sender = _resolve_sender(sender_email=sender_email)

    encoded_attachments = []
    for item in attachments or []:
        content = item.get("content", "")
        if isinstance(content, bytes):
            content = base64.b64encode(content).decode("utf-8")
        encoded_attachments.append(
            {
                "name": item.get("name", "attachment.bin"),
                "content": content,
            }
        )

    payload: dict[str, Any] = {
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content,
        "sender": sender,
        "attachment": encoded_attachments,
    }

    return _post_brevo(payload)
