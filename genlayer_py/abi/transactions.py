import rlp
from eth_utils import to_hex


def serialize(data):
    serialized_data = rlp.encode(data)
    return to_hex(serialized_data)
