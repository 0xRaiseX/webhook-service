import time
from typing import Optional, Dict, Any
from eth_utils import to_checksum_address
from .types import RawLog
from .id import deterministic_event_id
from .decoders import (
    try_decode_erc20_transfer,
    try_decode_erc721_transfer,
    try_decode_erc1155_transfer,
    decode_with_abi,
)
from ..domain.event import CanonicalEvent, EventData, EventSource


def normalize_log(
    raw: RawLog,
    api_version: str,
    default_type: str = "contract.event",
    abi_event: Optional[Dict[str, Any]] = None,
) -> Optional[CanonicalEvent]:
    decoded = (
        try_decode_erc20_transfer(raw.topics, raw.data, raw.contract_address)
        or try_decode_erc721_transfer(raw.topics, raw.data, raw.contract_address)
        or try_decode_erc1155_transfer(raw.topics, raw.data, raw.contract_address)
    )
    if not decoded and abi_event:
        decoded = decode_with_abi(abi_event, raw.topics, raw.data)
    if not decoded:
        return None

    event_id = deterministic_event_id(raw.chain_id, raw.tx_hash, raw.log_index, api_version)
    evt = CanonicalEvent(
        id=event_id,
        type=decoded.get("type", default_type),
        created=int(time.time()),
        project_id="",
        api_version=api_version,
        source=EventSource(
            chain_id=raw.chain_id,
            network=None,
            block_number=raw.block_number,
            block_hash=raw.block_hash,
            tx_hash=raw.tx_hash,
            tx_index=raw.tx_index,
            log_index=raw.log_index,
            contract_address=to_checksum_address(raw.contract_address),
        ),
        data=EventData(normalized=decoded["normalized"], raw=decoded.get("raw")),
        links=None,
    )
    return evt

