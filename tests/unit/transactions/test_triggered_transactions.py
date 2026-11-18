from types import SimpleNamespace
from unittest.mock import Mock

from hexbytes import HexBytes
from web3 import Web3

import genlayer_py.transactions.actions as transaction_actions
from genlayer_py.chains import testnet_bradbury

TX_ID = "0x" + "ab" * 32
RECEIPT_TX_HASH = HexBytes("0x" + "cd" * 32)


def _client():
    event = Mock()
    event.process_receipt.return_value = []
    consensus_main = Mock()
    consensus_main.get_event_by_name.return_value = event
    eth = Mock()
    eth.block_number = 200
    eth.get_logs.return_value = [{"transactionHash": RECEIPT_TX_HASH}]
    eth.wait_for_transaction_receipt.return_value = {}
    eth.contract.return_value = consensus_main
    w3 = SimpleNamespace(keccak=Web3.keccak, to_hex=Web3.to_hex, eth=eth)
    return SimpleNamespace(w3=w3, chain=testnet_bradbury)


def test_triggered_transaction_log_filters_use_0x_prefixed_hex():
    client = _client()
    tx = {
        "tx_id": TX_ID,
        "lifecycle": {"state": "finalized", "outcome": "accepted"},
        "read_state_block_range": {"proposal_block": 100},
    }

    assert transaction_actions._decode_triggered_txs(client, tx) == []

    topics = [
        call.args[0]["topics"][0] for call in client.w3.eth.get_logs.call_args_list
    ]
    assert topics == [
        Web3.to_hex(Web3.keccak(text="TransactionAccepted(bytes32)")),
        Web3.to_hex(Web3.keccak(text="TransactionFinalized(bytes32)")),
    ]
    assert all(topic.startswith("0x") for topic in topics)
    for call in client.w3.eth.wait_for_transaction_receipt.call_args_list:
        assert call.args[0] == RECEIPT_TX_HASH.to_0x_hex()
