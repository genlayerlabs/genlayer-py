from __future__ import annotations
from eth_account.signers.local import LocalAccount
import eth_utils
from eth_abi import encode as abi_encode
from typing import TYPE_CHECKING, Optional, Union, List, Dict, AnyStr, Any
from eth_typing import Address, ChecksumAddress, HexStr
from genlayer_py.types import (
    CalldataEncodable,
    ContractSchema,
    TransactionHashVariant,
    SimConfig,
)
from genlayer_py.exceptions import GenLayerError
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import localnet
from web3.constants import ADDRESS_ZERO
from web3.logs import DISCARD
from genlayer_py.contracts.utils import make_calldata_object

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


def get_contract_schema(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
) -> ContractSchema:
    if self.chain.id != localnet.id:
        raise GenLayerError("Contract schema is not supported on this network")

    response = self.provider.make_request(
        method="gen_getContractSchema", params=[address]
    )
    return response["result"]


def get_contract_schema_for_code(
    self: GenLayerClient,
    contract_code: AnyStr,
) -> ContractSchema:
    if self.chain.id != localnet.id:
        raise GenLayerError("Contract schema is not supported on this network")

    response = self.provider.make_request(
        method="gen_getContractSchemaForCode",
        params=[eth_utils.hexadecimal.encode_hex(contract_code)],
    )
    return response["result"]


def read_contract(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
    function_name: str,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    account: Optional[LocalAccount] = None,
    raw_return: bool = False,
    transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
    sim_config: Optional[SimConfig] = None,
) -> CalldataEncodable:
    if account is None and self.local_account is None:
        raise GenLayerError("No account provided and no account is connected")
    sender_address = self.local_account.address
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        b"\x00",
    ]
    serialized_data = serialize(data)
    request_params = {
        "type": "read",
        "to": address,
        "from": sender_address,
        "data": serialized_data,
        "transaction_hash_variant": transaction_hash_variant.value,
    }
    if sim_config is not None:
        request_params["sim_config"] = sim_config
    enc_result = self.provider.make_request(
        method="gen_call",
        params=[request_params],
    )["result"]
    prefixed_result = "0x" + enc_result
    if raw_return:
        return prefixed_result
    result = calldata.decode(eth_utils.hexadecimal.decode_hex(prefixed_result))
    return result


def write_contract(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
    function_name: str,
    account: Optional[LocalAccount] = None,
    consensus_max_rotations: Optional[int] = None,
    value: int = 0,
    leader_only: bool = False,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    sim_config: Optional[SimConfig] = None,
):
    if consensus_max_rotations is None:
        consensus_max_rotations = self.chain.default_consensus_max_rotations
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        leader_only,
    ]
    sender_account = account if account is not None else self.local_account
    serialized_data = serialize(data)
    encoded_data = _encode_add_transaction_data(
        self=self,
        sender_account=sender_account,
        recipient=address,
        consensus_max_rotations=consensus_max_rotations,
        data=serialized_data,
    )
    return _send_transaction(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=value,
        sim_config=sim_config,
    )


def deploy_contract(
    self: GenLayerClient,
    code: Union[str, bytes],
    account: Optional[LocalAccount] = None,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    consensus_max_rotations: Optional[int] = None,
    leader_only: bool = False,
    sim_config: Optional[SimConfig] = None,
):
    if consensus_max_rotations is None:
        consensus_max_rotations = self.chain.default_consensus_max_rotations
    data = [
        code,
        calldata.encode(make_calldata_object(method=None, args=args, kwargs=kwargs)),
        leader_only,
    ]
    serialized_data = serialize(data)
    sender_account = account if account is not None else self.local_account

    encoded_data = _encode_add_transaction_data(
        self=self,
        sender_account=sender_account,
        recipient=ADDRESS_ZERO,
        consensus_max_rotations=consensus_max_rotations,
        data=serialized_data,
    )
    return _send_transaction(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        sim_config=sim_config,
    )


def appeal_transaction(
    self: GenLayerClient,
    transaction_id: HexStr,
    account: Optional[LocalAccount] = None,
    value: int = 0,
) -> None:
    sender_account = account if account is not None else self.local_account
    encoded_data = _encode_submit_appeal_data(self=self, transaction_id=transaction_id)

    return _send_transaction(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=value,
    )


def simulate_write_contract(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
    function_name: str,
    account: Optional[LocalAccount] = None,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    sim_config: Optional[SimConfig] = None,
    transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
) -> CalldataEncodable:
    if self.chain.id != localnet.id:
        raise GenLayerError("Client is not connected to the localnet")
    if account is None and self.local_account is None:
        raise GenLayerError("No account provided and no account is connected")
    sender_address = self.local_account.address if account is None else account.address
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        b"\x00",
    ]
    serialized_data = serialize(data)
    request_params = {
        "type": "write",
        "to": address,
        "from": sender_address,
        "data": serialized_data,
        "transaction_hash_variant": transaction_hash_variant.value,
    }
    if sim_config is not None:
        request_params["sim_config"] = sim_config
    receipt = self.provider.make_request(
        method="sim_call",
        params=[request_params],
    )["result"]
    return receipt


def _encode_submit_appeal_data(
    self: GenLayerClient,
    transaction_id: HexStr,
):
    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )
    contract_fn = consensus_main_contract.get_function_by_name("submitAppeal")
    if transaction_id.startswith("0x"):
        transaction_id = transaction_id[2:]
    if len(transaction_id) > 64:
        raise ValueError("transaction_id too long for bytes32")
    params = abi_encode(
        contract_fn.argument_types,
        [self.w3.to_bytes(hexstr=transaction_id)],
    )
    function_selector = eth_utils.keccak(text=contract_fn.signature)[:4].hex()
    encoded_data = "0x" + function_selector + params.hex()
    return encoded_data


def _encode_add_transaction_data(
    self: GenLayerClient,
    sender_account,
    recipient,
    consensus_max_rotations,
    data,
    valid_until: int = 0,
):
    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )
    contract_fn = consensus_main_contract.get_function_by_name("addTransaction")
    params = abi_encode(
        contract_fn.argument_types,
        [
            sender_account.address,
            recipient,
            self.chain.default_number_of_initial_validators,
            consensus_max_rotations,
            self.w3.to_bytes(hexstr=data),
            valid_until,
        ],
    )
    function_selector = eth_utils.keccak(text=contract_fn.signature)[:4].hex()
    encoded_data = "0x" + function_selector + params.hex()
    return encoded_data


def _prepare_transaction(
    self: GenLayerClient,
    sender: Union[Address, ChecksumAddress],
    recipient: Union[Address, ChecksumAddress],
    data: HexStr,
    value: int = 0,
) -> Dict[str, Any]:

    nonce = self.get_current_nonce(address=sender)

    if self.chain.id != localnet.id:
        latest_block = self.w3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        priority_fee = self.w3.to_wei(2, "gwei")
        max_fee = base_fee + priority_fee
        fee_data = {
            "maxFeePerGas": hex(max_fee),
            "maxPriorityFeePerGas": hex(priority_fee),
        }
    else:
        fee_data = {
            "gasPrice": 0,
        }

    transaction = {
        "from": sender,
        "nonce": hex(nonce),
        "data": data,
        "to": recipient,
        "value": hex(value),
        **fee_data,
        "chainId": self.chain.id,
    }
    transaction["gas"] = self.provider.make_request(
        "eth_estimateGas", params=[transaction]
    )["result"]
    return transaction


def _send_transaction(
    self: GenLayerClient,
    encoded_data: HexStr,
    sender_account: Optional[LocalAccount] = None,
    value: int = 0,
    sim_config: Optional[SimConfig] = None,
):
    if sender_account is None:
        raise GenLayerError(
            "No account set. Configure the client with an account or pass an account to this function."
        )

    if self.chain.consensus_main_contract is None:
        raise GenLayerError(
            "Consensus main contract not initialized. Please ensure client is properly initialized.",
        )

    transaction = _prepare_transaction(
        self=self,
        sender=sender_account.address,
        recipient=self.chain.consensus_main_contract["address"],
        data=encoded_data,
        value=value,
    )
    signed_transaction = sender_account.sign_transaction(transaction)
    serialized_transaction = self.w3.to_hex(signed_transaction.raw_transaction)
    params = [serialized_transaction]
    if sim_config is not None:
        params.append(sim_config)
    tx_hash = self.provider.make_request(
        method="eth_sendRawTransaction", params=params
    )["result"]
    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt.status != 1:
        raise GenLayerError("Transaction failed")

    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )
    event = consensus_main_contract.get_event_by_name("NewTransaction")
    events = event.process_receipt(tx_receipt, DISCARD)

    if len(events) == 0:
        raise GenLayerError("Transaction not processed by consensus")

    return self.w3.to_hex(events[0]["args"]["txId"])
