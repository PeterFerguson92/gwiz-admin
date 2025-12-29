import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def stripe_enabled() -> bool:
    """
    Return True when a Stripe secret key has been configured.
    """
    return bool(getattr(settings, "STRIPE_SECRET_KEY", ""))


def _configure_stripe() -> None:
    secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not secret:
        raise ImproperlyConfigured(
            "Stripe secret key is not configured. Set STRIPE_SECRET_KEY."
        )
    stripe.api_key = secret


def _convert_price_to_cents(amount: Decimal) -> int:
    if amount is None:
        raise ValueError("Event price is not configured.")

    decimal_amount = Decimal(amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    cents = int(decimal_amount * 100)

    if cents < 0:
        raise ValueError("Event price cannot be negative.")

    return cents


def _payment_description(ticket) -> str:
    prefix = getattr(settings, "STRIPE_PAYMENT_DESCRIPTION_PREFIX", "Gwiz Event")
    event = ticket.event
    return f"{prefix}: {event.name} on {event.start_datetime.date()}"


def create_payment_intent_for_ticket(ticket):
    """
    Create a Stripe PaymentIntent for the supplied ticket purchase.
    Amount = ticket_price * quantity.
    """
    _configure_stripe()

    event = ticket.event
    amount_cents = _convert_price_to_cents(event.ticket_price) * ticket.quantity

    metadata = {
        "ticket_id": str(ticket.id),
        "user_id": str(ticket.user_id),
        "event_id": str(event.id),
    }

    kwargs: Dict[str, Any] = {
        "amount": amount_cents,
        "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
        "metadata": metadata,
        "description": _payment_description(ticket),
        "automatic_payment_methods": {
            "enabled": True,
            "allow_redirects": "never",  # avoid return_url requirement in CLI/local tests
        },
    }

    email = getattr(ticket.user, "email", "")
    if email:
        kwargs["receipt_email"] = email

    intent = stripe.PaymentIntent.create(**kwargs)

    logger.debug(
        "Created Stripe PaymentIntent %s for ticket %s",
        intent.id,
        ticket.id,
    )

    return intent


def refund_payment_intent(payment_intent_id: str) -> None:
    """
    Issue a refund for a PaymentIntent if configured. Swallows Stripe errors to
    avoid breaking cancellation flows; caller can handle logging.
    """
    if not payment_intent_id:
        return
    _configure_stripe()
    try:
        stripe.Refund.create(payment_intent=payment_intent_id)
    except stripe.error.StripeError:
        logger.exception("Stripe refund failed for PaymentIntent %s", payment_intent_id)


def parse_stripe_event(payload: bytes, sig_header: str):
    """
    Parse the Stripe webhook payload.

    Uses STRIPE_EVENTS_WEBHOOK_SECRET if set, otherwise falls back to
    STRIPE_WEBHOOK_SECRET. If neither is set we still attempt to construct
    the event (useful for local dev without signature verification).
    """
    webhook_secret = getattr(
        settings,
        "STRIPE_EVENTS_WEBHOOK_SECRET",
        getattr(settings, "STRIPE_WEBHOOK_SECRET", ""),
    )

    if webhook_secret:
        return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    return stripe.Webhook.construct_event(
        payload, sig_header or None, webhook_secret or None
    )
