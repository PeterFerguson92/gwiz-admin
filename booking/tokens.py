from django.conf import settings
from django.core import signing

CANCEL_TOKEN_SALT = "cancel-token"
CANCEL_TOKEN_MAX_AGE = getattr(
    settings, "CANCEL_TOKEN_MAX_AGE", 60 * 60 * 24 * 7
)  # 7 days


def generate_cancel_token(kind: str, obj_id) -> str:
    return signing.dumps({"kind": kind, "id": str(obj_id)}, salt=CANCEL_TOKEN_SALT)


def verify_cancel_token(token: str, expected_kind: str, expected_id) -> bool:
    try:
        data = signing.loads(
            token,
            salt=CANCEL_TOKEN_SALT,
            max_age=CANCEL_TOKEN_MAX_AGE,
        )
    except signing.BadSignature:
        return False
    return data.get("kind") == expected_kind and data.get("id") == str(expected_id)
