import logging
from email.utils import parseaddr
from functools import lru_cache

from django.conf import settings

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:  # pragma: no cover
    SendGridAPIClient = None  # type: ignore
    Mail = None  # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_sendgrid_client():
    if not getattr(settings, "EMAIL_NOTIFICATIONS_ENABLED", True):
        logger.debug("Email notifications disabled via settings.")
        return None

    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    if not api_key:
        logger.error(
            "SENDGRID_API_KEY is not configured; password reset emails cannot be sent."
        )
        return None

    if SendGridAPIClient is None:
        logger.error(
            "sendgrid package is not installed. "
            "Run `pip install sendgrid` to enable password reset emails."
        )
        return None

    return SendGridAPIClient(api_key)


def _format_from_email():
    default_from = getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
    source = "settings.DEFAULT_FROM_EMAIL"
    if not default_from:
        default_from = getattr(settings, "SERVER_EMAIL", "").strip()
        source = "settings.SERVER_EMAIL"
    if not default_from:
        default_from = "webmaster@localhost"
        source = "fallback"

    name, email = parseaddr(default_from)
    if not email:
        email = default_from
    if name:
        formatted = f"{name} <{email}>"
    else:
        formatted = email

    logger.debug("Using %s for password reset emails: %s", source, formatted)
    return formatted


def send_password_reset_email(*, user, reset_url: str) -> bool:
    """
    Sends the password reset email via SendGrid.
    Returns True if the API accepts the email, False otherwise.
    """
    client = _get_sendgrid_client()
    if client is None or Mail is None:
        return False

    user_name = user.first_name or user.email
    subject = "Reset your Fsxcg password"
    plain_message = (
        f"Hi {user_name},\n\n"
        "We received a request to reset the password for your account.\n\n"
        f"To reset your password, click the link below:\n\n"
        f"{reset_url}\n\n"
        "If you did not request a password reset, you can safely ignore this email.\n\n"
        "Thanks,\n"
        "The Fsxcg Team"
    )

    html_message = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#f6f6f6; padding: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 520px; margin:auto; background:#ffffff; padding: 20px; border-radius: 8px;">
          <tr>
            <td>
              <h2 style="color:#333333;">Reset Your Password</h2>

              <p style="font-size: 15px; color:#555;">
                Hi {user_name},
              </p>

              <p style="font-size: 15px; color:#555;">
                We received a request to reset your password. Click the button below to choose a new one.
              </p>

              <p style="text-align:center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color:#007bff; color:white; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:bold;">
                  Reset Password
                </a>
              </p>

              <p style="font-size: 14px; color:#777;">
                If the button does not work, copy and paste this link into your browser:
              </p>

              <p style="font-size: 14px; word-break: break-all; color:#007bff;">
                {reset_url}
              </p>

              <hr style="border:none; border-top:1px solid #eee; margin: 25px 0;"/>

              <p style="font-size: 13px; color:#999;">
                If you did not request a password reset, you can safely ignore this email.
              </p>

              <p style="font-size: 14px; color:#333;">— The Fsxcg Team</p>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    from_email = _format_from_email()
    logger.info("Sending password reset email via SendGrid as %s", from_email)

    message = Mail(
        from_email=from_email,
        to_emails=user.email,
        subject=subject,
        plain_text_content=plain_message,
        html_content=html_message,
    )

    try:
        response = client.send(message)
        logger.info(
            "SendGrid accepted password reset email for %s (status %s).",
            user.email,
            response.status_code,
        )
        return True
    except Exception as exc:
        error_body = getattr(exc, "body", "")
        logger.exception(
            "SendGrid failed to send password reset email to %s. Response: %s",
            user.email,
            error_body,
        )
        return False
