from types import SimpleNamespace
from unittest.mock import Mock

import eth_utils
from web3 import Web3

import genlayer_py.contracts.actions as contract_actions


ADD_TRANSACTION_ABI_V5 = [
    {
        "type": "function",
        "name": "addTransaction",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_sender", "type": "address"},
            {"name": "_recipient", "type": "address"},
            {"name": "_numOfInitialValidators", "type": "uint256"},
            {"name": "_maxRotations", "type": "uint256"},
            {"name": "_calldata", "type": "bytes"},
        ],
        "outputs": [],
    }
]

ADD_TRANSACTION_ABI_V6 = [
    {
        "type": "function",
        "name": "addTransaction",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_sender", "type": "address"},
            {"name": "_recipient", "type": "address"},
            {"name": "_numOfInitialValidators", "type": "uint256"},
            {"name": "_maxRotations", "type": "uint256"},
            {"name": "_calldata", "type": "bytes"},
            {"name": "_validUntil", "type": "uint256"},
        ],
        "outputs": [],
    }
]

SENDER = "0x1111111111111111111111111111111111111111"
RECIPIENT = "0x2222222222222222222222222222222222222222"


def _make_client(add_transaction_abi):
    chain = SimpleNamespace(
        id=61999,
        consensus_main_contract={
            "address": "0x3333333333333333333333333333333333333333",
            "abi": add_transaction_abi,
        },
        default_number_of_initial_validators=5,
        default_consensus_max_rotations=3,
    )
    local_account = SimpleNamespace(address=SENDER)
    return SimpleNamespace(
        chain=chain,
        local_account=local_account,
        w3=Web3(),
    )


def test_encode_add_transaction_uses_v5_signature_when_abi_has_5_inputs():
    client = _make_client(ADD_TRANSACTION_ABI_V5)

    encoded = contract_actions._encode_add_transaction_data(
        self=client,
        sender_account=client.local_account,
        recipient=RECIPIENT,
        consensus_max_rotations=3,
        data="0x",
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes)"
    )[:4].hex()
    assert encoded.startswith(f"0x{selector}")


def test_encode_add_transaction_uses_v6_signature_when_abi_has_6_inputs():
    client = _make_client(ADD_TRANSACTION_ABI_V6)

    encoded = contract_actions._encode_add_transaction_data(
        self=client,
        sender_account=client.local_account,
        recipient=RECIPIENT,
        consensus_max_rotations=3,
        data="0x",
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes,uint256)"
    )[:4].hex()
    assert encoded.startswith(f"0x{selector}")


def test_write_contract_refreshes_consensus_abi_before_add_transaction_encoding(
    monkeypatch,
):
    client = _make_client(ADD_TRANSACTION_ABI_V5)
    client.initialize_consensus_smart_contract = Mock(
        side_effect=lambda: client.chain.consensus_main_contract.__setitem__(
            "abi", ADD_TRANSACTION_ABI_V6
        )
    )

    captured = {}

    def fake_send_transaction(**kwargs):
        captured["encoded_data"] = kwargs["encoded_data"]
        return "0xdeadbeef"

    monkeypatch.setattr(contract_actions, "_send_transaction", fake_send_transaction)

    result = contract_actions.write_contract(
        self=client,
        address=RECIPIENT,
        function_name="ping",
        account=client.local_account,
        value=0,
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes,uint256)"
    )[:4].hex()
    assert result == "0xdeadbeef"
    client.initialize_consensus_smart_contract.assert_called_once_with()
    assert captured["encoded_data"].startswith(f"0x{selector}")
