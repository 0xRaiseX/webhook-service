from typing import Optional, Dict, Any
from eth_utils import event_abi_to_log_topic, to_checksum_address
from eth_abi import decode

TRANSFER_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": False, "name": "value", "type": "uint256"},
    ],
    "name": "Transfer",
    "type": "event",
}
TRANSFER_TOPIC0 = event_abi_to_log_topic(TRANSFER_ABI).hex()


def try_decode_erc20_transfer(topics: list[str], data: str, contract_address: str) -> Optional[Dict[str, Any]]:
    if len(topics) != 3 or topics[0].lower() != TRANSFER_TOPIC0.lower():
        return None
    try:
        from_addr = to_checksum_address("0x" + topics[1][-40:])
        to_addr = to_checksum_address("0x" + topics[2][-40:])
        value = decode(["uint256"], bytes.fromhex(data[2:] if data.startswith("0x") else data))[0]
        return {
            "type": "token.transfer",
            "normalized": {
                "from": from_addr,
                "to": to_addr,
                "amount": str(value),
                "token_address": to_checksum_address(contract_address),
            },
            "raw": {"abi_event": "Transfer(address,address,uint256)", "topics": topics, "data": data},
        }
    except Exception:
        return None

