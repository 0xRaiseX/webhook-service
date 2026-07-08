from datetime import datetime
from src.webhook_service.api.cursor import encode_cursor, decode_cursor


def test_cursor_roundtrip():
    now = datetime.utcnow().replace(microsecond=0)
    cur = encode_cursor(now, "abc")
    created, id_ = decode_cursor(cur)
    assert created == now
    assert id_ == "abc"
