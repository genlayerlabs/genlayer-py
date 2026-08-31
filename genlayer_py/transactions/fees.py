from __future__ import annotations

from enum import IntEnum
from typing import Any, Optional, TypedDict, Union

from eth_abi import encode as abi_encode
from eth_typing import HexStr
from eth_utils.crypto import keccak
from web3 import Web3


BigNumberish = Union[int, str]


class MessageType(IntEnum):
    External = 0
    Internal = 1


class FeesDistributionInput(TypedDict, total=False):
    leaderTimeunitsAllocation: BigNumberish
    leader_time_units_allocation: BigNumberish
    validatorTimeunitsAllocation: BigNumberish
    validator_time_units_allocation: BigNumberish
    appealRounds: BigNumberish
    appeal_rounds: BigNumberish
    executionBudgetPerRound: BigNumberish
    execution_budget_per_round: BigNumberish
    executionConsumed: BigNumberish
    execution_consumed: BigNumberish
    totalMessageFees: BigNumberish
    total_message_fees: BigNumberish
    rotations: list[BigNumberish]
    maxPriceGenPerTimeUnit: BigNumberish
    max_price_gen_per_time_unit: BigNumberish
    storageFeeMaxGasPrice: BigNumberish
    storage_fee_max_gas_price: BigNumberish
    receiptFeeMaxGasPrice: BigNumberish
    receipt_fee_max_gas_price: BigNumberish


class FeesDistribution(TypedDict):
    leaderTimeunitsAllocation: int
    validatorTimeunitsAllocation: int
    appealRounds: int
    executionBudgetPerRound: int
    executionConsumed: int
    totalMessageFees: int
    rotations: list[int]
    maxPriceGenPerTimeUnit: int
    storageFeeMaxGasPrice: int
    receiptFeeMaxGasPrice: int


class InternalMessageFeeParamsInput(TypedDict, total=False):
    leaderTimeunitsAllocation: BigNumberish
    leader_time_units_allocation: BigNumberish
    validatorTimeunitsAllocation: BigNumberish
    validator_time_units_allocation: BigNumberish
    appealRounds: BigNumberish
    appeal_rounds: BigNumberish
    executionBudgetPerRound: BigNumberish
    execution_budget_per_round: BigNumberish
    rotations: list[BigNumberish]


class ExternalMessageFeeParamsInput(TypedDict, total=False):
    gasLimit: BigNumberish
    gas_limit: BigNumberish
    maxGasPrice: BigNumberish
    max_gas_price: BigNumberish


class MessageFeeAllocationInput(TypedDict, total=False):
    messageType: Union[MessageType, int, str]
    message_type: Union[MessageType, int, str]
    onAcceptance: bool
    on_acceptance: bool
    parentIndex: BigNumberish
    parent_index: BigNumberish
    recipient: str
    callKey: Union[str, bytes]
    call_key: Union[str, bytes]
    budget: BigNumberish
    feeParams: Union[str, bytes]
    fee_params: Union[str, bytes]


class MessageFeeAllocationNode(TypedDict):
    messageType: int
    onAcceptance: bool
    parentIndex: int
    recipient: str
    callKey: bytes
    budget: int
    feeParams: bytes


class TransactionFeeOptions(TypedDict, total=False):
    distribution: FeesDistributionInput
    messageAllocations: list[MessageFeeAllocationInput]
    message_allocations: list[MessageFeeAllocationInput]
    feeValue: BigNumberish
    fee_value: BigNumberish


class FeePolicyQuote(TypedDict):
    enabled: bool
    genPerTimeUnit: int
    storageUnitPrice: int
    receiptGasPrice: int
    executionBudgetFloor: int


class FeeEstimateOptions(FeesDistributionInput, total=False):
    priceCapHeadroomBps: BigNumberish
    price_cap_headroom_bps: BigNumberish
    messageAllocations: list[MessageFeeAllocationInput]
    message_allocations: list[MessageFeeAllocationInput]
    executionHeadroomBps: BigNumberish
    execution_headroom_bps: BigNumberish
    messageHeadroomBps: BigNumberish
    message_headroom_bps: BigNumberish


class TransactionFeeEstimate(TypedDict, total=False):
    distribution: FeesDistribution
    messageAllocations: list[MessageFeeAllocationInput]
    message_allocations: list[MessageFeeAllocationInput]
    feeValue: int
    fee_value: int
    policy: FeePolicyQuote
    observed: dict[str, int]
    simulation: Any


class SimulationFeeEstimateOptions(FeeEstimateOptions, total=False):
    simulation: Any


class SimulationFeePreset(TypedDict, total=False):
    estimateOptions: FeeEstimateOptions
    estimate_options: FeeEstimateOptions
    observed: dict[str, int]
    messageAllocations: list[MessageFeeAllocationInput]
    message_allocations: list[MessageFeeAllocationInput]


class NormalizedTransactionFees(TypedDict):
    distribution: FeesDistribution
    message_allocations: list[MessageFeeAllocationNode]
    fee_value: Optional[int]
    requires_fee_aware_transaction: bool


MESSAGE_ALLOCATION_ROOT_PARENT_INDEX = (1 << 256) - 1
# Wildcard sentinel = keccak256 of empty bytes, untagged. Reserved: it can never be a
# derived key — short names (<32B) are left-aligned with a zero tail byte, long names
# get the low bit forced to 1, and this hash has neither.
CALL_KEY_WILDCARD = bytes.fromhex(
    "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
)
# Empty method name derives bytes32(0); GenVM emits it for deploy and emit_transfer.
CALL_KEY_UNNAMED = HexStr("0x" + ("0" * 64))
DEPLOY_CALL_KEY = CALL_KEY_UNNAMED
CALL_KEY_DEPLOY = DEPLOY_CALL_KEY

FEES_DISTRIBUTION_ABI_TYPE = (
    "(uint256,uint256,uint256,uint256,uint256,uint256,uint256[],uint256,uint256,uint256)"
)
MESSAGE_FEE_ALLOCATION_ABI_TYPE = "(uint8,bool,uint256,address,bytes32,uint256,bytes)"
ADD_TRANSACTION_PARAMS_ABI_TYPE = (
    f"(address,address,uint256,uint256,uint256,uint256,uint256,"
    f"{FEES_DISTRIBUTION_ABI_TYPE},bytes,{MESSAGE_FEE_ALLOCATION_ABI_TYPE}[])"
)
ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES = (ADD_TRANSACTION_PARAMS_ABI_TYPE,)
ADD_TRANSACTION_WITH_FEES_SIGNATURE = f"addTransaction({ADD_TRANSACTION_PARAMS_ABI_TYPE})"
DEPLOY_SALTED_WITH_FEES_SIGNATURE = f"deploySalted({ADD_TRANSACTION_PARAMS_ABI_TYPE})"
ADD_TRANSACTION_WITH_FEES_SELECTOR = keccak(
    text=ADD_TRANSACTION_WITH_FEES_SIGNATURE
)[:4].hex()
DEPLOY_SALTED_WITH_FEES_SELECTOR = keccak(
    text=DEPLOY_SALTED_WITH_FEES_SIGNATURE
)[:4].hex()


DEFAULT_FEES_DISTRIBUTION: FeesDistribution = {
    "leaderTimeunitsAllocation": 0,
    "validatorTimeunitsAllocation": 0,
    "appealRounds": 0,
    "executionBudgetPerRound": 0,
    "executionConsumed": 0,
    "totalMessageFees": 0,
    "rotations": [0],
    "maxPriceGenPerTimeUnit": 0,
    "storageFeeMaxGasPrice": 0,
    "receiptFeeMaxGasPrice": 0,
}

DEFAULT_PRICE_CAP_HEADROOM_BPS = 12_000
DEFAULT_LEADER_TIMEUNITS_ALLOCATION = 100
DEFAULT_VALIDATOR_TIMEUNITS_ALLOCATION = 200
DEFAULT_TRANSACTION_EXECUTION_BUDGET_PER_ROUND = 500_000
# Provisional heuristic sized ~20x observed dev-env consumption (~5M gas-equivalent).
# TODO(data): replace with telemetry-derived default (p99 x margin) once fee consumption telemetry is collected.
DEFAULT_TRANSACTION_EXECUTION_GAS = 100_000_000
DEFAULT_PARENT_MESSAGE_RECEIPT_HEADROOM = 10_000
MIN_RECEIPT_BYTES = 512
DEFAULT_RECEIPT_SLOTS_CHANGED = 7
DEFAULT_INTRINSIC_GAS = 21_000
DEFAULT_BOOTLOADER_OVERHEAD = 60_000
DEFAULT_FIXED_PROPOSE_RECEIPT_GAS = 210_000
DEFAULT_FIXED_MESSAGE_REVEAL_GAS = 100_000
DEFAULT_GAS_PER_CHANGED_SLOT = 1_000
DEFAULT_CALLDATA_GAS_PER_BYTE = 16
DEFAULT_MESSAGE_REVEAL_LENGTH_SLOTS = 32
DEFAULT_NONDET_OUTPUT_LENGTH_BYTES = 32
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

VALIDATORS_PER_ROUND = [
    5,
    7,
    11,
    13,
    23,
    25,
    47,
    49,
    95,
    97,
    191,
    193,
    383,
    385,
    767,
    769,
    1535,
    1537,
]


def _get(mapping: Optional[dict], *names: str, default: Any = None) -> Any:
    if not mapping:
        return default
    for name in names:
        if name in mapping:
            return mapping[name]
    return default


def _dict_or_none(value: Any) -> Optional[dict]:
    return value if isinstance(value, dict) else None


def _hex_from_unknown(value: Any, field_name: str, default: str = "0x") -> str:
    if value is None:
        return default
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, bytearray):
        return "0x" + bytes(value).hex()
    if isinstance(value, str):
        return value if value.startswith("0x") else "0x" + value
    raise ValueError(f"{field_name} must be a 0x-prefixed hex string or bytes.")


def to_uint(value: Optional[BigNumberish], field_name: str, fallback: int = 0) -> int:
    if value is None:
        return fallback
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer.")
    normalized = int(value)
    if normalized < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero.")
    return normalized


def _normalize_hex_bytes(value: Union[str, bytes, bytearray], field_name: str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"{field_name} must be a 0x-prefixed hex string or bytes.")
    return Web3.to_bytes(hexstr=value)


def _normalize_bytes32(value: Union[str, bytes, bytearray], field_name: str) -> bytes:
    normalized = _normalize_hex_bytes(value, field_name)
    if len(normalized) != 32:
        raise ValueError(f"{field_name} must be exactly 32 bytes.")
    return normalized


def _bytes_to_padded_call_key(value: bytes) -> HexStr:
    if len(value) > 32:
        raise ValueError("call key source bytes must be 32 bytes or fewer.")
    return HexStr("0x" + value.hex().ljust(64, "0"))


def derive_internal_message_call_key(method_name: str = "") -> HexStr:
    method_bytes = method_name.encode("utf-8")
    if len(method_bytes) < 32:
        return _bytes_to_padded_call_key(method_bytes)

    hashed = bytearray(keccak(method_bytes))
    hashed[-1] |= 1
    return HexStr("0x" + bytes(hashed).hex())


def derive_external_message_call_key(
    selector_or_calldata: Union[str, bytes, bytearray, None] = "0x",
) -> HexStr:
    calldata = _normalize_hex_bytes(
        selector_or_calldata if selector_or_calldata is not None else "0x",
        "selector_or_calldata",
    )
    if len(calldata) < 4:
        return CALL_KEY_UNNAMED
    return _bytes_to_padded_call_key(calldata[:4])


def deploy_call_key() -> HexStr:
    return DEPLOY_CALL_KEY


def _normalize_message_type(value: Union[MessageType, int, str]) -> int:
    if isinstance(value, MessageType):
        return int(value)
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "external":
            return int(MessageType.External)
        if lowered == "internal":
            return int(MessageType.Internal)
    normalized = int(value)
    if normalized not in (int(MessageType.External), int(MessageType.Internal)):
        raise ValueError("messageType must be External/Internal or 0/1.")
    return normalized


def _normalize_rotations(
    rotations: Optional[list[BigNumberish]],
    appeal_rounds: int,
    field_name: str,
) -> list[int]:
    expected_length = appeal_rounds + 1
    if rotations is None:
        return [0 for _ in range(expected_length)]
    normalized = [
        to_uint(rotation, f"{field_name}[{index}]")
        for index, rotation in enumerate(rotations)
    ]
    if len(normalized) != expected_length:
        raise ValueError(f"{field_name} must contain appealRounds + 1 entries.")
    return normalized


def create_fees_distribution(
    fee_distribution: Optional[FeesDistributionInput] = None,
) -> FeesDistribution:
    appeal_rounds = to_uint(
        _get(fee_distribution, "appealRounds", "appeal_rounds"),
        "fees.distribution.appealRounds",
    )
    return {
        "leaderTimeunitsAllocation": to_uint(
            _get(
                fee_distribution,
                "leaderTimeunitsAllocation",
                "leader_time_units_allocation",
            ),
            "fees.distribution.leaderTimeunitsAllocation",
        ),
        "validatorTimeunitsAllocation": to_uint(
            _get(
                fee_distribution,
                "validatorTimeunitsAllocation",
                "validator_time_units_allocation",
            ),
            "fees.distribution.validatorTimeunitsAllocation",
        ),
        "appealRounds": appeal_rounds,
        "executionBudgetPerRound": to_uint(
            _get(
                fee_distribution,
                "executionBudgetPerRound",
                "execution_budget_per_round",
            ),
            "fees.distribution.executionBudgetPerRound",
        ),
        "executionConsumed": to_uint(
            _get(fee_distribution, "executionConsumed", "execution_consumed"),
            "fees.distribution.executionConsumed",
        ),
        "totalMessageFees": to_uint(
            _get(fee_distribution, "totalMessageFees", "total_message_fees"),
            "fees.distribution.totalMessageFees",
        ),
        "rotations": _normalize_rotations(
            _get(fee_distribution, "rotations"),
            appeal_rounds,
            "fees.distribution.rotations",
        ),
        "maxPriceGenPerTimeUnit": to_uint(
            _get(
                fee_distribution,
                "maxPriceGenPerTimeUnit",
                "max_price_gen_per_time_unit",
            ),
            "fees.distribution.maxPriceGenPerTimeUnit",
        ),
        "storageFeeMaxGasPrice": to_uint(
            _get(
                fee_distribution,
                "storageFeeMaxGasPrice",
                "storage_fee_max_gas_price",
            ),
            "fees.distribution.storageFeeMaxGasPrice",
        ),
        "receiptFeeMaxGasPrice": to_uint(
            _get(
                fee_distribution,
                "receiptFeeMaxGasPrice",
                "receipt_fee_max_gas_price",
            ),
            "fees.distribution.receiptFeeMaxGasPrice",
        ),
    }


def encode_internal_message_fee_params(
    params: Optional[InternalMessageFeeParamsInput] = None,
) -> HexStr:
    appeal_rounds = to_uint(
        _get(params, "appealRounds", "appeal_rounds"),
        "internalMessageFeeParams.appealRounds",
    )
    encoded = abi_encode(
        ("(uint256,uint256,uint256,uint256,uint256[])",),
        (
            (
                to_uint(
                    _get(
                        params,
                        "leaderTimeunitsAllocation",
                        "leader_time_units_allocation",
                    ),
                    "internalMessageFeeParams.leaderTimeunitsAllocation",
                ),
                to_uint(
                    _get(
                        params,
                        "validatorTimeunitsAllocation",
                        "validator_time_units_allocation",
                    ),
                    "internalMessageFeeParams.validatorTimeunitsAllocation",
                ),
                appeal_rounds,
                to_uint(
                    _get(
                        params,
                        "executionBudgetPerRound",
                        "execution_budget_per_round",
                    ),
                    "internalMessageFeeParams.executionBudgetPerRound",
                ),
                _normalize_rotations(
                    _get(params, "rotations"),
                    appeal_rounds,
                    "internalMessageFeeParams.rotations",
                ),
            ),
        ),
    )
    return HexStr("0x" + encoded.hex())


def encode_external_message_fee_params(
    params: Optional[ExternalMessageFeeParamsInput] = None,
) -> HexStr:
    encoded = abi_encode(
        ("(uint256,uint256)",),
        (
            (
                to_uint(
                    _get(params, "gasLimit", "gas_limit"),
                    "externalMessageFeeParams.gasLimit",
                ),
                to_uint(
                    _get(params, "maxGasPrice", "max_gas_price"),
                    "externalMessageFeeParams.maxGasPrice",
                ),
            ),
        ),
    )
    return HexStr("0x" + encoded.hex())


def normalize_message_fee_allocations(
    allocations: Optional[list[MessageFeeAllocationInput]] = None,
) -> list[MessageFeeAllocationNode]:
    normalized: list[MessageFeeAllocationNode] = []
    for index, allocation in enumerate(allocations or []):
        recipient = _get(allocation, "recipient")
        if not recipient:
            raise ValueError(f"fees.messageAllocations[{index}].recipient is required.")
        message_type = _normalize_message_type(
            _get(allocation, "messageType", "message_type", default=MessageType.External)
        )
        normalized.append(
            {
                "messageType": message_type,
                "onAcceptance": bool(
                    _get(
                        allocation,
                        "onAcceptance",
                        "on_acceptance",
                        default=message_type != int(MessageType.External),
                    )
                ),
                "parentIndex": to_uint(
                    _get(allocation, "parentIndex", "parent_index"),
                    f"fees.messageAllocations[{index}].parentIndex",
                    MESSAGE_ALLOCATION_ROOT_PARENT_INDEX,
                ),
                "recipient": recipient,
                "callKey": _normalize_bytes32(
                    _get(
                        allocation,
                        "callKey",
                        "call_key",
                        default=CALL_KEY_WILDCARD,
                    ),
                    f"fees.messageAllocations[{index}].callKey",
                ),
                "budget": to_uint(
                    _get(allocation, "budget"),
                    f"fees.messageAllocations[{index}].budget",
                ),
                "feeParams": _normalize_hex_bytes(
                    _get(allocation, "feeParams", "fee_params", default="0x"),
                    f"fees.messageAllocations[{index}].feeParams",
                ),
            }
        )
    return normalized


def fees_distribution_to_abi_tuple(distribution: FeesDistribution) -> tuple:
    return (
        distribution["leaderTimeunitsAllocation"],
        distribution["validatorTimeunitsAllocation"],
        distribution["appealRounds"],
        distribution["executionBudgetPerRound"],
        distribution["executionConsumed"],
        distribution["totalMessageFees"],
        distribution["rotations"],
        distribution["maxPriceGenPerTimeUnit"],
        distribution["storageFeeMaxGasPrice"],
        distribution["receiptFeeMaxGasPrice"],
    )


def message_allocation_to_abi_tuple(allocation: MessageFeeAllocationNode) -> tuple:
    return (
        allocation["messageType"],
        allocation["onAcceptance"],
        allocation["parentIndex"],
        allocation["recipient"],
        allocation["callKey"],
        allocation["budget"],
        allocation["feeParams"],
    )


def _has_non_default_fees_distribution(distribution: FeesDistribution) -> bool:
    return distribution != DEFAULT_FEES_DISTRIBUTION


def normalize_transaction_fees(
    fees: Optional[TransactionFeeOptions] = None,
) -> NormalizedTransactionFees:
    distribution = create_fees_distribution(_get(fees, "distribution"))
    message_allocations = normalize_message_fee_allocations(
        _get(fees, "messageAllocations", "message_allocations")
    )
    raw_fee_value = _get(fees, "feeValue", "fee_value")
    fee_value = (
        None
        if raw_fee_value is None
        else to_uint(raw_fee_value, "fees.feeValue")
    )

    return {
        "distribution": distribution,
        "message_allocations": message_allocations,
        "fee_value": fee_value,
        "requires_fee_aware_transaction": (
            _has_non_default_fees_distribution(distribution)
            or len(message_allocations) > 0
            or (fee_value or 0) != 0
        ),
    }


def requires_fee_deposit_calculation(distribution: FeesDistribution) -> bool:
    return (
        distribution["leaderTimeunitsAllocation"] != 0
        or distribution["validatorTimeunitsAllocation"] != 0
        or distribution["executionBudgetPerRound"] != 0
        or distribution["totalMessageFees"] != 0
    )


def _with_cap_headroom(value: int, headroom_bps: int) -> int:
    if value == 0:
        return 0
    return (value * headroom_bps + 9_999) // 10_000


def _int_from_unknown(value: Any, field_name: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError(f"{field_name} is not an integer value.")
    normalized = int(value)
    if normalized < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero.")
    return normalized


def extract_studio_fee_policy(config: Any) -> FeePolicyQuote:
    if not isinstance(config, dict):
        raise ValueError("sim_getFeeConfig did not return an object.")

    enabled = config.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        raise ValueError("sim_getFeeConfig enabled flag is not a boolean.")

    policy = config.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("sim_getFeeConfig did not expose a policy object.")

    gen_per_time_unit = _int_from_unknown(
        policy.get("genPerTimeUnit"),
        "policy.genPerTimeUnit",
    )
    storage_unit_price = _int_from_unknown(
        policy.get("storageUnitPrice"),
        "policy.storageUnitPrice",
    )
    receipt_gas_price = _int_from_unknown(
        policy.get("receiptGasPrice"),
        "policy.receiptGasPrice",
    )
    intrinsic_gas = _int_from_unknown(
        policy.get("intrinsicGas", DEFAULT_INTRINSIC_GAS),
        "policy.intrinsicGas",
    )
    bootloader_overhead = _int_from_unknown(
        policy.get("bootloaderOverhead", DEFAULT_BOOTLOADER_OVERHEAD),
        "policy.bootloaderOverhead",
    )
    gas_per_changed_slot = _int_from_unknown(
        policy.get("gasPerChangedSlot", DEFAULT_GAS_PER_CHANGED_SLOT),
        "policy.gasPerChangedSlot",
    )
    calldata_gas_per_byte = _int_from_unknown(
        policy.get("calldataGasPerByte", DEFAULT_CALLDATA_GAS_PER_BYTE),
        "policy.calldataGasPerByte",
    )
    fixed_propose_receipt_gas = _int_from_unknown(
        policy.get("fixedProposeReceiptGas", DEFAULT_FIXED_PROPOSE_RECEIPT_GAS),
        "policy.fixedProposeReceiptGas",
    )
    fixed_message_reveal_gas = _int_from_unknown(
        policy.get("fixedMessageRevealGas", DEFAULT_FIXED_MESSAGE_REVEAL_GAS),
        "policy.fixedMessageRevealGas",
    )
    explicit_budget_floor = policy.get(
        "messageFeeParamsBudgetFloor",
        config.get("messageFeeParamsBudgetFloor"),
    )
    execution_budget_floor = (
        _int_from_unknown(
            explicit_budget_floor,
            "policy.messageFeeParamsBudgetFloor",
        )
        if explicit_budget_floor is not None
        else receipt_gas_price
        * (
            fixed_propose_receipt_gas
            + intrinsic_gas
            + bootloader_overhead
            + (DEFAULT_RECEIPT_SLOTS_CHANGED * gas_per_changed_slot)
            + fixed_message_reveal_gas
            + intrinsic_gas
            + bootloader_overhead
            + (DEFAULT_MESSAGE_REVEAL_LENGTH_SLOTS * gas_per_changed_slot)
            + (DEFAULT_NONDET_OUTPUT_LENGTH_BYTES * calldata_gas_per_byte)
        )
    )

    return {
        "enabled": bool(
            enabled
            if enabled is not None
            else gen_per_time_unit > 0
            or storage_unit_price > 0
            or receipt_gas_price > 0
        ),
        "genPerTimeUnit": gen_per_time_unit,
        "storageUnitPrice": storage_unit_price,
        "receiptGasPrice": receipt_gas_price,
        "executionBudgetFloor": execution_budget_floor,
    }


def _default_execution_budget_per_round(policy: FeePolicyQuote) -> int:
    if (
        not policy["enabled"]
        or (
            policy["storageUnitPrice"] == 0
            and policy["receiptGasPrice"] == 0
        )
    ):
        return 0

    return max(
        DEFAULT_TRANSACTION_EXECUTION_BUDGET_PER_ROUND,
        policy["executionBudgetFloor"],
        policy["receiptGasPrice"] * DEFAULT_TRANSACTION_EXECUTION_GAS,
    )


def fee_accounting_from_simulation(simulation: Any) -> Optional[dict]:
    simulation_record = _dict_or_none(simulation)
    if not simulation_record:
        return None

    direct = _dict_or_none(
        _get(simulation_record, "feeAccounting", "fee_accounting")
    )
    if direct:
        return direct

    receipt = _dict_or_none(simulation_record.get("receipt")) or simulation_record
    genvm_result = _dict_or_none(
        _get(receipt, "genvm_result", "genvmResult")
    )
    if not genvm_result:
        return None

    return _dict_or_none(
        _get(genvm_result, "fee_accounting", "feeAccounting")
    )


def fee_report_from_simulation(simulation: Any, accounting: Optional[dict]) -> Optional[dict]:
    simulation_record = _dict_or_none(simulation)
    direct = _dict_or_none(
        _get(simulation_record, "feeReport", "fee_report") if simulation_record else None
    )
    if direct:
        return direct
    return _dict_or_none(
        _get(accounting, "execution_fee_report", "executionFeeReport")
    )


def message_allocations_from_accounting(
    accounting: Optional[dict],
) -> Optional[list[MessageFeeAllocationInput]]:
    raw_allocations = _get(accounting, "message_allocations", "messageAllocations")
    if raw_allocations is None:
        return None
    if not isinstance(raw_allocations, list):
        raise ValueError("simulation.feeAccounting.message_allocations must be a list.")

    allocations: list[MessageFeeAllocationInput] = []
    for index, allocation in enumerate(raw_allocations):
        allocation_record = _dict_or_none(allocation)
        if not allocation_record:
            raise ValueError(
                f"simulation.feeAccounting.message_allocations[{index}] must be an object."
            )
        allocations.append(
            {
                "messageType": _normalize_message_type(
                    _get(
                        allocation_record,
                        "messageType",
                        "message_type",
                        default=MessageType.External,
                    )
                ),
                "onAcceptance": bool(
                    _get(
                        allocation_record,
                        "onAcceptance",
                        "on_acceptance",
                    )
                ),
                "parentIndex": to_uint(
                    _get(
                        allocation_record,
                        "parentIndex",
                        "parent_index",
                    ),
                    f"simulation.feeAccounting.message_allocations[{index}].parentIndex",
                    MESSAGE_ALLOCATION_ROOT_PARENT_INDEX,
                ),
                "recipient": str(
                    _get(
                        allocation_record,
                        "recipient",
                        default=ZERO_ADDRESS,
                    )
                ),
                "callKey": _hex_from_unknown(
                    _get(
                        allocation_record,
                        "callKey",
                        "call_key",
                        default=CALL_KEY_WILDCARD,
                    ),
                    f"simulation.feeAccounting.message_allocations[{index}].callKey",
                    "0x" + CALL_KEY_WILDCARD.hex(),
                ),
                "budget": to_uint(
                    _get(allocation_record, "budget"),
                    f"simulation.feeAccounting.message_allocations[{index}].budget",
                ),
                "feeParams": _hex_from_unknown(
                    _get(
                        allocation_record,
                        "feeParams",
                        "fee_params",
                        default="0x",
                    ),
                    f"simulation.feeAccounting.message_allocations[{index}].feeParams",
                ),
            }
        )
    return allocations


def _message_is_internal(message: dict) -> bool:
    message_type = _get(message, "messageType", "message_type")
    if isinstance(message_type, str):
        return message_type.lower() == "internal" or message_type == "1"
    if message_type is None:
        return False
    return int(message_type) == int(MessageType.Internal)


def observed_simulation_fee_usage(
    options: SimulationFeeEstimateOptions,
    policy: FeePolicyQuote,
) -> dict[str, int]:
    simulation = options.get("simulation")
    accounting = fee_accounting_from_simulation(simulation) or {}
    report = fee_report_from_simulation(simulation, accounting) or {}
    execution_headroom_bps = to_uint(
        _get(options, "executionHeadroomBps", "execution_headroom_bps"),
        "executionHeadroomBps",
        DEFAULT_PRICE_CAP_HEADROOM_BPS,
    )
    message_headroom_bps = to_uint(
        _get(options, "messageHeadroomBps", "message_headroom_bps"),
        "messageHeadroomBps",
        DEFAULT_PRICE_CAP_HEADROOM_BPS,
    )

    execution_fee_consumed = _int_from_unknown(
        _get(accounting, "execution_fee_consumed", "executionFeeConsumed"),
        "simulation.feeAccounting.execution_fee_consumed",
    )
    execution_fee_report_total = _int_from_unknown(
        _get(report, "totalEstimatedFee", "total_estimated_fee"),
        "simulation.feeReport.totalEstimatedFee",
    )
    observed_execution_budget = execution_fee_consumed + execution_fee_report_total
    recommended_execution_budget = (
        max(
            policy["executionBudgetFloor"],
            _with_cap_headroom(observed_execution_budget, execution_headroom_bps),
        )
        if observed_execution_budget > 0
        else 0
    )

    message_fee_consumed = _int_from_unknown(
        _get(accounting, "message_fee_consumed", "messageFeeConsumed"),
        "simulation.feeAccounting.message_fee_consumed",
    )
    genvm_message_fee_consumed = _int_from_unknown(
        _get(accounting, "genvm_message_fee_consumed", "genvmMessageFeeConsumed"),
        "simulation.feeAccounting.genvm_message_fee_consumed",
    )
    message_fee_budget = _int_from_unknown(
        _get(accounting, "message_fee_budget", "messageFeeBudget"),
        "simulation.feeAccounting.message_fee_budget",
    )
    message_fee_refunded = _int_from_unknown(
        _get(accounting, "message_fee_refunded", "messageFeeRefunded"),
        "simulation.feeAccounting.message_fee_refunded",
    )
    external_message_reserved = _int_from_unknown(
        _get(accounting, "external_message_fee_reserved", "externalMessageReserved"),
        "simulation.feeAccounting.external_message_fee_reserved",
    )
    external_message_reimbursed = _int_from_unknown(
        _get(accounting, "external_message_fee_reimbursed", "externalMessageReimbursed"),
        "simulation.feeAccounting.external_message_fee_reimbursed",
    )
    external_message_remainder = _int_from_unknown(
        _get(accounting, "external_message_fee_remainder", "externalMessageRemainder"),
        "simulation.feeAccounting.external_message_fee_remainder",
    )

    message_reveal = _dict_or_none(
        _get(report, "messageReveal", "message_reveal")
    ) or {}
    messages = message_reveal.get("messages") or []
    internal_declared_budget = 0
    if isinstance(messages, list):
        for index, message in enumerate(messages):
            message_record = _dict_or_none(message)
            if message_record and _message_is_internal(message_record):
                internal_declared_budget += _int_from_unknown(
                    _get(
                        message_record,
                        "declaredBudget",
                        "declared_budget",
                    ),
                    f"simulation.feeReport.messageReveal.messages[{index}].declaredBudget",
                )

    observed_message_budget = max(
        message_fee_consumed,
        internal_declared_budget + external_message_reimbursed,
    )

    return {
        "executionFeeConsumed": execution_fee_consumed,
        "executionFeeReportTotal": execution_fee_report_total,
        "recommendedExecutionBudgetPerRound": recommended_execution_budget,
        "genvmMessageFeeConsumed": genvm_message_fee_consumed,
        "messageFeeBudget": message_fee_budget,
        "messageFeeConsumed": message_fee_consumed,
        "messageFeeRefunded": message_fee_refunded,
        "internalDeclaredBudget": internal_declared_budget,
        "externalMessageReserved": external_message_reserved,
        "externalMessageReimbursed": external_message_reimbursed,
        "externalMessageRemainder": external_message_remainder,
        "recommendedTotalMessageFees": (
            _with_cap_headroom(observed_message_budget, message_headroom_bps)
            if observed_message_budget > 0
            else 0
        ),
    }


def transaction_fee_estimate_from_studio_estimate(
    result: Any,
    policy: FeePolicyQuote,
) -> Optional[TransactionFeeEstimate]:
    estimate = _dict_or_none(result)
    if estimate is None:
        return None

    preset = _dict_or_none(_get(estimate, "recommendedPreset", "recommended_preset"))
    if preset is None:
        return None
    distribution_input = _dict_or_none(_get(preset, "distribution"))
    fee_value = _get(preset, "feeValue", "fee_value")
    if distribution_input is None or fee_value is None:
        return None

    accounting = _dict_or_none(_get(estimate, "feeAccounting", "fee_accounting"))
    fee_report = _dict_or_none(_get(estimate, "feeReport", "fee_report"))
    if fee_report is None and accounting is not None:
        fee_report = _dict_or_none(
            _get(accounting, "execution_fee_report", "executionFeeReport")
        )

    simulation = {
        "feeAccounting": accounting,
        "feeReport": fee_report,
    }
    transaction_estimate: TransactionFeeEstimate = {
        "distribution": create_fees_distribution(distribution_input),
        "feeValue": to_uint(fee_value, "recommendedPreset.feeValue"),
        "fee_value": to_uint(fee_value, "recommendedPreset.feeValue"),
        "policy": policy,
        "simulation": simulation,
        "observed": observed_simulation_fee_usage(
            {"simulation": simulation},
            policy,
        ),
    }

    message_allocations = _get(
        preset,
        "messageAllocations",
        "message_allocations",
    )
    if message_allocations is not None:
        normalized_allocations = message_allocations_from_accounting(
            {"message_allocations": message_allocations}
        )
        if normalized_allocations is not None:
            transaction_estimate["messageAllocations"] = normalized_allocations
            transaction_estimate["message_allocations"] = normalized_allocations

    return transaction_estimate


def build_estimated_fees_options_from_simulation(
    options: SimulationFeeEstimateOptions,
    policy: FeePolicyQuote,
) -> SimulationFeePreset:
    if not isinstance(options, dict) or "simulation" not in options:
        raise ValueError("simulation is required.")

    accounting = fee_accounting_from_simulation(options["simulation"])
    observed = observed_simulation_fee_usage(options, policy)
    message_allocations = _get(options, "messageAllocations", "message_allocations")
    if message_allocations is None:
        message_allocations = message_allocations_from_accounting(accounting)

    estimate_options: FeeEstimateOptions = {
        key: value
        for key, value in options.items()
        if key
        not in {
            "simulation",
            "executionHeadroomBps",
            "execution_headroom_bps",
            "messageHeadroomBps",
            "message_headroom_bps",
        }
    }
    if message_allocations is not None:
        estimate_options["messageAllocations"] = message_allocations
        estimate_options.pop("message_allocations", None)

    if (
        _get(
            estimate_options,
            "executionBudgetPerRound",
            "execution_budget_per_round",
        )
        is None
        and observed["recommendedExecutionBudgetPerRound"] > 0
    ):
        estimate_options["executionBudgetPerRound"] = observed[
            "recommendedExecutionBudgetPerRound"
        ]

    if (
        _get(estimate_options, "totalMessageFees", "total_message_fees") is None
        and message_allocations is None
        and observed["recommendedTotalMessageFees"] > 0
    ):
        estimate_options["totalMessageFees"] = observed["recommendedTotalMessageFees"]

    preset: SimulationFeePreset = {
        "estimateOptions": estimate_options,
        "estimate_options": estimate_options,
        "observed": observed,
    }
    if message_allocations is not None:
        preset["messageAllocations"] = message_allocations
        preset["message_allocations"] = message_allocations
    return preset


def build_estimated_fees_distribution(
    options: Optional[FeeEstimateOptions],
    policy: FeePolicyQuote,
    default_consensus_max_rotations: BigNumberish,
) -> FeesDistribution:
    headroom_bps = to_uint(
        _get(options, "priceCapHeadroomBps", "price_cap_headroom_bps"),
        "priceCapHeadroomBps",
        DEFAULT_PRICE_CAP_HEADROOM_BPS,
    )
    base_execution_budget_default = _default_execution_budget_per_round(policy)

    total_message_fees = _get(options, "totalMessageFees", "total_message_fees")
    message_allocations = _get(options, "messageAllocations", "message_allocations")
    normalized_message_allocations = (
        normalize_message_fee_allocations(message_allocations)
        if message_allocations is not None
        else None
    )
    if total_message_fees is None and message_allocations is not None:
        total_message_fees = sum(
            allocation["budget"]
            for allocation in normalized_message_allocations or []
            if allocation["messageType"] == int(MessageType.External)
            or allocation["parentIndex"] == MESSAGE_ALLOCATION_ROOT_PARENT_INDEX
        )
    emits_messages = (
        (
            normalized_message_allocations is not None
            and len(normalized_message_allocations) > 0
        )
        or (
            total_message_fees is not None
            and to_uint(total_message_fees, "totalMessageFees") > 0
        )
    )
    execution_budget_default = (
        base_execution_budget_default
        + policy["receiptGasPrice"] * DEFAULT_PARENT_MESSAGE_RECEIPT_HEADROOM
        if emits_messages
        else base_execution_budget_default
    )
    appeal_rounds = to_uint(
        _get(options, "appealRounds", "appeal_rounds"),
        "appealRounds",
    )
    rotations = _get(options, "rotations")
    if rotations is None:
        default_rotations = to_uint(
            default_consensus_max_rotations,
            "defaultConsensusMaxRotations",
        )
        rotations = [default_rotations] * (appeal_rounds + 1)

    return create_fees_distribution(
        {
            "leaderTimeunitsAllocation": _get(
                options,
                "leaderTimeunitsAllocation",
                "leader_time_units_allocation",
                default=DEFAULT_LEADER_TIMEUNITS_ALLOCATION
                if policy["enabled"]
                else 0,
            ),
            "validatorTimeunitsAllocation": _get(
                options,
                "validatorTimeunitsAllocation",
                "validator_time_units_allocation",
                default=DEFAULT_VALIDATOR_TIMEUNITS_ALLOCATION
                if policy["enabled"]
                else 0,
            ),
            "appealRounds": appeal_rounds,
            "executionBudgetPerRound": _get(
                options,
                "executionBudgetPerRound",
                "execution_budget_per_round",
                default=execution_budget_default,
            ),
            "executionConsumed": _get(
                options,
                "executionConsumed",
                "execution_consumed",
            ),
            "totalMessageFees": total_message_fees,
            "rotations": rotations,
            "maxPriceGenPerTimeUnit": _get(
                options,
                "maxPriceGenPerTimeUnit",
                "max_price_gen_per_time_unit",
                default=_with_cap_headroom(
                    policy["genPerTimeUnit"],
                    headroom_bps,
                ),
            ),
            "storageFeeMaxGasPrice": _get(
                options,
                "storageFeeMaxGasPrice",
                "storage_fee_max_gas_price",
                default=_with_cap_headroom(
                    policy["storageUnitPrice"],
                    headroom_bps,
                ),
            ),
            "receiptFeeMaxGasPrice": _get(
                options,
                "receiptFeeMaxGasPrice",
                "receipt_fee_max_gas_price",
                default=_with_cap_headroom(
                    policy["receiptGasPrice"],
                    headroom_bps,
                ),
            ),
        }
    )


def _validator_index(num_of_validators: int) -> int:
    for index, validators in enumerate(VALIDATORS_PER_ROUND):
        if validators == num_of_validators:
            return index
    raise ValueError("InvalidNumOfValidators")


def _calculate_fee_for_round(
    num_of_validators: int,
    rotations: int,
    leader_time_units_allocation: int,
    validator_time_units_allocation: int,
) -> int:
    return rotations * (
        leader_time_units_allocation
        + num_of_validators * validator_time_units_allocation
    )


def calculate_local_round_fees(
    distribution: FeesDistribution,
    num_of_initial_validators: int,
    policy: FeePolicyQuote,
) -> int:
    if distribution["appealRounds"] != len(distribution["rotations"]) - 1:
        raise ValueError("InvalidAppealRounds")
    if (
        distribution["maxPriceGenPerTimeUnit"] > 0
        and policy["genPerTimeUnit"] > distribution["maxPriceGenPerTimeUnit"]
    ):
        raise ValueError("MaxPriceExceeded")
    if (
        distribution["storageFeeMaxGasPrice"] > 0
        and policy["storageUnitPrice"] > distribution["storageFeeMaxGasPrice"]
    ):
        raise ValueError("MaxPriceExceeded")
    if (
        distribution["receiptFeeMaxGasPrice"] > 0
        and policy["receiptGasPrice"] > distribution["receiptFeeMaxGasPrice"]
    ):
        raise ValueError("MaxPriceExceeded")

    start_index = _validator_index(num_of_initial_validators)
    if start_index + distribution["appealRounds"] * 2 >= len(VALIDATORS_PER_ROUND):
        raise ValueError("InvalidNumOfValidators")

    total = _calculate_fee_for_round(
        VALIDATORS_PER_ROUND[start_index],
        distribution["rotations"][0] + 1,
        distribution["leaderTimeunitsAllocation"],
        distribution["validatorTimeunitsAllocation"],
    )
    rotations_index = 1
    rotations_this_round = 1
    for offset in range(1, distribution["appealRounds"] * 2 + 1):
        if offset % 2 == 0 and rotations_index < len(distribution["rotations"]):
            rotations_this_round = distribution["rotations"][rotations_index] + 1
            rotations_index += 1
        elif offset % 2 == 1:
            rotations_this_round = 1

        total += _calculate_fee_for_round(
            VALIDATORS_PER_ROUND[start_index + offset],
            rotations_this_round,
            distribution["leaderTimeunitsAllocation"],
            distribution["validatorTimeunitsAllocation"],
        )

    if policy["genPerTimeUnit"] > 0:
        total *= policy["genPerTimeUnit"]

    leader_rounds = sum(
        rotations + 1
        for rotations in distribution["rotations"]
    ) + distribution["appealRounds"]
    total += distribution["executionBudgetPerRound"] * leader_rounds
    return total


def build_add_transaction_params_tuple(
    *,
    sender_address: str,
    recipient_address: str,
    num_of_initial_validators: int,
    max_rotations: int,
    valid_until: int,
    salt_nonce: int,
    user_value: int,
    tx_data: Union[HexStr, str, bytes],
    transaction_fees: NormalizedTransactionFees,
) -> tuple:
    tx_calldata = (
        tx_data
        if isinstance(tx_data, bytes)
        else Web3.to_bytes(hexstr=tx_data)
    )
    return (
        sender_address,
        recipient_address,
        num_of_initial_validators,
        max_rotations,
        valid_until,
        salt_nonce,
        user_value,
        fees_distribution_to_abi_tuple(transaction_fees["distribution"]),
        tx_calldata,
        [
            message_allocation_to_abi_tuple(allocation)
            for allocation in transaction_fees["message_allocations"]
        ],
    )


def encode_fee_aware_add_transaction_data(
    *,
    sender_address: str,
    recipient_address: str,
    num_of_initial_validators: int,
    max_rotations: int,
    tx_data: Union[HexStr, str, bytes],
    valid_until: int,
    salt_nonce: int = 0,
    user_value: int = 0,
    transaction_fees: Optional[NormalizedTransactionFees] = None,
) -> HexStr:
    normalized_fees = transaction_fees or normalize_transaction_fees()
    params_tuple = build_add_transaction_params_tuple(
        sender_address=sender_address,
        recipient_address=recipient_address,
        num_of_initial_validators=num_of_initial_validators,
        max_rotations=max_rotations,
        valid_until=valid_until,
        salt_nonce=salt_nonce,
        user_value=user_value,
        tx_data=tx_data,
        transaction_fees=normalized_fees,
    )
    encoded = abi_encode(ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES, [params_tuple])
    return HexStr("0x" + ADD_TRANSACTION_WITH_FEES_SELECTOR + encoded.hex())


def decode_fees_distribution_tuple(values: tuple) -> FeesDistribution:
    return {
        "leaderTimeunitsAllocation": values[0],
        "validatorTimeunitsAllocation": values[1],
        "appealRounds": values[2],
        "executionBudgetPerRound": values[3],
        "executionConsumed": values[4],
        "totalMessageFees": values[5],
        "rotations": list(values[6]),
        "maxPriceGenPerTimeUnit": values[7],
        "storageFeeMaxGasPrice": values[8],
        "receiptFeeMaxGasPrice": values[9],
    }


def decode_message_allocation_tuple(values: tuple) -> MessageFeeAllocationNode:
    return {
        "messageType": values[0],
        "onAcceptance": values[1],
        "parentIndex": values[2],
        "recipient": values[3],
        "callKey": values[4],
        "budget": values[5],
        "feeParams": values[6],
    }
