import rlp
from eth_utils import to_hex


def deserialize(data):
    deserialized_data = rlp.decode(data)
    return deserialized_data


def serialize(data):
    serialized_data = rlp.encode(data)
    return to_hex(serialized_data)
