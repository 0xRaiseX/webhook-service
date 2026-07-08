import hashlib


def deterministic_event_id(
    chain_id: str, tx_hash: str, log_index: int, api_version: str
) -> str:
    """Deterministic event id for logs."""
    payload = f"{chain_id}:{tx_hash}:{log_index}:{api_version}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    return f"evt_{digest}"

