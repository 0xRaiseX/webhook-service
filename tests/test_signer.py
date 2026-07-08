from src.webhook_service.core.delivery.signer import sign_event
from src.webhook_service.core.domain.event import CanonicalEvent, EventData, EventSource


def _dummy_event() -> CanonicalEvent:
    return CanonicalEvent(
        id="evt_test",
        type="token.transfer",
        created=1,
        project_id="proj",
        api_version="2026-01-13",
        source=EventSource(
            chain_id="1",
            network="ethereum",
            block_number=1,
            block_hash="0x0",
            tx_hash="0x1",
            tx_index=0,
            log_index=0,
            contract_address="0x0",
        ),
        data=EventData(normalized={}, raw={}),
    )


def test_signer():
    evt = _dummy_event()
    header, ts = sign_event("secret", evt, timestamp=100)
    assert "t=100" in header and "v1=" in header

