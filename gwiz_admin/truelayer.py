import datetime
import json
import logging
import time
import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Tuple

import jwt
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from jwt.utils import base64url_encode

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 15


class TrueLayerError(RuntimeError):
    pass


def truelayer_enabled() -> bool:
    return bool(
        getattr(settings, "TRUE_LAYER_CLIENT_ID", "")
        and getattr(settings, "TRUE_LAYER_KEY_ID", "")
        and getattr(settings, "TRUE_LAYER_PRIVATE_KEY", "")
        and getattr(settings, "TRUE_LAYER_MERCHANT_ACCOUNT_ID", "")
    )


def _private_key() -> str:
    key = getattr(settings, "TRUE_LAYER_PRIVATE_KEY", "")
    if not key:
        raise ImproperlyConfigured(
            "TrueLayer private key is not configured. Set TRUE_LAYER_PRIVATE_KEY."
        )
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    return key


def _auth_token() -> str:
    client_id = getattr(settings, "TRUE_LAYER_CLIENT_ID", "")
    key_id = getattr(settings, "TRUE_LAYER_KEY_ID", "")
    audience = getattr(settings, "TRUE_LAYER_AUTH_AUDIENCE", "")
    if not client_id or not key_id or not audience:
        raise ImproperlyConfigured(
            "TrueLayer auth is not configured. Set TRUE_LAYER_CLIENT_ID/KEY_ID/AUDIENCE."
        )

    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": audience,
        "iat": now,
        "exp": now + 60,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        _private_key(),
        algorithm="RS256",
        headers={"kid": key_id, "typ": "JWT"},
    )
    return token


def _api_base() -> str:
    return getattr(settings, "TRUE_LAYER_API_BASE", "").rstrip("/")


def _headers(idempotency_key: str | None = None) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {_auth_token()}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def create_payment(
    *,
    amount_minor: int,
    currency: str,
    reference: str,
    return_url: str,
    webhook_url: str,
    metadata: Dict[str, Any] | None = None,
    payer: Dict[str, Any] | None = None,
) -> Tuple[str, str]:
    """
    Create a TrueLayer payment and return (payment_id, authorization_url).

    Note: uses the Payments v3 hosted flow. Ensure return_url and webhook_url
    are absolute URLs.
    """
    if amount_minor <= 0:
        raise ValueError("amount_minor must be a positive integer.")
    if not return_url:
        raise ValueError("return_url is required for TrueLayer payments.")
    if not webhook_url:
        raise ValueError("webhook_url is required for TrueLayer payments.")
    if not truelayer_enabled():
        raise ImproperlyConfigured("TrueLayer is not configured.")

    payload: Dict[str, Any] = {
        "amount_in_minor": amount_minor,
        "currency": currency.upper(),
        "reference": reference,
        "beneficiary": {
            "type": "merchant_account",
            "merchant_account_id": getattr(
                settings, "TRUE_LAYER_MERCHANT_ACCOUNT_ID", ""
            ),
        },
        "payment_method": {"type": "bank_transfer"},
        "redirect": {"return_uri": return_url},
        "webhook_uri": webhook_url,
    }
    if metadata:
        payload["metadata"] = metadata
    if payer:
        payload["user"] = payer

    idempotency_key = str(uuid.uuid4())
    response = requests.post(
        f"{_api_base()}/payments",
        headers=_headers(idempotency_key),
        data=json.dumps(payload),
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code >= 400:
        logger.error(
            "TrueLayer payment create failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise TrueLayerError("Failed to create TrueLayer payment.")

    data = response.json()
    payment_id = data.get("id")
    authorization_url = (
        data.get("authorization_flow", {}).get("actions", {}).get("next", {}).get("uri")
    )
    if not payment_id or not authorization_url:
        raise TrueLayerError("TrueLayer payment response missing id/authorization URL.")

    return payment_id, authorization_url


def cancel_payment(payment_id: str) -> None:
    if not payment_id:
        return
    try:
        response = requests.post(
            f"{_api_base()}/payments/{payment_id}/cancel",
            headers=_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code >= 400:
            logger.warning(
                "TrueLayer cancel failed: payment_id=%s status=%s body=%s",
                payment_id,
                response.status_code,
                response.text,
            )
    except Exception as exc:
        logger.warning("TrueLayer cancel failed: payment_id=%s err=%s", payment_id, exc)


def verify_webhook(
    signature: str | None, timestamp: str | None, payload: bytes
) -> bool:
    """
    Verify TrueLayer webhook signature with detached JWS payload.
    Requires TRUE_LAYER_WEBHOOK_SIGNING_KEY (public key PEM) to be set.
    """
    signing_key = getattr(settings, "TRUE_LAYER_WEBHOOK_SIGNING_KEY", "")
    if not signing_key:
        return True
    if not signature:
        return False

    tolerance = int(getattr(settings, "TRUE_LAYER_WEBHOOK_TOLERANCE_SEC", 300))
    if timestamp:
        try:
            ts = int(
                datetime.datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                ).timestamp()
            )
            now = int(time.time())
            if abs(now - ts) > tolerance:
                logger.warning("TrueLayer webhook timestamp outside tolerance.")
                return False
        except Exception:
            logger.warning("TrueLayer webhook timestamp invalid.")
            return False

    try:
        header = jwt.get_unverified_header(signature)
        alg = header.get("alg")
        if not alg:
            return False
        parts = signature.split(".")
        if len(parts) != 3:
            return False
        payload_b64 = base64url_encode(payload).decode("utf-8")
        reconstructed = f"{parts[0]}.{payload_b64}.{parts[2]}"
        jwt.decode(
            reconstructed,
            signing_key,
            algorithms=[alg],
            options={"verify_aud": False, "verify_exp": False},
        )
        return True
    except Exception as exc:
        logger.warning("TrueLayer webhook signature verification failed: %s", exc)
        return False


def normalize_status(raw: str | None) -> str:
    if not raw:
        return ""
    return raw.strip().lower()


def is_success_status(status: str) -> bool:
    return status in {"executed", "settled", "credited"}


def is_failure_status(status: str) -> bool:
    return status in {"failed", "cancelled", "canceled", "rejected", "expired"}


def to_minor_units(amount: Decimal) -> int:
    if amount is None:
        raise ValueError("Amount is required.")
    decimal_amount = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    minor = int(decimal_amount * 100)
    if minor <= 0:
        raise ValueError("Amount must be greater than zero.")
    return minor
