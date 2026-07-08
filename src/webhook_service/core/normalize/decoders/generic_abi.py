from typing import Optional, Dict, Any, List
from eth_abi import decode
from eth_utils import event_abi_to_log_topic, to_checksum_address


def decode_with_abi(abi_event: Dict[str, Any], topics: List[str], data: str) -> Optional[Dict[str, Any]]:
    try:
        topic0 = event_abi_to_log_topic(abi_event).hex()
        if topics[0].lower() != topic0.lower():
            return None
        indexed_inputs = [inp for inp in abi_event["inputs"] if inp.get("indexed")]
        non_indexed_inputs = [inp for inp in abi_event["inputs"] if not inp.get("indexed")]
        args: Dict[str, Any] = {}
        # decode indexed (topics[1:]) for address/string types only
        for topic_value, inp in zip(topics[1:], indexed_inputs):
            if inp["type"] == "address":
                args[inp["name"]] = to_checksum_address("0x" + topic_value[-40:])
            else:
                args[inp["name"]] = topic_value
        if non_indexed_inputs:
            types = [inp["type"] for inp in non_indexed_inputs]
            values = decode(types, bytes.fromhex(data[2:] if data.startswith("0x") else data))
            for inp, val in zip(non_indexed_inputs, values):
                args[inp["name"]] = val
        return {
            "type": "contract.event",
            "normalized": {
                "abi_event": abi_event.get("name"),
                "args": {k: _stringify(v) for k, v in args.items()},
            },
            "raw": {"abi_event": abi_event.get("name"), "topics": topics, "data": data},
        }
    except Exception:
        return None


def _stringify(value: Any) -> Any:
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, (list, tuple)):
        return [_stringify(v) for v in value]
    return value

