"""Unit tests for the staking action module.

The tests here are structural — they check that methods encode the
expected ABI signature and target the right contract (Staking vs.
ValidatorWallet). End-to-end stake lifecycle is covered in the
ci-core-e2e-runner tooling suite instead, since it needs a live node.
"""

from types import SimpleNamespace
from unittest.mock import Mock

from eth_utils import keccak
import pytest
from web3 import Web3

import genlayer_py.staking.actions as staking_actions
from genlayer_py.staking.abi import STAKING_ABI, VALIDATOR_WALLET_ABI


STAKING_ADDR = "0x1111111111111111111111111111111111111111"
WALLET_ADDR = "0x2222222222222222222222222222222222222222"
SENDER_ADDR = "0x3333333333333333333333333333333333333333"
OTHER_ADDR = "0x4444444444444444444444444444444444444444"

# 4-byte selectors for the function signatures we rely on.
SEL_VALIDATOR_JOIN_NO_ARGS = keccak(text="validatorJoin()")[:4].hex()
SEL_VALIDATOR_JOIN_ADDR = keccak(text="validatorJoin(address)")[:4].hex()
SEL_WALLET_DEPOSIT = keccak(text="validatorDeposit()")[:4].hex()
SEL_WALLET_EXIT = keccak(text="validatorExit(uint256)")[:4].hex()
SEL_SET_OPERATOR = keccak(text="setOperator(address)")[:4].hex()
SEL_DELEGATOR_JOIN = keccak(text="delegatorJoin(address)")[:4].hex()


def _make_client():
    """SimpleNamespace stand-in for GenLayerClient — enough surface for
    the action helpers. Uses a real Web3().eth for contract encoding,
    but patches the eth methods that would otherwise hit a live node."""
    signed = SimpleNamespace(raw_transaction=b"\x00")
    w3 = Web3()
    w3.eth.get_transaction_count = Mock(return_value=1)
    w3.eth.estimate_gas = Mock(return_value=100_000)
    w3.eth.send_raw_transaction = Mock(return_value=b"\xde\xad" * 16)
    # gas_price is a property on Eth — stub the attr path used by _build.
    type(w3.eth).gas_price = 1_000_000_000  # type: ignore[assignment]

    local_account = SimpleNamespace(
        address=SENDER_ADDR,
        sign_transaction=Mock(return_value=signed),
    )
    chain = SimpleNamespace(
        id=61999,
        staking_contract={"address": STAKING_ADDR, "abi": STAKING_ABI},
    )
    return SimpleNamespace(chain=chain, local_account=local_account, w3=w3)


def _last_tx(client):
    """Return the tx dict the client's sign_transaction was called with."""
    return client.local_account.sign_transaction.call_args.args[0]


def test_validator_join_no_operator_targets_staking_and_encodes_empty_args():
    client = _make_client()
    staking_actions.validator_join(self=client, amount=10)
    tx = _last_tx(client)
    assert tx["to"].lower() == STAKING_ADDR.lower()
    assert tx["value"] == 10
    assert tx["data"][2:10] == SEL_VALIDATOR_JOIN_NO_ARGS


def test_validator_join_with_operator_encodes_address_variant():
    client = _make_client()
    staking_actions.validator_join(self=client, amount=10, operator=OTHER_ADDR)
    tx = _last_tx(client)
    assert tx["data"][2:10] == SEL_VALIDATOR_JOIN_ADDR


def test_validator_deposit_targets_wallet_not_staking():
    """The sender check on Staking.validatorDeposit requires msg.sender
    to be the ValidatorWallet — the SDK must route through the wallet."""
    client = _make_client()
    staking_actions.validator_deposit(self=client, validator=WALLET_ADDR, amount=5)
    tx = _last_tx(client)
    assert tx["to"].lower() == WALLET_ADDR.lower()
    assert tx["to"].lower() != STAKING_ADDR.lower()
    assert tx["value"] == 5
    assert tx["data"][2:10] == SEL_WALLET_DEPOSIT


def test_validator_exit_routes_through_wallet():
    client = _make_client()
    staking_actions.validator_exit(self=client, validator=WALLET_ADDR, shares=42)
    tx = _last_tx(client)
    assert tx["to"].lower() == WALLET_ADDR.lower()
    assert tx["data"][2:10] == SEL_WALLET_EXIT


def test_set_operator_routes_through_wallet():
    client = _make_client()
    staking_actions.set_operator(self=client, validator=WALLET_ADDR, operator=OTHER_ADDR)
    tx = _last_tx(client)
    assert tx["to"].lower() == WALLET_ADDR.lower()
    assert tx["data"][2:10] == SEL_SET_OPERATOR


def test_delegator_join_targets_staking_with_value():
    client = _make_client()
    staking_actions.delegator_join(self=client, validator=WALLET_ADDR, amount=7)
    tx = _last_tx(client)
    assert tx["to"].lower() == STAKING_ADDR.lower()
    assert tx["value"] == 7
    assert tx["data"][2:10] == SEL_DELEGATOR_JOIN


def test_staking_not_configured_raises():
    client = _make_client()
    client.chain.staking_contract = None
    with pytest.raises(Exception, match="staking_contract"):
        staking_actions.epoch(self=client)


def test_abis_include_expected_functions():
    """Guard against the bundled ABI JSON drifting or truncating."""
    names = {e["name"] for e in STAKING_ABI if e.get("type") == "function"}
    wallet_names = {e["name"] for e in VALIDATOR_WALLET_ABI if e.get("type") == "function"}
    assert {
        "epoch",
        "activeValidators",
        "activeValidatorsCount",
        "isValidator",
        "validatorView",
        "stakeOf",
        "validatorJoin",
        "validatorClaim",
        "validatorPrime",
        "delegatorJoin",
        "delegatorExit",
        "delegatorClaim",
    }.issubset(names)
    assert {"validatorDeposit", "validatorExit", "setOperator", "setIdentity"}.issubset(
        wallet_names
    )
