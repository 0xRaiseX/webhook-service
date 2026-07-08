from src.webhook_service.core.normalize.decoders.erc20 import try_decode_erc20_transfer, TRANSFER_TOPIC0


def test_decode_erc20_transfer():
    topics = [
        TRANSFER_TOPIC0,
        "0x" + "0" * 24 + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "0x" + "0" * 24 + "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    ]
    data = "0x" + (64 * "0")  # value = 0
    decoded = try_decode_erc20_transfer(topics, data, "0x" + "0" * 40)
    assert decoded is not None
    assert decoded["normalized"]["from"].lower().endswith("aaaaaaaa")

