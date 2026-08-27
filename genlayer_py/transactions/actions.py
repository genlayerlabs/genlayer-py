from __future__ import annotations

from genlayer_py.logging import logger
import json
from typing import Any, Dict, List, Literal, Optional
from web3 import Web3
from web3.types import _Hash32
from eth_typing import Address, HexStr
from web3.logs import DISCARD

from genlayer_py.config import transaction_config
from genlayer_py.types import (
    ExecutionResult,
    EXECUTION_RESULT_NUMBER_TO_NAME,
)
from genlayer_py.types.transactions import (
    PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME,
    RESOLUTION_ACTION_NUMBER_TO_NAME,
    RESOLUTION_SOURCE_NUMBER_TO_NAME,
    ProtocolTransactionLifecycle,
    ProtocolTransactionStatus,
    transaction_lifecycle_from_protocol_status,
    transaction_outcome_from_protocol_result,
)
from genlayer_py.consensus.abi import (
    ADDRESS_MANAGER_ABI,
    CONSENSUS_DATA_BIG_ROUNDS_ABI,
    ROUNDS_STORAGE_READ_ABI,
    TRANSACTION_MANAGER_READ_ABI,
)
from genlayer_py.exceptions import GenLayerError
from typing import TYPE_CHECKING
from genlayer_py.types import GenLayerTransaction, GenLayerRawTransaction
import time
from genlayer_py.chains import localnet
from genlayer_py.utils.jsonifier import (
    calldata_to_user_friendly_json,
    result_to_user_friendly_json,
    b64_to_array,
)

# Fields to remove from simplified transaction receipts
FIELDS_TO_REMOVE = {
    "raw",
    "contract_state",
    "base64",
    "consensus_history",
    "tx_data",
    "eq_blocks_outputs",
    "r",
    "s",
    "v",
    "created_timestamp",
    "current_timestamp",
    "tx_execution_hash",
    "random_seed",
    "states",
    "contract_code",
    "appeal_failed",
    "appeal_leader_timeout",
    "appeal_processing_time",
    "appeal_undetermined",
    "appealed",
    "timestamp_appeal",
    "config_rotation_rounds",
    "rotation_count",
    "queue_position",
    "queue_type",
    "leader_timeout_validators",
    "triggered_by",
    "num_of_initial_validators",
    "timestamp_awaiting_finalization",
    "last_vote_timestamp",
    "read_state_block_range",
    "tx_slot",
}

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


TRANSACTION_ARRAY_PAGE_SIZE = 64


def _normalize_execution_result_name(value: Any) -> Optional[ExecutionResult]:
    if isinstance(value, ExecutionResult):
        return value
    if isinstance(value, str) and value in ExecutionResult._value2member_map_:
        return ExecutionResult(value)
    if value is None:
        return None
    return EXECUTION_RESULT_NUMBER_TO_NAME.get(str(value))


def is_successful(transaction: GenLayerTransaction) -> bool:
    lifecycle = transaction.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return False
    lifecycle_state = lifecycle.get("state")
    successful_lifecycle = (
        lifecycle_state == "finalized"
        and lifecycle.get("outcome") in (None, "accepted")
    ) or (lifecycle_state == "decided" and lifecycle.get("outcome") == "accepted")
    execution_result_name = _normalize_execution_result_name(
        transaction.get(
            "tx_execution_result_name",
            transaction.get("tx_execution_result"),
        )
    )

    if execution_result_name is None:
        consensus_data = transaction.get("consensus_data")
        if isinstance(consensus_data, dict):
            leader_receipt = consensus_data.get("leader_receipt")
            if isinstance(leader_receipt, list):
                leader_receipt = leader_receipt[0] if leader_receipt else None
            if (
                isinstance(leader_receipt, dict)
                and leader_receipt.get("execution_result") == "SUCCESS"
            ):
                execution_result_name = ExecutionResult.FINISHED_WITH_RETURN

    return (
        successful_lifecycle
        and execution_result_name == ExecutionResult.FINISHED_WITH_RETURN
    )


def _wait_for_transaction(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    wait_until: Literal["decided", "finalized"],
    interval: int = transaction_config.wait_interval,
    retries: int = transaction_config.retries,
    full_transaction: bool = False,
) -> GenLayerTransaction:
    attempts = 0
    transaction = None
    last_state = None
    while attempts < retries:
        transaction = self.get_transaction(transaction_hash=transaction_hash)
        if transaction is None:
            raise GenLayerError(f"Transaction {transaction_hash} not found")
        lifecycle = transaction.get("lifecycle")
        if not isinstance(lifecycle, dict) or not isinstance(
            lifecycle.get("state"), str
        ):
            raise GenLayerError(
                f"Transaction {transaction_hash} has no valid lifecycle"
            )
        last_state = lifecycle["state"]
        reached_target = (
            last_state in ("decided", "finalized", "canceled")
            if wait_until == "decided"
            else last_state == "finalized"
        )

        if wait_until == "finalized" and last_state == "canceled":
            raise GenLayerError(
                f"Transaction {transaction_hash} was canceled before finalization"
            )

        if reached_target:
            if not full_transaction:
                return _simplify_transaction_receipt(transaction)
            return transaction
        time.sleep(interval / 1000)
        attempts += 1
    raise GenLayerError(
        f"Transaction {transaction_hash} did not reach '{wait_until}' after {retries} attempts "
        f"(polling every {interval}ms for a total of {retries * interval / 1000:.1f}s). "
        f"Last observed lifecycle state: '{last_state or '<unknown>'}'. "
        f"This may indicate the transaction is still processing, or the network is experiencing delays. "
        f"Consider increasing 'retries' or 'interval' parameters.\n"
        f"Transaction object simplified: {json.dumps(_simplify_transaction_receipt(transaction), indent=2, default=str)}"
    )


def wait_for_decision(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    interval: int = transaction_config.wait_interval,
    retries: int = transaction_config.retries,
    full_transaction: bool = False,
) -> GenLayerTransaction:
    """Poll until the stored transaction state is decided or terminal."""

    return _wait_for_transaction(
        self,
        transaction_hash,
        "decided",
        interval,
        retries,
        full_transaction,
    )


def wait_for_finalization(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    interval: int = transaction_config.wait_interval,
    retries: int = transaction_config.retries,
    full_transaction: bool = False,
) -> GenLayerTransaction:
    """Poll until the stored transaction state is finalized."""

    return _wait_for_transaction(
        self,
        transaction_hash,
        "finalized",
        interval,
        retries,
        full_transaction,
    )


def wait_for_transaction_receipt(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    wait_until: Literal["decided", "finalized"] = "decided",
    interval: int = transaction_config.wait_interval,
    retries: int = transaction_config.retries,
    full_transaction: bool = False,
) -> GenLayerTransaction:
    """Poll for a stored decision (default) or stored finalization."""

    if wait_until == "decided":
        return wait_for_decision(
            self, transaction_hash, interval, retries, full_transaction
        )
    if wait_until == "finalized":
        return wait_for_finalization(
            self, transaction_hash, interval, retries, full_transaction
        )
    raise ValueError("wait_until must be 'decided' or 'finalized'.")


def _call_at_block(contract_function, block_number: int):
    return contract_function.call(block_identifier=block_number)


def _address_manager(
    self: GenLayerClient,
    consensus_data_contract,
    block_number: int,
):
    address_manager_address = _call_at_block(
        consensus_data_contract.functions.addressManager(), block_number
    )
    return self.w3.eth.contract(
        address=address_manager_address, abi=ADDRESS_MANAGER_ABI
    )


def _resolve_contract(
    self: GenLayerClient,
    address_manager,
    name: str,
    abi: List[dict],
    block_number: int,
):
    contract_address = _call_at_block(
        address_manager.functions.getAddressNonZero(name), block_number
    )
    return self.w3.eth.contract(address=contract_address, abi=abi)


def _read_round_validators(
    big_rounds_contract,
    transaction_hash: _Hash32,
    round_number: int,
    validators_count: int,
    block_number: int,
) -> List[Address]:
    validators: List[Address] = []
    for offset in range(0, validators_count, TRANSACTION_ARRAY_PAGE_SIZE):
        page, total = _call_at_block(
            big_rounds_contract.functions.getRoundValidatorsPaged(
                transaction_hash,
                round_number,
                offset,
                TRANSACTION_ARRAY_PAGE_SIZE,
            ),
            block_number,
        )
        if total != validators_count:
            raise GenLayerError(
                "Inconsistent transaction committee size at fixed block "
                f"{block_number}: expected {validators_count}, got {total}"
            )
        validators.extend(page)

    if len(validators) != validators_count:
        raise GenLayerError(
            "Incomplete transaction committee at fixed block "
            f"{block_number}: expected {validators_count}, got {len(validators)}"
        )
    return validators


def _read_consumed_validators(
    big_rounds_contract,
    transaction_hash: _Hash32,
    validators_count: int,
    block_number: int,
) -> List[Address]:
    validators: List[Address] = []
    for offset in range(0, validators_count, TRANSACTION_ARRAY_PAGE_SIZE):
        page, total = _call_at_block(
            big_rounds_contract.functions.getConsumedValidatorsPaged(
                transaction_hash,
                offset,
                TRANSACTION_ARRAY_PAGE_SIZE,
            ),
            block_number,
        )
        if total != validators_count:
            raise GenLayerError(
                "Inconsistent consumed-validator count at fixed block "
                f"{block_number}: expected {validators_count}, got {total}"
            )
        validators.extend(page)

    if len(validators) != validators_count:
        raise GenLayerError(
            "Incomplete consumed-validator set at fixed block "
            f"{block_number}: expected {validators_count}, got {len(validators)}"
        )
    return validators


def _read_train_transaction_data(
    self: GenLayerClient,
    consensus_data_contract,
    transaction_hash: _Hash32,
    block_number: int,
):
    """Compose one bounded transaction snapshot from train read surfaces."""
    address_manager = _address_manager(self, consensus_data_contract, block_number)
    big_rounds = _resolve_contract(
        self,
        address_manager,
        "ConsensusDataBigRounds",
        CONSENSUS_DATA_BIG_ROUNDS_ABI,
        block_number,
    )
    transaction_manager = _resolve_contract(
        self,
        address_manager,
        "TransactionManager",
        TRANSACTION_MANAGER_READ_ABI,
        block_number,
    )
    rounds_storage = _resolve_contract(
        self,
        address_manager,
        "RoundsStorage",
        ROUNDS_STORAGE_READ_ABI,
        block_number,
    )

    tx_data = _call_at_block(
        big_rounds.functions.getStoredTransactionDataLight(transaction_hash),
        block_number,
    )
    last_round = tx_data[21]
    round_number = last_round[0]
    validators_count = last_round[7]
    validators = _read_round_validators(
        big_rounds,
        transaction_hash,
        round_number,
        validators_count,
        block_number,
    )
    consumed_validators = _read_consumed_validators(
        big_rounds,
        transaction_hash,
        tx_data[22],
        block_number,
    )
    validator_votes = _call_at_block(
        rounds_storage.functions.getValidatorVotes(transaction_hash, round_number),
        block_number,
    )
    validator_votes_hash = _call_at_block(
        rounds_storage.functions.getValidatorVotesHash(transaction_hash, round_number),
        block_number,
    )
    validator_result_hash = _call_at_block(
        rounds_storage.functions.getValidatorResultHash(transaction_hash, round_number),
        block_number,
    )
    tx_execution_result = _call_at_block(
        transaction_manager.functions.getTxExecutionResult(transaction_hash),
        block_number,
    )
    num_of_initial_validators = _call_at_block(
        transaction_manager.functions.getNumOfInitialValidators(transaction_hash),
        block_number,
    )

    for label, values in (
        ("validator votes", validator_votes),
        ("validator vote hashes", validator_votes_hash),
        ("validator result hashes", validator_result_hash),
    ):
        if len(values) != validators_count:
            raise GenLayerError(
                f"Incomplete {label} at fixed block {block_number}: "
                f"expected {validators_count}, got {len(values)}"
            )

    return (
        tx_data,
        validators,
        validator_votes,
        validator_votes_hash,
        validator_result_hash,
        consumed_validators,
        tx_execution_result,
        num_of_initial_validators,
    )


def _read_transaction_lifecycle(
    consensus_data_contract,
    transaction_hash: _Hash32,
    block_number: int,
    timestamp: int = 0,
) -> ProtocolTransactionLifecycle:
    lifecycle = _call_at_block(
        consensus_data_contract.functions.getTransactionLifecycle(
            transaction_hash, timestamp
        ),
        block_number,
    )
    stored_status, resolution, latest_decision, decision_active = lifecycle
    projected_status = resolution[2]
    resolution_action = resolution[3]
    resolution_source = resolution[6]
    return {
        "stored_status": int(stored_status),
        "stored_status_name": PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[
            str(stored_status)
        ],
        "projected_status": int(projected_status),
        "projected_status_name": PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[
            str(projected_status)
        ],
        "resolution_action": int(resolution_action),
        "resolution_action_name": RESOLUTION_ACTION_NUMBER_TO_NAME[
            str(resolution_action)
        ],
        "resolution_source": int(resolution_source),
        "resolution_source_name": RESOLUTION_SOURCE_NUMBER_TO_NAME[
            str(resolution_source)
        ],
        "decision_id": str(latest_decision[1]) if decision_active else None,
        "decision_active": bool(decision_active),
        "evaluated_at": int(resolution[17]),
    }


def _decode_rpc_transaction_lifecycle(result: Any) -> ProtocolTransactionLifecycle:
    if not isinstance(result, dict):
        raise GenLayerError("gen_getTransactionLifecycle returned no lifecycle object")

    def code(key: str) -> int:
        value = result.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise GenLayerError(
                f"gen_getTransactionLifecycle returned invalid {key}: {value!r}"
            )
        return value

    stored_status = code("storedStatusCode")
    projected_status = code("projectedStatusCode")
    resolution_action = code("resolutionActionCode")
    resolution_source = code("resolutionSourceCode")
    try:
        stored_status_name = PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[
            str(stored_status)
        ]
        projected_status_name = PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[
            str(projected_status)
        ]
        resolution_action_name = RESOLUTION_ACTION_NUMBER_TO_NAME[
            str(resolution_action)
        ]
        resolution_source_name = RESOLUTION_SOURCE_NUMBER_TO_NAME[
            str(resolution_source)
        ]
    except KeyError as exc:
        raise GenLayerError(
            f"gen_getTransactionLifecycle returned unknown protocol ordinal: {exc.args[0]}"
        ) from exc

    wire_names = {
        "storedStatus": stored_status_name.value,
        "projectedStatus": projected_status_name.value,
        "resolutionAction": resolution_action_name.value,
        "resolutionSource": resolution_source_name.value,
    }
    for key, enum_value in wire_names.items():
        expected = enum_value
        if result.get(key) != expected:
            raise GenLayerError(
                f"gen_getTransactionLifecycle returned inconsistent {key}: "
                f"expected {expected!r}, got {result.get(key)!r}"
            )

    decision_active = result.get("decisionActive")
    if not isinstance(decision_active, bool):
        raise GenLayerError(
            "gen_getTransactionLifecycle returned invalid decisionActive"
        )
    decision_id = result.get("decisionId")
    if decision_id is not None and (
        not isinstance(decision_id, str) or not decision_id.isdigit()
    ):
        raise GenLayerError("gen_getTransactionLifecycle returned invalid decisionId")
    if decision_active != (decision_id is not None):
        raise GenLayerError(
            "gen_getTransactionLifecycle returned inconsistent decision identity"
        )
    evaluated_at = result.get("evaluatedAt")
    if isinstance(evaluated_at, bool) or not isinstance(evaluated_at, int):
        raise GenLayerError("gen_getTransactionLifecycle returned invalid evaluatedAt")

    return {
        "stored_status": stored_status,
        "stored_status_name": stored_status_name,
        "projected_status": projected_status,
        "projected_status_name": projected_status_name,
        "resolution_action": resolution_action,
        "resolution_action_name": resolution_action_name,
        "resolution_source": resolution_source,
        "resolution_source_name": resolution_source_name,
        "decision_id": decision_id,
        "decision_active": decision_active,
        "evaluated_at": evaluated_at,
    }


def get_transaction_lifecycle(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    timestamp: Optional[int] = None,
) -> ProtocolTransactionLifecycle:
    """Return the raw stored/projected resolution-kernel view.

    This is an advanced protocol API. Ordinary consumers should use the
    discriminated ``lifecycle`` returned by :func:`get_transaction`.
    """

    if self.chain.id == localnet.id:
        params: Dict[str, Any] = {
            "txId": (
                Web3.to_hex(transaction_hash)
                if isinstance(transaction_hash, bytes)
                else transaction_hash
            )
        }
        if timestamp is not None:
            params["timestamp"] = timestamp
        response = self.provider.make_request(
            method="gen_getTransactionLifecycle", params=[params]
        )
        return _decode_rpc_transaction_lifecycle(response.get("result"))

    consensus_data_contract = self.w3.eth.contract(
        address=self.chain.consensus_data_contract["address"],
        abi=self.chain.consensus_data_contract["abi"],
    )
    block_number = self.w3.eth.block_number
    return _read_transaction_lifecycle(
        consensus_data_contract,
        transaction_hash,
        block_number,
        timestamp if timestamp is not None else 0,
    )


def get_transaction(
    self: GenLayerClient,
    transaction_hash: _Hash32,
) -> GenLayerTransaction:
    if self.chain.id == localnet.id:
        transaction = self.provider.make_request(
            method="eth_getTransactionByHash", params=[transaction_hash]
        )["result"]
        protocol_status = (
            ProtocolTransactionStatus.PENDING
            if transaction["status"] == "ACTIVATED"
            else transaction["status"]
        )
        lifecycle = transaction_lifecycle_from_protocol_status(protocol_status)
        if lifecycle["state"] == "finalized":
            outcome = transaction_outcome_from_protocol_result(
                transaction.get("result_name", transaction.get("result", 0))
            )
            if outcome is not None:
                lifecycle["outcome"] = outcome
        transaction["lifecycle"] = lifecycle
        transaction.pop("status", None)
        transaction.pop("status_name", None)
        return _decode_localnet_transaction(transaction)
    # Decode one fixed-block train snapshot. The light record and split array
    # reads avoid the oversized aggregate getTransactionAllData response.
    consensus_data_contract = self.w3.eth.contract(
        address=self.chain.consensus_data_contract["address"],
        abi=self.chain.consensus_data_contract["abi"],
    )
    block_number = self.w3.eth.block_number
    (
        tx_data,
        validators,
        validator_votes,
        validator_votes_hash,
        validator_result_hash,
        consumed_validators,
        tx_execution_result,
        num_of_initial_validators,
    ) = _read_train_transaction_data(
        self,
        consensus_data_contract,
        transaction_hash,
        block_number,
    )
    raw_transaction = GenLayerRawTransaction.from_transaction_data_light(
        tx_data,
        validators,
        validator_votes,
        validator_votes_hash,
        validator_result_hash,
        consumed_validators,
        tx_execution_result,
        num_of_initial_validators,
    )
    decoded_transaction = raw_transaction.decode()
    decoded_transaction["triggered_transactions"] = _decode_triggered_txs(
        self, decoded_transaction
    )
    return decoded_transaction


def _decode_triggered_txs(
    self: GenLayerClient, tx: GenLayerTransaction
) -> List[HexStr]:
    lifecycle = tx["lifecycle"]
    state = lifecycle["state"]
    accepted = state == "decided" and lifecycle.get("outcome") == "accepted"
    if not accepted and state != "finalized":
        return []

    event_hashes_by_status = {
        "finalized": self.w3.keccak(text="TransactionFinalized(bytes32)").hex(),
        "accepted": self.w3.keccak(text="TransactionAccepted(bytes32)").hex(),
    }

    def process_events_for_status(
        event_status: Literal["accepted", "finalized"],
    ) -> List[HexStr]:
        """Helper function to process events for a given status."""
        event_signature_hash = event_hashes_by_status[event_status]
        from_block = int(tx["read_state_block_range"]["proposal_block"])
        max_range = 10000
        latest_block = self.w3.eth.block_number
        to_block = min(from_block + max_range, latest_block)
        logs = self.w3.eth.get_logs(
            {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": self.chain.consensus_main_contract["address"],
                "topics": [event_signature_hash, tx["tx_id"]],
            }
        )
        if not logs:
            return []

        tx_hash = logs[0]["transactionHash"].hex()
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        consensus_main_contract = self.w3.eth.contract(
            abi=self.chain.consensus_main_contract["abi"]
        )
        event = consensus_main_contract.get_event_by_name("InternalMessageProcessed")
        events = event.process_receipt(tx_receipt, DISCARD)

        return [self.w3.to_hex(event["args"]["txId"]) for event in events]

    triggered_txs = []

    # Triggered transactions can happen on ACCEPTED or FINALIZED statuses
    if accepted or state == "finalized":
        triggered_txs.extend(process_events_for_status("accepted"))

    if state == "finalized":
        triggered_txs.extend(process_events_for_status("finalized"))

    return triggered_txs


def get_triggered_transaction_ids(
    self: GenLayerClient,
    transaction_hash: _Hash32,
) -> List[HexStr]:
    if self.chain.id == localnet.id:
        tx = get_transaction(self, transaction_hash)
        return tx.get("triggered_transactions", [])

    tx = get_transaction(self, transaction_hash)
    return _decode_triggered_txs(self, tx)


def debug_trace_transaction(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    round: int = 0,
) -> Dict[str, Any]:
    response = self.provider.make_request(
        method="gen_dbg_traceTransaction",
        params=[
            {
                "txID": (
                    Web3.to_hex(transaction_hash)
                    if isinstance(transaction_hash, bytes)
                    else transaction_hash
                ),
                "round": round,
            }
        ],
    )
    return response.get("result", {})


def _simplify_transaction_receipt(tx: GenLayerTransaction) -> GenLayerTransaction:
    """
    Simplify transaction receipt by removing non-essential fields while preserving functionality.

    Removes: Binary data, internal timestamps, appeal fields, processing details, historical data
    Preserves: Transaction IDs, lifecycle, execution results, node configs, readable data
    """
    simplified_tx = tx.copy()

    def remove_non_readable_fields(obj, path=""):
        if isinstance(obj, dict):
            filtered_dict = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                # Always remove these fields
                if key in FIELDS_TO_REMOVE:
                    continue

                # Remove node_config only from top level (keep it in consensus_data)
                if key == "node_config" and "consensus_data" not in path:
                    continue

                # Special handling for consensus_data - keep execution results and votes
                if key == "consensus_data" and isinstance(value, dict):
                    simplified_consensus = {}

                    # Keep votes
                    if "votes" in value:
                        simplified_consensus["votes"] = value["votes"]

                    # Process leader_receipt to keep only essential fields
                    if "leader_receipt" in value and isinstance(
                        value["leader_receipt"], list
                    ):
                        simplified_receipts = []
                        for receipt in value["leader_receipt"]:
                            simplified_receipt = {}
                            # Keep essential execution info
                            if "execution_result" in receipt:
                                simplified_receipt["execution_result"] = receipt[
                                    "execution_result"
                                ]
                            if "genvm_result" in receipt:
                                simplified_receipt["genvm_result"] = receipt[
                                    "genvm_result"
                                ]
                            if "mode" in receipt:
                                simplified_receipt["mode"] = receipt["mode"]
                            if "vote" in receipt:
                                simplified_receipt["vote"] = receipt["vote"]
                            if "node_config" in receipt:
                                simplified_receipt["node_config"] = receipt[
                                    "node_config"
                                ]
                            # Keep readable calldata
                            if (
                                "calldata" in receipt
                                and isinstance(receipt["calldata"], dict)
                                and "readable" in receipt["calldata"]
                            ):
                                simplified_receipt["calldata"] = {
                                    "readable": receipt["calldata"]["readable"]
                                }
                            # Keep readable outputs
                            if "eq_outputs" in receipt:
                                simplified_receipt["eq_outputs"] = (
                                    remove_non_readable_fields(
                                        receipt["eq_outputs"], current_path
                                    )
                                )
                            if "result" in receipt:
                                simplified_receipt["result"] = (
                                    remove_non_readable_fields(
                                        receipt["result"], current_path
                                    )
                                )
                            simplified_receipts.append(simplified_receipt)
                        simplified_consensus["leader_receipt"] = simplified_receipts

                    # Process validators to keep execution results
                    if "validators" in value and isinstance(value["validators"], list):
                        simplified_validators = []
                        for validator in value["validators"]:
                            simplified_validator = {}
                            if "execution_result" in validator:
                                simplified_validator["execution_result"] = validator[
                                    "execution_result"
                                ]
                            if "genvm_result" in validator:
                                simplified_validator["genvm_result"] = validator[
                                    "genvm_result"
                                ]
                            if "mode" in validator:
                                simplified_validator["mode"] = validator["mode"]
                            if "vote" in validator:
                                simplified_validator["vote"] = validator["vote"]
                            if "node_config" in validator:
                                simplified_validator["node_config"] = validator[
                                    "node_config"
                                ]
                            simplified_validators.append(simplified_validator)
                        if simplified_validators:
                            simplified_consensus["validators"] = simplified_validators

                    filtered_dict[key] = simplified_consensus
                    continue
                elif isinstance(value, (dict, list)):
                    result = remove_non_readable_fields(value, current_path)
                    if result:  # Only include if not empty after filtering
                        filtered_dict[key] = result
                else:
                    filtered_dict[key] = value
            return filtered_dict
        elif isinstance(obj, list):
            return [remove_non_readable_fields(item, path) for item in obj if item]
        else:
            return obj

    return remove_non_readable_fields(simplified_tx)


def _decode_localnet_transaction(tx: GenLayerTransaction) -> GenLayerTransaction:
    if "data" not in tx or tx["data"] is None:
        return tx

    try:
        leader_receipt = tx.get("consensus_data", {}).get("leader_receipt")
        if leader_receipt is not None:
            receipts = (
                leader_receipt if isinstance(leader_receipt, list) else [leader_receipt]
            )
            for receipt in receipts:
                if "result" in receipt:
                    receipt["result"] = result_to_user_friendly_json(receipt["result"])

                if "calldata" in receipt:
                    receipt["calldata"] = {
                        "base64": receipt["calldata"],
                        **calldata_to_user_friendly_json(
                            b64_to_array(receipt["calldata"])
                        ),
                    }

                if "eq_outputs" in receipt:
                    decoded_outputs = {}
                    for key, value in receipt["eq_outputs"].items():
                        try:
                            decoded_outputs[key] = result_to_user_friendly_json(value)
                        except Exception as e:
                            logger.warning(f"Error decoding eq_output {key}: {str(e)}")
                            decoded_outputs[key] = value
                    receipt["eq_outputs"] = decoded_outputs

        if "calldata" in tx.get("data", {}):
            tx["data"]["calldata"] = {
                "base64": tx["data"]["calldata"],
                **calldata_to_user_friendly_json(b64_to_array(tx["data"]["calldata"])),
            }

    except Exception as e:
        logger.warning(f"Error decoding transaction: {str(e)}")
    return tx
