from genlayer_py.logging import logger
import rlp
from web3 import Web3
from eth_abi import decode as abi_decode
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI
from genlayer_py.abi import calldata


def decode_add_transaction_data(encoded_data):
    w3 = Web3()
    consensus_main_contract = w3.eth.contract(abi=CONSENSUS_MAIN_ABI)
    contract_fn = consensus_main_contract.get_function_by_name("addTransaction")
    abi_decoded = abi_decode(
        contract_fn.argument_types,
        w3.to_bytes(hexstr=encoded_data[10:]),
    )
    encoded_tx_data_bytes = abi_decoded[4]
    encoded_tx_data = Web3.to_hex(encoded_tx_data_bytes)
    decoded_tx_data = decode_tx_data(encoded_tx_data_bytes)
    return {
        "sender_address": abi_decoded[0],
        "recipient_address": abi_decoded[1],
        "num_of_initial_validators": abi_decoded[2],
        "max_rotations": abi_decoded[3],
        "tx_data": {
            "encoded": encoded_tx_data,
            "decoded": decoded_tx_data,
        },
    }


def decode_tx_data(encoded_data_bytes: bytes):
    try:
        deserialized_data = rlp.decode(encoded_data_bytes)
        if len(deserialized_data) == 3:
            return decode_tx_data_deploy(encoded_data_bytes)
        if len(deserialized_data) == 2:
            return decode_tx_data_call(encoded_data_bytes)
        logger.warning(
            "[decode_tx_data] Unexpected RLP array length: %s Raw RLP App Data: %s",
            len(deserialized_data),
            Web3.to_hex(encoded_data_bytes),
        )
        return None
    except Exception as e:
        logger.warning(
            "[decode_tx_data] Error decoding RLP: %s Raw RLP App Data: %s",
            e,
            Web3.to_hex(encoded_data_bytes),
        )
        return None


def decode_tx_data_call(encoded_data_bytes: bytes):
    deserialized_data = rlp.decode(encoded_data_bytes)
    if len(deserialized_data) != 2:
        logger.warning(
            "[decode_tx_data_call] Unexpected RLP array length: %s Raw RLP App Data: %s",
            len(deserialized_data),
            Web3.to_hex(encoded_data_bytes),
        )
        return None
    call_data = calldata.decode(deserialized_data[0]) if deserialized_data[0] else None
    decoded_data = {
        "call_data": call_data,
        "leader_only": deserialized_data[1] == b"\x01",
        "type": "call",
    }
    return decoded_data


def decode_tx_data_deploy(encoded_data_bytes: bytes):
    deserialized_data = rlp.decode(encoded_data_bytes)
    if len(deserialized_data) != 3:
        logger.warning(
            "[decode_tx_data_deploy] Unexpected RLP array length: %s Raw RLP App Data: %s",
            len(deserialized_data),
            Web3.to_hex(encoded_data_bytes),
        )
        return None
    constructor_args = (
        calldata.decode(deserialized_data[1]) if deserialized_data[1] else None
    )
    decoded_data = {
        "code": Web3.to_hex(deserialized_data[0]),
        "constructor_args": constructor_args,
        "leader_only": deserialized_data[2] == b"\x01",
        "type": "deploy",
    }
    return decoded_data
