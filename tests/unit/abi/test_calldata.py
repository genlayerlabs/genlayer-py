from genlayer_py.abi.calldata import decode, encode, to_str


def test_decode_type_bytes_returns_bytes():
    encoded = encode(b"hello")
    decoded = decode(encoded)
    assert isinstance(decoded, bytes)
    assert decoded == b"hello"


def test_decode_nested_bytes_returns_bytes():
    decoded = decode(encode({"data": b"\x00\x01\x02"}))
    assert isinstance(decoded["data"], bytes)
    assert decoded["data"] == b"\x00\x01\x02"


def test_to_str_handles_decoded_bytes():
    assert to_str(decode(encode(b"hello"))) == "b#68656c6c6f"
