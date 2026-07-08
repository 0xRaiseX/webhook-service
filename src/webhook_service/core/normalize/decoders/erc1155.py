from typing import Optional, Dict, Any
from eth_utils import event_abi_to_log_topic, to_checksum_address
from eth_abi import decode

TRANSFER_SINGLE_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "operator", "type": "address"},
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": False, "name": "id", "type": "uint256"},
        {"indexed": False, "name": "value", "type": "uint256"},
    ],
    "name": "TransferSingle",
    "type": "event",
}
TRANSFER_BATCH_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "operator", "type": "address"},
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": False, "name": "ids", "type": "uint256[]"},
        {"indexed": False, "name": "values", "type": "uint256[]"},
    ],
    "name": "TransferBatch",
    "type": "event",
}
TRANSFER_SINGLE_TOPIC0 = event_abi_to_log_topic(TRANSFER_SINGLE_ABI).hex()
TRANSFER_BATCH_TOPIC0 = event_abi_to_log_topic(TRANSFER_BATCH_ABI).hex()


def try_decode_erc1155_transfer(topics: list[str], data: str, contract_address: str) -> Optional[Dict[str, Any]]:
    try:
        if topics[0].lower() == TRANSFER_SINGLE_TOPIC0.lower():
            if len(topics) != 4:
                return None
            operator = to_checksum_address("0x" + topics[1][-40:])
            from_addr = to_checksum_address("0x" + topics[2][-40:])
            to_addr = to_checksum_address("0x" + topics[3][-40:])
            decoded = decode(["uint256", "uint256"], bytes.fromhex(data[2:] if data.startswith("0x") else data))
            token_id, amount = decoded
            normalized = {
                "operator": operator,
                "from": from_addr,
                "to": to_addr,
                "token_id": str(token_id),
                "amount": str(amount),
                "token_address": to_checksum_address(contract_address),
                "token_standard": "erc1155",
            }
            return {
                "type": "nft.transfer",
                "normalized": normalized,
                "raw": {"abi_event": "TransferSingle(address,address,address,uint256,uint256)", "topics": topics, "data": data},
            }
        if topics[0].lower() == TRANSFER_BATCH_TOPIC0.lower():
            if len(topics) != 4:
                return None
            operator = to_checksum_address("0x" + topics[1][-40:])
            from_addr = to_checksum_address("0x" + topics[2][-40:])
            to_addr = to_checksum_address("0x" + topics[3][-40:])
            decoded = decode(["uint256[]", "uint256[]"], bytes.fromhex(data[2:] if data.startswith("0x") else data))
            ids, values = decoded
            normalized = {
                "operator": operator,
                "from": from_addr,
                "to": to_addr,
                "token_ids": [str(i) for i in ids],
                "amounts": [str(v) for v in values],
                "token_address": to_checksum_address(contract_address),
                "token_standard": "erc1155",
            }
            return {
                "type": "nft.transfer",
                "normalized": normalized,
                "raw": {"abi_event": "TransferBatch(address,address,address,uint256[],uint256[])", "topics": topics, "data": data},
            }
    except Exception:
        return None
    return None

