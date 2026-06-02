import time
from typing import Optional, List, Dict
from genlayer_py.types import CalldataEncodable
from genlayer_py.abi.transactions import serialize
from genlayer_py.abi import calldata
from genlayer_py.contracts.utils import make_calldata_object
from web3 import Web3
from eth_abi import encode as abi_encode
from eth_typing import HexStr
import eth_utils
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI
from genlayer_py.transactions.fees import (
    TransactionFeeOptions,
    encode_fee_aware_add_transaction_data,
    normalize_transaction_fees,
)


def encode_add_transaction_data(
    sender_address: str,
    recipient_address: str,
    num_of_initial_validators: int,
    max_rotations: int,
    tx_data: HexStr,
    valid_until: int = 0,
    user_value: int = 0,
    salt_nonce: int = 0,
    fees: Optional[TransactionFeeOptions] = None,
    fee_aware: bool = False,
):
    w3 = Web3()
    consensus_main_contract = w3.eth.contract(abi=CONSENSUS_MAIN_ABI)
    transaction_fees = normalize_transaction_fees(fees)

    if (
        fee_aware
        or user_value != 0
        or transaction_fees["requires_fee_aware_transaction"]
    ):
        return encode_fee_aware_add_transaction_data(
            sender_address=sender_address,
            recipient_address=recipient_address,
            num_of_initial_validators=num_of_initial_validators,
            max_rotations=max_rotations,
            tx_data=tx_data,
            valid_until=valid_until or int(time.time()) + 3600,
            salt_nonce=salt_nonce,
            user_value=user_value,
            transaction_fees=transaction_fees,
        )

    contract_fn = consensus_main_contract.get_function_by_name("addTransaction")
    add_transaction_args = [
        sender_address,
        recipient_address,
        num_of_initial_validators,
        max_rotations,
        w3.to_bytes(hexstr=tx_data),
    ]
    if len(contract_fn.argument_types) >= 6:
        add_transaction_args.append(valid_until)

    params = abi_encode(
        contract_fn.argument_types,
        add_transaction_args,
    )
    function_selector = eth_utils.keccak(text=contract_fn.signature)[:4].hex()
    encoded_data = "0x" + function_selector + params.hex()
    return encoded_data


def encode_tx_data_call(
    function_name: str,
    leader_only: bool,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
):
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        leader_only,
    ]
    tx_data = serialize(data)
    return tx_data


def encode_tx_data_deploy(
    code: HexStr,
    leader_only: bool,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
):
    data = [
        code,
        calldata.encode(make_calldata_object(method=None, args=args, kwargs=kwargs)),
        leader_only,
    ]
    tx_data = serialize(data)
    return tx_data
