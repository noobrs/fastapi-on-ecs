from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

from config import settings

DEFAULT_TOLERANCE_SECONDS = 300


def build_signature_payload(payload: bytes, timestamp: str) -> bytes:
    return timestamp.encode("utf-8") + b"." + payload


def generate_signature(payload: bytes, timestamp: str) -> str:
    message = build_signature_payload(payload, timestamp)
    digest = hmac.new(
        key=settings.resume_pipeline_secret.encode("utf-8"),
        msg=message,
        digestmod=hashlib.sha256,
    )
    return digest.hexdigest()


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    try:
        if timestamp.endswith("Z"):
            timestamp = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(timestamp).astimezone(timezone.utc)
    except ValueError:
        return None


def verify_signature(
    payload: bytes,
    timestamp: Optional[str],
    signature: Optional[str],
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> bool:
    if not timestamp or not signature:
        return False

    parsed = parse_timestamp(timestamp)
    if parsed is None:
        return False

    now = datetime.now(timezone.utc)
    if abs((now - parsed).total_seconds()) > tolerance_seconds:
        return False

    expected = generate_signature(payload, timestamp)
    if len(expected) != len(signature):
        return False

    return hmac.compare_digest(expected, signature)
