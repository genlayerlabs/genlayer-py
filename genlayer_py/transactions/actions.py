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
