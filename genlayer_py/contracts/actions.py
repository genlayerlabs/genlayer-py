from __future__ import annotations
import time
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
from genlayer_py.transactions.fees import (
    FeeEstimateOptions,
    FeePolicyQuote,
    FeesDistributionInput,
    FeesDistribution,
    FEES_DISTRIBUTION_ABI_TYPE,
    DEFAULT_BOOTLOADER_OVERHEAD,
    DEFAULT_CALLDATA_GAS_PER_BYTE,
    DEFAULT_FIXED_PROPOSE_RECEIPT_GAS,
    DEFAULT_GAS_PER_CHANGED_SLOT,
    DEFAULT_INTRINSIC_GAS,
    DEFAULT_RECEIPT_SLOTS_CHANGED,
    MIN_RECEIPT_BYTES,
    NormalizedTransactionFees,
    SimulationFeeEstimateOptions,
    TransactionFeeEstimate,
    TransactionFeeOptions,
    build_estimated_fees_distribution,
    build_estimated_fees_options_from_simulation,
    calculate_local_round_fees,
    create_fees_distribution,
    encode_fee_aware_add_transaction_data,
    extract_studio_fee_policy,
    fees_distribution_to_abi_tuple,
    normalize_transaction_fees,
    requires_fee_deposit_calculation,
    to_uint,
    transaction_fee_estimate_from_studio_estimate,
)

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

    code_bytes = (
        contract_code.encode("utf-8")
        if isinstance(contract_code, str)
        else contract_code
    )
    response = self.provider.make_request(
        method="gen_getContractSchemaForCode",
        params=[eth_utils.hexadecimal.encode_hex(code_bytes)],
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
    sender = account if account is not None else self.local_account
    sender_address = sender.address
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
    valid_until: Optional[int] = None,
    fees: Optional[TransactionFeeOptions] = None,
):
    if consensus_max_rotations is None:
        consensus_max_rotations = self.chain.default_consensus_max_rotations
    self.initialize_consensus_smart_contract()
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        leader_only,
    ]
    sender_account = account if account is not None else self.local_account
    serialized_data = serialize(data)
    transaction_fees = _resolve_transaction_fees(
        self=self,
        fees=fees,
        num_of_initial_validators=self.chain.default_number_of_initial_validators,
    )
    encoded_data = _encode_add_transaction_data(
        self=self,
        sender_account=sender_account,
        recipient=address,
        consensus_max_rotations=consensus_max_rotations,
        data=serialized_data,
        valid_until=valid_until,
        user_value=value,
        transaction_fees=transaction_fees,
    )
    return _send_transaction(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=value + (transaction_fees["fee_value"] or 0),
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
    valid_until: Optional[int] = None,
    fees: Optional[TransactionFeeOptions] = None,
):
    if consensus_max_rotations is None:
        consensus_max_rotations = self.chain.default_consensus_max_rotations
    self.initialize_consensus_smart_contract()
    data = [
        code,
        calldata.encode(make_calldata_object(method=None, args=args, kwargs=kwargs)),
        leader_only,
    ]
    serialized_data = serialize(data)
    sender_account = account if account is not None else self.local_account
    transaction_fees = _resolve_transaction_fees(
        self=self,
        fees=fees,
        num_of_initial_validators=self.chain.default_number_of_initial_validators,
    )

    encoded_data = _encode_add_transaction_data(
        self=self,
        sender_account=sender_account,
        recipient=ADDRESS_ZERO,
        consensus_max_rotations=consensus_max_rotations,
        data=serialized_data,
        valid_until=valid_until,
        user_value=0,
        transaction_fees=transaction_fees,
    )
    return _send_transaction(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=transaction_fees["fee_value"] or 0,
        sim_config=sim_config,
    )


def appeal_transaction(
    self: GenLayerClient,
    transaction_id: HexStr,
    account: Optional[LocalAccount] = None,
    value: Optional[int] = None,
    expected_decision_id: Optional[int] = None,
) -> HexStr:
    """Appeals a consensus transaction. Returns the original transaction_id.

    Appeals emit AppealStarted/TransactionActivated events (not NewTransaction),
    so we send the EVM tx directly instead of going through _send_transaction.
    Both Studio and deployed Consensus bind the appeal to the exact active
    decision and can resolve omitted decision/value inputs from the
    authoritative appeal quote.
    """
    sender_account = account if account is not None else self.local_account
    if sender_account is None:
        raise GenLayerError("No account set.")
    if self.chain.consensus_main_contract is None:
        raise GenLayerError("Consensus main contract not configured.")
    expected_decision_id, resolved_value = _resolve_appeal_parameters(
        self,
        transaction_id,
        expected_decision_id=expected_decision_id,
        value=value,
    )

    encoded_data = _encode_submit_appeal_data(
        self=self,
        transaction_id=transaction_id,
        expected_decision_id=expected_decision_id,
    )

    _send_consensus_call(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=resolved_value,
        operation_name="Appeal",
    )

    return transaction_id


def top_up_fees(
    self: GenLayerClient,
    transaction_id: HexStr,
    distribution: FeesDistributionInput,
    value: int,
    account: Optional[LocalAccount] = None,
) -> HexStr:
    """Deposits additional fee budget for an existing consensus transaction.

    Returns the backend RPC hash: an EVM transaction hash on network backends,
    or the target GenLayer tx id on Studio/localnet.
    """
    sender_account = account if account is not None else self.local_account
    encoded_data = _encode_fee_management_data(
        self=self,
        function_name="topUpFees",
        transaction_id=transaction_id,
        distribution=distribution,
    )
    return _send_consensus_call(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=value,
        operation_name="Top up fees",
    )


def top_up_and_submit_appeal(
    self: GenLayerClient,
    transaction_id: HexStr,
    distribution: FeesDistributionInput,
    account: Optional[LocalAccount] = None,
    value: Optional[int] = None,
    expected_decision_id: Optional[int] = None,
) -> HexStr:
    """Deposits appeal fee budget and submits an appeal in one consensus call.

    Returns the original GenLayer transaction id, matching appeal_transaction.
    Both Studio and deployed Consensus use the decision-bound train shape.
    """
    sender_account = account if account is not None else self.local_account
    expected_decision_id, resolved_value = _resolve_appeal_parameters(
        self,
        transaction_id,
        expected_decision_id=expected_decision_id,
        value=value,
    )
    encoded_data = _encode_fee_management_data(
        self=self,
        function_name="topUpAndSubmitAppeal",
        transaction_id=transaction_id,
        distribution=distribution,
        expected_decision_id=expected_decision_id,
    )
    _send_consensus_call(
        self=self,
        encoded_data=encoded_data,
        sender_account=sender_account,
        value=resolved_value,
        operation_name="Top up and submit appeal",
    )
    return transaction_id


def get_round_number(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> int:
    """Returns the current consensus round number for a transaction."""
    if self.chain.rounds_storage_contract is None:
        raise GenLayerError("rounds_storage_contract not configured for this chain")
    contract = self.w3.eth.contract(
        address=self.w3.to_checksum_address(
            self.chain.rounds_storage_contract["address"]
        ),
        abi=self.chain.rounds_storage_contract["abi"],
    )
    tx_bytes = _to_bytes32(self, transaction_id)
    return contract.functions.getRoundNumber(tx_bytes).call()


def get_round_data(
    self: GenLayerClient,
    transaction_id: HexStr,
    round: int,
) -> dict:
    """Returns detailed data for a specific consensus round."""
    if self.chain.rounds_storage_contract is None:
        raise GenLayerError("rounds_storage_contract not configured for this chain")
    contract = self.w3.eth.contract(
        address=self.w3.to_checksum_address(
            self.chain.rounds_storage_contract["address"]
        ),
        abi=self.chain.rounds_storage_contract["abi"],
    )
    tx_bytes = _to_bytes32(self, transaction_id)
    return contract.functions.getRoundData(tx_bytes, round).call()


def get_last_round_data(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> tuple:
    """Returns the current round number and its data."""
    if self.chain.rounds_storage_contract is None:
        raise GenLayerError("rounds_storage_contract not configured for this chain")
    contract = self.w3.eth.contract(
        address=self.w3.to_checksum_address(
            self.chain.rounds_storage_contract["address"]
        ),
        abi=self.chain.rounds_storage_contract["abi"],
    )
    tx_bytes = _to_bytes32(self, transaction_id)
    return contract.functions.getLastRoundData(tx_bytes).call()


def can_appeal(
    self: GenLayerClient,
    transaction_id: HexStr,
    expected_decision_id: Optional[int] = None,
) -> bool:
    """Checks whether the exact active decision can be appealed on a network.

    When no decision id is supplied, the latest active decision is read first.
    The guarded on-chain call returns ``False`` if that decision changes before
    it is evaluated. Studio uses its lifecycle and appeal-quote RPCs for the
    same semantics.
    """
    if _is_studio_chain(self):
        lifecycle = self.get_transaction_lifecycle(transaction_id)
        if not lifecycle["decision_active"]:
            return False
        active_decision_id = lifecycle["decision_id"]
        if (
            expected_decision_id is not None
            and expected_decision_id != active_decision_id
        ):
            return False
        try:
            return get_appeal_quote(self, transaction_id)["decision_id"] == int(
                active_decision_id
            )
        except Exception as exc:
            if "CanNotAppeal" in str(exc):
                return False
            raise

    if self.chain.appeals_contract is None:
        raise GenLayerError("appeals_contract not configured for this chain")
    if expected_decision_id is None:
        expected_decision_id = _get_active_decision_id(self, transaction_id)
        if expected_decision_id is None:
            return False
    contract = _appeals_contract(self)
    tx_bytes = _to_bytes32(self, transaction_id)
    return contract.functions.canAppeal(tx_bytes, expected_decision_id).call()


def get_appeal_quote(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> Dict[str, int]:
    """Returns the exact latest-decision appeal charge and race guard.

    ``total`` is the value to submit: the appeal bond plus induced-work
    funding. Pass ``decision_id`` back to the decision-guarded appeal methods.
    """
    if _is_studio_chain(self):
        response = self.provider.make_request(
            method="gen_estimateLatestAppealCharge",
            params=[{"txId": transaction_id}],
        )
        if not isinstance(response, dict):
            raise GenLayerError(
                "gen_estimateLatestAppealCharge returned an invalid response"
            )
        if response.get("error") is not None:
            raise GenLayerError(
                f"gen_estimateLatestAppealCharge failed: {response['error']}"
            )
        quote = response.get("result")
        if not isinstance(quote, dict):
            raise GenLayerError(
                "gen_estimateLatestAppealCharge returned an invalid result"
            )
        decision_id = int(quote["decisionId"])
        bond = int(quote["bond"])
        funding = int(quote["funding"])
        return {
            "decision_id": decision_id,
            "bond": bond,
            "funding": funding,
            "total": bond + funding,
            "appeal_deadline": int(quote["appealDeadline"]),
        }
    contract = _consensus_data_contract(self)
    decision_id, bond, funding, appeal_deadline = (
        contract.functions.estimateLatestAppealCharge(
            _to_bytes32(self, transaction_id)
        ).call()
    )
    return {
        "decision_id": int(decision_id),
        "bond": int(bond),
        "funding": int(funding),
        "total": int(bond) + int(funding),
        "appeal_deadline": int(appeal_deadline),
    }


def get_appeal_charge(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> int:
    """Returns the full payment required to appeal the latest decision."""
    return get_appeal_quote(self, transaction_id)["total"]


def get_min_appeal_bond(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> int:
    """Deprecated alias for :func:`get_appeal_charge`.

    Despite its historical name, this returns bond plus induced-work funding.
    """
    return get_appeal_charge(self, transaction_id)


def _consensus_data_contract(self: GenLayerClient):
    if self.chain.consensus_data_contract is None:
        raise GenLayerError("consensus_data_contract not configured for this chain")
    return self.w3.eth.contract(
        address=self.w3.to_checksum_address(
            self.chain.consensus_data_contract["address"]
        ),
        abi=self.chain.consensus_data_contract["abi"],
    )


def _appeals_contract(self: GenLayerClient):
    if self.chain.appeals_contract is None:
        raise GenLayerError("appeals_contract not configured for this chain")
    return self.w3.eth.contract(
        address=self.w3.to_checksum_address(self.chain.appeals_contract["address"]),
        abi=self.chain.appeals_contract["abi"],
    )


def _get_active_decision_id(
    self: GenLayerClient,
    transaction_id: HexStr,
) -> Optional[int]:
    lifecycle = (
        _consensus_data_contract(self)
        .functions.getTransactionLifecycle(_to_bytes32(self, transaction_id), 0)
        .call()
    )
    latest_decision = lifecycle[2]
    decision_active = lifecycle[3]
    return int(latest_decision[1]) if decision_active else None


def _resolve_appeal_parameters(
    self: GenLayerClient,
    transaction_id: HexStr,
    expected_decision_id: Optional[int],
    value: Optional[int],
) -> tuple[int, int]:
    if expected_decision_id is not None and value is not None:
        return expected_decision_id, value

    try:
        quote = get_appeal_quote(self, transaction_id)
    except Exception as exc:
        raise GenLayerError(
            "Cannot quote an active appeal decision. The transaction may not be "
            "appealable yet; refresh its lifecycle and retry."
        ) from exc

    if (
        expected_decision_id is not None
        and expected_decision_id != quote["decision_id"]
    ):
        raise GenLayerError(
            f"Appeal decision {expected_decision_id} is stale; the latest active "
            f"decision is {quote['decision_id']}. Refresh and retry."
        )

    return (
        quote["decision_id"] if expected_decision_id is None else expected_decision_id,
        quote["total"] if value is None else value,
    )


def _is_studio_chain(self: GenLayerClient) -> bool:
    """Reports whether the client targets the studio-embedded consensus.

    localnet and studionet share chain id 61999, the same check
    ``transactions.actions.get_transaction`` uses to take its studio path.
    """
    return self.chain.id == localnet.id

def _to_bytes32(self: GenLayerClient, hex_str: HexStr) -> bytes:
    """Convert a hex string to bytes32."""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return self.w3.to_bytes(hexstr=hex_str)


def simulate_write_contract(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
    function_name: str,
    account: Optional[LocalAccount] = None,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    value: int = 0,
    leader_only: bool = False,
    fees: Optional[TransactionFeeOptions] = None,
    sim_config: Optional[SimConfig] = None,
    transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
) -> dict:
    if self.chain.id != localnet.id:
        raise GenLayerError("Client is not connected to the localnet")
    if account is None and self.local_account is None:
        raise GenLayerError("No account provided and no account is connected")
    sender_address = self.local_account.address if account is None else account.address
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        leader_only,
    ]
    serialized_data = serialize(data)
    request_params = {
        "type": "write",
        "to": address,
        "from": sender_address,
        "data": serialized_data,
        "transaction_hash_variant": transaction_hash_variant.value,
    }
    if value > 0:
        request_params["value"] = hex(value)
    rpc_fees = _transaction_fees_to_rpc(fees)
    if rpc_fees is not None:
        request_params["fees"] = rpc_fees
    if sim_config is not None:
        request_params["sim_config"] = sim_config
    receipt = self.provider.make_request(
        method="sim_call",
        params=[request_params],
    )["result"]
    return receipt


def _transaction_fees_to_rpc(
    fees: Optional[TransactionFeeOptions],
) -> Optional[dict]:
    if fees is None:
        return None
    normalized = normalize_transaction_fees(fees)
    rpc_fees = {
        "distribution": normalized["distribution"],
        "messageAllocations": normalized["message_allocations"],
    }
    if normalized["fee_value"] is not None:
        rpc_fees["feeValue"] = normalized["fee_value"]
    return _json_safe_rpc_value(rpc_fees)


def _json_safe_rpc_value(value):
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if isinstance(value, list):
        return [_json_safe_rpc_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_rpc_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe_rpc_value(item) for key, item in value.items()}
    return value


def _encode_submit_appeal_data(
    self: GenLayerClient,
    transaction_id: HexStr,
    expected_decision_id: Optional[int] = None,
):
    """Encode the decision-bound submitAppeal entrypoint."""
    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )
    contract_fn = consensus_main_contract.get_function_by_name("submitAppeal")
    if transaction_id.startswith("0x"):
        transaction_id = transaction_id[2:]
    if len(transaction_id) > 64:
        raise ValueError("transaction_id too long for bytes32")
    if expected_decision_id is None:
        raise ValueError("submitAppeal requires expected_decision_id")
    arguments = [self.w3.to_bytes(hexstr=transaction_id), expected_decision_id]
    params = abi_encode(contract_fn.argument_types, arguments)
    function_selector = eth_utils.keccak(text=contract_fn.signature)[:4].hex()
    encoded_data = "0x" + function_selector + params.hex()
    return encoded_data


FEE_MANAGEMENT_ARGUMENT_TYPES = ("bytes32", FEES_DISTRIBUTION_ABI_TYPE)
TOP_UP_AND_SUBMIT_APPEAL_ARGUMENT_TYPES = (
    "bytes32",
    "uint256",
    FEES_DISTRIBUTION_ABI_TYPE,
)


def _encode_fee_management_data(
    self: GenLayerClient,
    function_name: str,
    transaction_id: HexStr,
    distribution: FeesDistributionInput,
    expected_decision_id: Optional[int] = None,
):
    """Encode the chain's native fee-management entrypoint."""
    if function_name not in ("topUpFees", "topUpAndSubmitAppeal"):
        raise ValueError(f"Unsupported fee management function: {function_name}")

    tx_bytes = _to_bytes32(self, transaction_id)
    fees_distribution = create_fees_distribution(distribution)
    fees_tuple = fees_distribution_to_abi_tuple(fees_distribution)
    if function_name == "topUpAndSubmitAppeal":
        if expected_decision_id is None:
            raise ValueError("topUpAndSubmitAppeal requires expected_decision_id")
        argument_types = TOP_UP_AND_SUBMIT_APPEAL_ARGUMENT_TYPES
        arguments = [tx_bytes, expected_decision_id, fees_tuple]
        signature = f"{function_name}(bytes32,uint256,{FEES_DISTRIBUTION_ABI_TYPE})"
    else:
        argument_types = FEE_MANAGEMENT_ARGUMENT_TYPES
        arguments = [tx_bytes, fees_tuple]
        signature = f"{function_name}(bytes32,{FEES_DISTRIBUTION_ABI_TYPE})"

    params = abi_encode(argument_types, arguments)
    function_selector = eth_utils.keccak(text=signature)[:4].hex()
    return "0x" + function_selector + params.hex()


FEE_MANAGER_CALCULATE_ROUND_FEES_ABI = [
    {
        "type": "function",
        "name": "GENPerTimeUnit",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "storageUnitPrice",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "quoteGasPrice",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "messageFeeParamsBudgetFloor",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "calculateRoundFees",
        "stateMutability": "view",
        "inputs": [
            {
                "name": "_feesDistribution",
                "type": "tuple",
                "components": [
                    {"name": "leaderTimeunitsAllocation", "type": "uint256"},
                    {"name": "validatorTimeunitsAllocation", "type": "uint256"},
                    {"name": "appealRounds", "type": "uint256"},
                    {"name": "executionBudgetPerRound", "type": "uint256"},
                    {"name": "executionConsumed", "type": "uint256"},
                    {"name": "totalMessageFees", "type": "uint256"},
                    {"name": "rotations", "type": "uint256[]"},
                    {"name": "maxPriceGenPerTimeUnit", "type": "uint256"},
                    {"name": "storageFeeMaxGasPrice", "type": "uint256"},
                    {"name": "receiptFeeMaxGasPrice", "type": "uint256"},
                ],
            },
            {"name": "_numOfValidators", "type": "uint256"},
            {"name": "round", "type": "uint256"},
        ],
        "outputs": [{"name": "totalFeesToPay", "type": "uint256"}],
    },
]


def _get_add_transaction_abi_version(abi: Optional[list]) -> str:
    if not abi:
        return "v5"

    for entry in abi:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "function" or entry.get("name") != "addTransaction":
            continue

        inputs = entry.get("inputs", [])
        if len(inputs) == 1 and inputs[0].get("type") == "tuple":
            return "fees"
        if len(inputs) >= 6:
            return "v6"
        return "v5"

    return "v5"


def _get_default_valid_until() -> int:
    return int(time.time()) + 3600


def get_current_fee_policy(self: GenLayerClient) -> FeePolicyQuote:
    if self.chain.fee_manager_contract and self.chain.fee_manager_contract.get(
        "address"
    ):
        fee_manager_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(
                self.chain.fee_manager_contract["address"]
            ),
            abi=FEE_MANAGER_CALCULATE_ROUND_FEES_ABI,
        )
        gen_per_time_unit = fee_manager_contract.functions.GENPerTimeUnit().call()
        storage_unit_price = fee_manager_contract.functions.storageUnitPrice().call()
        quoted_receipt_gas_price = fee_manager_contract.functions.quoteGasPrice().call()
        execution_budget_floor = (
            fee_manager_contract.functions.messageFeeParamsBudgetFloor().call()
        )
        enabled = (
            gen_per_time_unit > 0
            or storage_unit_price > 0
            or quoted_receipt_gas_price > 0
        )
        network_receipt_gas_price = self.w3.eth.gas_price if enabled else 0
        receipt_gas_price = max(quoted_receipt_gas_price, network_receipt_gas_price)
        if enabled and receipt_gas_price == 0:
            raise GenLayerError(
                "receipt gas price quoted as zero; refusing to build a zero price cap"
            )
        local_execution_budget_floor = receipt_gas_price * (
            DEFAULT_FIXED_PROPOSE_RECEIPT_GAS
            + DEFAULT_INTRINSIC_GAS
            + DEFAULT_BOOTLOADER_OVERHEAD
            + (MIN_RECEIPT_BYTES * DEFAULT_CALLDATA_GAS_PER_BYTE)
            + (DEFAULT_RECEIPT_SLOTS_CHANGED * DEFAULT_GAS_PER_CHANGED_SLOT)
        )
        return {
            "enabled": enabled,
            "genPerTimeUnit": gen_per_time_unit,
            "storageUnitPrice": storage_unit_price,
            "receiptGasPrice": receipt_gas_price,
            "executionBudgetFloor": max(
                execution_budget_floor,
                local_execution_budget_floor,
            ),
            # Live networks quote through FeeManager.calculateRoundFees; this
            # field is only consumed by Studio's local mirror.
            "timeUnitOverlayBps": 0,
        }

    try:
        response = self.provider.make_request(
            method="sim_getFeeConfig",
            params=[],
        )
        return extract_studio_fee_policy(response["result"])
    except Exception as exc:
        raise GenLayerError(
            "Fee policy estimation is not supported on this chain "
            "(missing fee_manager_contract and sim_getFeeConfig)."
        ) from exc


def estimate_fees_distribution(
    self: GenLayerClient,
    options: Optional[FeeEstimateOptions] = None,
) -> FeesDistribution:
    policy = get_current_fee_policy(self)
    return build_estimated_fees_distribution(
        options,
        policy,
        self.chain.default_consensus_max_rotations,
    )


def estimate_transaction_fees(
    self: GenLayerClient,
    options: Optional[FeeEstimateOptions] = None,
) -> TransactionFeeEstimate:
    policy = get_current_fee_policy(self)
    return _estimate_transaction_fees_with_policy(self, options, policy)


def _estimate_transaction_fees_with_policy(
    self: GenLayerClient,
    options: Optional[FeeEstimateOptions],
    policy: FeePolicyQuote,
) -> TransactionFeeEstimate:
    distribution = build_estimated_fees_distribution(
        options,
        policy,
        self.chain.default_consensus_max_rotations,
    )

    if self.chain.fee_manager_contract and self.chain.fee_manager_contract.get(
        "address"
    ):
        fee_manager_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(
                self.chain.fee_manager_contract["address"]
            ),
            abi=FEE_MANAGER_CALCULATE_ROUND_FEES_ABI,
        )
        round_fees = fee_manager_contract.functions.calculateRoundFees(
            fees_distribution_to_abi_tuple(distribution),
            self.chain.default_number_of_initial_validators,
            0,
        ).call()
        fee_value = round_fees + distribution["totalMessageFees"]
    else:
        fee_value = (
            calculate_local_round_fees(
                distribution,
                self.chain.default_number_of_initial_validators,
                policy,
            )
            + distribution["totalMessageFees"]
        )

    estimate: TransactionFeeEstimate = {
        "distribution": distribution,
        "feeValue": fee_value,
        "fee_value": fee_value,
        "policy": policy,
    }
    message_allocations = None
    if options:
        message_allocations = options.get(
            "messageAllocations",
            options.get("message_allocations"),
        )
    if message_allocations is not None:
        estimate["messageAllocations"] = message_allocations
        estimate["message_allocations"] = message_allocations
    return estimate


def estimate_transaction_fees_from_simulation(
    self: GenLayerClient,
    options: SimulationFeeEstimateOptions,
) -> TransactionFeeEstimate:
    policy = get_current_fee_policy(self)
    preset = build_estimated_fees_options_from_simulation(options, policy)
    estimate = _estimate_transaction_fees_with_policy(
        self,
        preset["estimateOptions"],
        policy,
    )
    estimate["observed"] = preset["observed"]
    message_allocations = preset.get("messageAllocations")
    if message_allocations is not None:
        estimate["messageAllocations"] = message_allocations
        estimate["message_allocations"] = message_allocations
    return estimate


def estimate_transaction_fees_for_write(
    self: GenLayerClient,
    address: Union[Address, ChecksumAddress],
    function_name: str,
    account: Optional[LocalAccount] = None,
    args: Optional[List[CalldataEncodable]] = None,
    kwargs: Optional[Dict[str, CalldataEncodable]] = None,
    value: int = 0,
    leader_only: bool = False,
    options: Optional[FeeEstimateOptions] = None,
    sim_config: Optional[SimConfig] = None,
    transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
) -> TransactionFeeEstimate:
    if self.chain.id != localnet.id:
        raise GenLayerError("Target write fee estimation is only supported on localnet")
    if account is None and self.local_account is None:
        raise GenLayerError("No account provided and no account is connected")

    policy = get_current_fee_policy(self)
    initial_estimate = _estimate_transaction_fees_with_policy(self, options, policy)
    initial_fees: TransactionFeeOptions = {
        "distribution": initial_estimate["distribution"],
        "feeValue": initial_estimate["feeValue"],
    }
    message_allocations = initial_estimate.get("messageAllocations")
    if message_allocations is not None:
        initial_fees["messageAllocations"] = message_allocations

    sender_address = self.local_account.address if account is None else account.address
    data = [
        calldata.encode(
            make_calldata_object(method=function_name, args=args, kwargs=kwargs)
        ),
        leader_only,
    ]
    request_params = {
        "type": "write",
        "to": address,
        "from": sender_address,
        "data": serialize(data),
        "transaction_hash_variant": transaction_hash_variant.value,
        "fees": _transaction_fees_to_rpc(initial_fees),
    }
    if value > 0:
        request_params["value"] = hex(value)
    if sim_config is not None:
        request_params["sim_config"] = sim_config

    estimate_result = self.provider.make_request(
        method="sim_estimateTransactionFees",
        params=[request_params],
    )["result"]
    authoritative_estimate = transaction_fee_estimate_from_studio_estimate(
        estimate_result,
        policy,
    )
    if authoritative_estimate is not None:
        return authoritative_estimate

    simulation = self.provider.make_request(
        method="sim_call",
        params=[request_params],
    )["result"]
    simulation_options: SimulationFeeEstimateOptions = dict(options or {})
    simulation_options["simulation"] = simulation
    return estimate_transaction_fees_from_simulation(
        self,
        simulation_options,
    )


def _resolve_transaction_fees(
    self: GenLayerClient,
    fees: Optional[TransactionFeeOptions],
    num_of_initial_validators: int,
) -> NormalizedTransactionFees:
    transaction_fees = normalize_transaction_fees(fees)
    if transaction_fees[
        "fee_value"
    ] is not None or not requires_fee_deposit_calculation(
        transaction_fees["distribution"]
    ):
        transaction_fees["fee_value"] = transaction_fees["fee_value"] or 0
        return transaction_fees

    if not self.chain.fee_manager_contract or not self.chain.fee_manager_contract.get(
        "address"
    ):
        try:
            policy = get_current_fee_policy(self)
        except GenLayerError as exc:
            raise GenLayerError(
                "fees.feeValue is required when the chain does not expose a fee_manager_contract."
            ) from exc
        transaction_fees["fee_value"] = (
            calculate_local_round_fees(
                transaction_fees["distribution"],
                num_of_initial_validators,
                policy,
            )
            + transaction_fees["distribution"]["totalMessageFees"]
            if policy["enabled"]
            else 0
        )
        return transaction_fees

    fee_manager_contract = self.w3.eth.contract(
        address=self.w3.to_checksum_address(self.chain.fee_manager_contract["address"]),
        abi=FEE_MANAGER_CALCULATE_ROUND_FEES_ABI,
    )
    round_fees = fee_manager_contract.functions.calculateRoundFees(
        fees_distribution_to_abi_tuple(transaction_fees["distribution"]),
        num_of_initial_validators,
        0,
    ).call()
    transaction_fees["fee_value"] = (
        round_fees + transaction_fees["distribution"]["totalMessageFees"]
    )
    return transaction_fees


def _encode_add_transaction_data(
    self: GenLayerClient,
    sender_account,
    recipient,
    consensus_max_rotations,
    data,
    valid_until: Optional[int] = None,
    user_value: int = 0,
    transaction_fees: Optional[NormalizedTransactionFees] = None,
):
    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )
    contract_fn = consensus_main_contract.get_function_by_name("addTransaction")
    abi_version = _get_add_transaction_abi_version(
        self.chain.consensus_main_contract["abi"]
    )
    transaction_fees = transaction_fees or normalize_transaction_fees()
    use_fee_aware_transaction = (
        transaction_fees["requires_fee_aware_transaction"] or abi_version == "fees"
    )
    normalized_valid_until = to_uint(
        valid_until,
        "valid_until",
        _get_default_valid_until() if use_fee_aware_transaction else 0,
    )

    if use_fee_aware_transaction:
        return encode_fee_aware_add_transaction_data(
            sender_address=sender_account.address,
            recipient_address=recipient,
            num_of_initial_validators=self.chain.default_number_of_initial_validators,
            max_rotations=consensus_max_rotations,
            tx_data=data,
            valid_until=normalized_valid_until,
            user_value=user_value,
            transaction_fees=transaction_fees,
        )

    add_transaction_args = [
        sender_account.address,
        recipient,
        self.chain.default_number_of_initial_validators,
        consensus_max_rotations,
        self.w3.to_bytes(hexstr=data),
    ]
    if len(contract_fn.argument_types) >= 6:
        add_transaction_args.append(normalized_valid_until)

    params = abi_encode(
        contract_fn.argument_types,
        add_transaction_args,
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


KNOWN_REVERT_SELECTOR_NAMES = {
    "0x8d53e553": "InsufficientFees",
    "0xb4132db3": "MaxPriceExceeded",
    "0x57df8523": "ExecutionBudgetExceeded",
    "0x305e533c": "BudgetTooLow",
    "0xa70732ee": "RollupBudgetBelowFloor",
    "0x632be5a1": "FeeValueMustBeNonZero",
}


def _format_rpc_error(error: Exception) -> str:
    parts = [str(error)]
    for attr in ("message", "data"):
        value = getattr(error, attr, None)
        if isinstance(value, str) and value.strip():
            parts.append(value)
    args = getattr(error, "args", ())
    for arg in args:
        if isinstance(arg, dict):
            for key in ("message", "data", "details", "shortMessage"):
                value = arg.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value)
        elif isinstance(arg, str) and arg.strip():
            parts.append(arg)

    text = " ".join(dict.fromkeys(parts))
    selector_name = next(
        (
            name
            for selector, name in KNOWN_REVERT_SELECTOR_NAMES.items()
            if selector in text
        ),
        None,
    )
    if selector_name and selector_name not in text:
        return f"{text} ({selector_name})"
    return text


def _send_consensus_call(
    self: GenLayerClient,
    encoded_data: HexStr,
    sender_account: Optional[LocalAccount] = None,
    value: int = 0,
    operation_name: str = "Consensus call",
) -> HexStr:
    if sender_account is None:
        raise GenLayerError(
            "No account set. Configure the client with an account or pass an account to this function."
        )
    if self.chain.consensus_main_contract is None:
        raise GenLayerError("Consensus main contract not configured.")

    try:
        transaction = _prepare_transaction(
            self=self,
            sender=sender_account.address,
            recipient=self.chain.consensus_main_contract["address"],
            data=encoded_data,
            value=value,
        )
        signed_transaction = sender_account.sign_transaction(transaction)
        serialized_transaction = self.w3.to_hex(signed_transaction.raw_transaction)
        tx_hash = self.provider.make_request(
            method="eth_sendRawTransaction", params=[serialized_transaction]
        )["result"]
    except Exception as exc:
        raise GenLayerError(
            f"{operation_name} failed: {_format_rpc_error(exc)}"
        ) from exc
    if self.chain.id == localnet.id:
        return tx_hash

    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt.status != 1:
        raise GenLayerError(f"{operation_name} reverted: EVM tx {tx_hash}")

    return tx_hash


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
            f'Consensus main contract address not found in chain config for "{self.chain.name}".',
        )

    try:
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
    except Exception as exc:
        raise GenLayerError(f"Transaction failed: {_format_rpc_error(exc)}") from exc
    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt.status != 1:
        raise GenLayerError(
            f"Transaction reverted: EVM tx {tx_hash} to consensus contract "
            f"{self.chain.consensus_main_contract['address']} was reverted."
        )

    consensus_main_contract = self.w3.eth.contract(
        abi=self.chain.consensus_main_contract["abi"]
    )

    # Check for NewTransaction (immediately activated) or CreatedTransaction (queued)
    new_tx_event = consensus_main_contract.get_event_by_name("NewTransaction")
    new_tx_events = new_tx_event.process_receipt(tx_receipt, DISCARD)
    if len(new_tx_events) > 0:
        return self.w3.to_hex(new_tx_events[0]["args"]["txId"])

    created_tx_event = consensus_main_contract.get_event_by_name("CreatedTransaction")
    created_tx_events = created_tx_event.process_receipt(tx_receipt, DISCARD)
    if len(created_tx_events) > 0:
        return self.w3.to_hex(created_tx_events[0]["args"]["txId"])

    raise GenLayerError(
        f"Transaction not processed by consensus: EVM tx {tx_hash} succeeded but no "
        f"NewTransaction or CreatedTransaction event was found in the receipt logs."
    )
