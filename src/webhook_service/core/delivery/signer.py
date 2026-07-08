import hmac
import hashlib
import time
from typing import Tuple
from ..domain.event import CanonicalEvent
import orjson


def sign_event(secret: str, event: CanonicalEvent, timestamp: int | None = None, delivery_id: str | None = None) -> Tuple[str, int]:
    ts = int(time.time()) if timestamp is None else timestamp
    payload = orjson.dumps(event.model_dump(), option=orjson.OPT_SORT_KEYS)
    msg = f"{ts}.".encode() + payload
    digest = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    # Webhook-Signature remains Stripe-like; separate headers carry id/timestamp
    header = f"t={ts},v1={digest}"
    return header, ts

