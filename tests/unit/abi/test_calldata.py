from genlayer_py.abi import calldata


def test_decode_bytes_returns_bytes():
    decoded = calldata.decode(calldata.encode(b"hello"))

    assert isinstance(decoded, bytes)
    assert decoded == b"hello"


def test_decoded_bytes_round_trip_through_to_str():
    value = b"hello"
    decoded = calldata.decode(calldata.encode(value))

    assert calldata.to_str(decoded) == calldata.to_str(value)
