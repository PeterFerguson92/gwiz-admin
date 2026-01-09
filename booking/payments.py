import json
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
    """
    Ensure the global Stripe client has the project secret key configured.
    """
    secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not secret:
        raise ImproperlyConfigured(
            "Stripe secret key is not configured. Set STRIPE_SECRET_KEY."
        )

    stripe.api_key = secret


def _convert_price_to_cents(amount: Decimal) -> int:
    """
    Convert a Decimal price into the integer amount (in cents) expected by Stripe.
    """
    if amount is None:
        raise ValueError("Session price is not configured.")

    decimal_amount = Decimal(amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    cents = int(decimal_amount * 100)

    if cents <= 0:
        raise ValueError("Session price must be greater than zero.")

    return cents


def _payment_description(booking) -> str:
    prefix = getattr(
        settings,
        "STRIPE_PAYMENT_DESCRIPTION_PREFIX",
        "Gwiz Class Booking",
    )
    session = booking.class_session
    class_name = session.fitness_class.name
    return f"{prefix}: {class_name} on {session.date}"


def _membership_payment_description(plan_name: str) -> str:
    prefix = getattr(settings, "STRIPE_PAYMENT_DESCRIPTION_PREFIX", "Gwiz Membership")
    return f"{prefix}: {plan_name}"


def create_payment_intent_for_booking(booking):
    """
    Create a Stripe PaymentIntent for the supplied booking instance.
    """
    _configure_stripe()

    session = booking.class_session
    amount_cents = _convert_price_to_cents(session.price_effective)

    metadata = {
        "booking_id": str(booking.id),
        "user_id": str(booking.user_id),
        "class_session_id": str(session.id),
        "type": "booking",
    }

    kwargs: Dict[str, Any] = {
        "amount": amount_cents,
        "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
        "metadata": metadata,
        "description": _payment_description(booking),
        "automatic_payment_methods": {
            "enabled": True,
            "allow_redirects": "never",  # avoid return_url requirement in CLI/local tests
        },
    }

    email = getattr(booking.user, "email", "")
    if email:
        kwargs["receipt_email"] = email

    intent = stripe.PaymentIntent.create(**kwargs)

    logger.debug(
        "Created Stripe PaymentIntent %s for booking %s",
        intent.id,
        booking.id,
    )

    return intent


def create_payment_intent_for_membership(purchase):
    """
    Create a Stripe PaymentIntent for a membership purchase.
    """
    _configure_stripe()

    amount_cents = _convert_price_to_cents(purchase.amount)
    metadata = {
        "membership_purchase_id": str(purchase.id),
        "user_id": str(purchase.user_id),
        "plan_id": str(purchase.plan_id),
    }

    kwargs: Dict[str, Any] = {
        "amount": amount_cents,
        "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
        "metadata": metadata,
        "description": _membership_payment_description(purchase.plan.name),
        "automatic_payment_methods": {
            "enabled": True,
            "allow_redirects": "never",
        },
    }

    email = getattr(purchase.user, "email", "")
    if email:
        kwargs["receipt_email"] = email

    intent = stripe.PaymentIntent.create(**kwargs)
    logger.debug(
        "Created Stripe PaymentIntent %s for membership purchase %s",
        intent.id,
        purchase.id,
    )
    return intent


def parse_stripe_event(payload: bytes, sig_header: str):
    """
    Parse the Stripe webhook payload. When STRIPE_WEBHOOK_SECRET is configured
    we verify the signature; otherwise we fall back to trusting the request body
    (suitable for local development).
    """
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise ImproperlyConfigured(
            "STRIPE_WEBHOOK_SECRET is not configured for booking webhooks."
        )

    return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
