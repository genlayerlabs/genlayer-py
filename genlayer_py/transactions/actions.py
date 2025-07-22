from __future__ import annotations

from genlayer_py.logging import logger
import json
from typing import List
from web3.types import _Hash32
from eth_typing import HexStr
from web3.logs import DISCARD

from genlayer_py.config import transaction_config
from genlayer_py.types import (
    TransactionStatus,
    TRANSACTION_STATUS_NAME_TO_NUMBER,
    TRANSACTION_STATUS_NUMBER_TO_NAME,
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

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


def wait_for_transaction_receipt(
    self: GenLayerClient,
    transaction_hash: _Hash32,
    status: TransactionStatus = TransactionStatus.ACCEPTED,
    interval: int = transaction_config.wait_interval,
    retries: int = transaction_config.retries,
    full_transaction: bool = False,
) -> GenLayerTransaction:

    attempts = 0
    while attempts < retries:
        transaction = self.get_transaction(transaction_hash=transaction_hash)
        if transaction is None:
            raise GenLayerError(f"Transaction {transaction_hash} not found")
        transaction_status = str(transaction["status"])
        last_status = TRANSACTION_STATUS_NUMBER_TO_NAME[transaction_status]
        finalized_status = TRANSACTION_STATUS_NAME_TO_NUMBER[
            TransactionStatus.FINALIZED
        ]
        requested_status = TRANSACTION_STATUS_NAME_TO_NUMBER[status]

        if transaction_status == requested_status or (
            status == TransactionStatus.ACCEPTED
            and transaction_status == finalized_status
        ):
            if not full_transaction:
                return _simplify_transaction_receipt(transaction)
            return transaction
        time.sleep(interval / 1000)
        attempts += 1
    raise GenLayerError(
        f"Transaction {transaction_hash} did not reach desired status '{status.value}' after {retries} attempts "
        f"(polling every {interval}ms for a total of {retries * interval / 1000:.1f}s). "
        f"Last observed status: '{last_status.value}'. "
        f"This may indicate the transaction is still processing, or the network is experiencing delays. "
        f"Consider increasing 'retries' or 'interval' parameters.\n"
        f"Transaction object: {json.dumps(transaction, indent=2, default=str)}"
    )


def get_transaction(
    self: GenLayerClient,
    transaction_hash: _Hash32,
) -> GenLayerTransaction:
    if self.chain.id == localnet.id:
        transaction = self.provider.make_request(
            method="eth_getTransactionByHash", params=[transaction_hash]
        )["result"]
        localnet_status = (
            TransactionStatus.PENDING
            if transaction["status"] == "ACTIVATED"
            else transaction["status"]
        )
        transaction["status"] = int(TRANSACTION_STATUS_NAME_TO_NUMBER[localnet_status])
        transaction["status_name"] = localnet_status
        return _decode_localnet_transaction(transaction)
    # Decode for testnet
    consensus_data_contract = self.w3.eth.contract(
        address=self.chain.consensus_data_contract["address"],
        abi=self.chain.consensus_data_contract["abi"],
    )
    transaction = consensus_data_contract.functions.getTransactionData(
        transaction_hash, int(time.time())
    ).call()
    raw_transaction = GenLayerRawTransaction.from_transaction_data(transaction)
    decoded_transaction = raw_transaction.decode()
    decoded_transaction["triggered_transactions"] = _decode_triggered_txs(
        self, decoded_transaction
    )
    return decoded_transaction


def _decode_triggered_txs(
    self: GenLayerClient, tx: GenLayerTransaction
) -> List[HexStr]:
    status = TRANSACTION_STATUS_NUMBER_TO_NAME[tx["status"]]
    if status not in [TransactionStatus.FINALIZED, TransactionStatus.ACCEPTED]:
        return []

    event_hashes_by_status = {
        TransactionStatus.FINALIZED: self.w3.keccak(
            text="TransactionFinalized(bytes32)"
        ).hex(),
        TransactionStatus.ACCEPTED: self.w3.keccak(
            text="TransactionAccepted(bytes32)"
        ).hex(),
    }

    def process_events_for_status(event_status: TransactionStatus) -> List[HexStr]:
        """Helper function to process events for a given status."""
        event_signature_hash = event_hashes_by_status[event_status]
        logs = self.w3.eth.get_logs(
            {
                "fromBlock": int(tx["read_state_block_range"]["proposal_block"]),
                "toBlock": "latest",
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
    if status in [TransactionStatus.ACCEPTED, TransactionStatus.FINALIZED]:
        triggered_txs.extend(process_events_for_status(TransactionStatus.ACCEPTED))

    if status == TransactionStatus.FINALIZED:
        triggered_txs.extend(process_events_for_status(TransactionStatus.FINALIZED))

    return triggered_txs


def _simplify_transaction_receipt(tx: GenLayerTransaction) -> GenLayerTransaction:
    """
    Simplify transaction receipt by removing non-essential fields while preserving functionality.

    Removes: Binary data, internal timestamps, appeal fields, processing details, historical data
    Preserves: Transaction IDs, status, execution results, node configs, readable data
    """
    simplified_tx = tx.copy()

    def remove_non_readable_fields(obj, path=""):
        if isinstance(obj, dict):
            filtered_dict = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                # Always remove these fields
                if key in [
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
                    # Remove appeal fields that are usually defaults
                    "appeal_failed",
                    "appeal_leader_timeout",
                    "appeal_processing_time",
                    "appeal_undetermined",
                    "appealed",
                    "timestamp_appeal",
                    # Remove internal processing fields
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
                ]:
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
                            if "calldata" in receipt and isinstance(
                                receipt["calldata"], dict
                            ):
                                if "readable" in receipt["calldata"]:
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
