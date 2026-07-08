from src.webhook_service.core.normalize.id import deterministic_event_id


def test_event_id_stable():
    a = deterministic_event_id("1", "0xabc", 3, "2026-01-13")
    b = deterministic_event_id("1", "0xabc", 3, "2026-01-13")
    assert a == b
    c = deterministic_event_id("1", "0xabc", 4, "2026-01-13")
    assert a != c

