"""Unit tests for the staking action module.

The tests here are structural — they check that methods encode the
expected ABI signature and target the right contract (Staking vs.
ValidatorWallet). End-to-end stake lifecycle is covered in the
ci-core-e2e-runner tooling suite instead, since it needs a live node.
"""

from types import SimpleNamespace
from unittest.mock import Mock

from eth_abi import decode as abi_decode
from eth_utils import keccak
import pytest
from web3 import Web3

import genlayer_py.staking.actions as staking_actions
from genlayer_py.exceptions import GenLayerError
from genlayer_py.staking.abi import STAKING_ABI, VALIDATOR_WALLET_ABI
from genlayer_py.staking.operator_registration import (
    OperatorRegistrationContext,
    OperatorRegistrationProof,
)

STAKING_ADDR = "0x1111111111111111111111111111111111111111"
WALLET_ADDR = "0x2222222222222222222222222222222222222222"
SENDER_ADDR = "0x3333333333333333333333333333333333333333"
OTHER_ADDR = "0x4444444444444444444444444444444444444444"
ADDRESS_MANAGER_ADDR = "0x5555555555555555555555555555555555555555"
FACTORY_ADDR = "0x6666666666666666666666666666666666666666"

# 4-byte selectors for the function signatures we rely on.
SEL_VALIDATOR_JOIN = keccak(text="validatorJoin(uint256[2],bytes)")[:4].hex()
SEL_WALLET_DEPOSIT = keccak(text="validatorDeposit()")[:4].hex()
SEL_WALLET_EXIT = keccak(text="validatorExit(uint256)")[:4].hex()
SEL_DELEGATOR_JOIN = keccak(text="delegatorJoin(address)")[:4].hex()

REGISTRATION = OperatorRegistrationProof(
    operator=OTHER_ADDR,
    operator_pub_key=(1, 2),
    possession_proof=b"\x99" * 65,
)
JOIN_CONTEXT = OperatorRegistrationContext(
    registrar=FACTORY_ADDR,
    owner=SENDER_ADDR,
    chain_id=61999,
)


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


def test_validator_join_targets_staking_and_encodes_proof(monkeypatch):
    client = _make_client()
    monkeypatch.setattr(
        staking_actions,
        "get_validator_join_context",
        lambda self, account=None: JOIN_CONTEXT,
    )
    monkeypatch.setattr(
        staking_actions,
        "verify_operator_registration",
        lambda registration, context: registration is REGISTRATION
        and context == JOIN_CONTEXT,
    )

    staking_actions.validator_join(self=client, amount=10, registration=REGISTRATION)
    tx = _last_tx(client)
    assert tx["to"].lower() == STAKING_ADDR.lower()
    assert tx["value"] == 10
    assert tx["data"][2:10] == SEL_VALIDATOR_JOIN
    pub_key, proof = abi_decode(
        ("uint256[2]", "bytes"), Web3.to_bytes(hexstr=tx["data"][10:])
    )
    assert pub_key == (1, 2)
    assert proof == REGISTRATION.possession_proof


@pytest.mark.parametrize(
    "kwargs",
    ({}, {"operator": OTHER_ADDR}, {"registration": OTHER_ADDR}),
)
def test_validator_join_rejects_legacy_address_only_calls(kwargs):
    client = _make_client()
    with pytest.raises(GenLayerError, match="OperatorRegistrationProof"):
        staking_actions.validator_join(self=client, amount=10, **kwargs)
    client.local_account.sign_transaction.assert_not_called()


def test_validator_join_rejects_proof_for_the_wrong_context(monkeypatch):
    client = _make_client()
    monkeypatch.setattr(
        staking_actions,
        "get_validator_join_context",
        lambda self, account=None: JOIN_CONTEXT,
    )
    monkeypatch.setattr(
        staking_actions,
        "verify_operator_registration",
        lambda registration, context: False,
    )

    with pytest.raises(GenLayerError, match="fresh proof"):
        staking_actions.validator_join(
            self=client, amount=10, registration=REGISTRATION
        )
    client.local_account.sign_transaction.assert_not_called()


def test_validator_join_context_uses_factory_and_sender(monkeypatch):
    staking = SimpleNamespace(
        functions=SimpleNamespace(
            addressManager=lambda: SimpleNamespace(call=lambda: ADDRESS_MANAGER_ADDR)
        )
    )
    get_address = Mock(return_value=SimpleNamespace(call=lambda: FACTORY_ADDR))
    address_manager = SimpleNamespace(
        functions=SimpleNamespace(getAddressNonZero=get_address)
    )
    client = SimpleNamespace(
        local_account=SimpleNamespace(address=SENDER_ADDR),
        w3=SimpleNamespace(
            to_checksum_address=Web3.to_checksum_address,
            eth=SimpleNamespace(
                chain_id=61999,
                contract=Mock(return_value=address_manager),
            ),
        ),
    )
    monkeypatch.setattr(staking_actions, "_staking", lambda self: staking)

    assert staking_actions.get_validator_join_context(client) == JOIN_CONTEXT
    get_address.assert_called_once_with("ValidatorWalletFactory")


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


def test_set_operator_fails_with_actionable_migration_without_sending():
    client = _make_client()
    with pytest.raises(GenLayerError, match="initiate_operator_transfer"):
        staking_actions.set_operator(
            self=client, validator=WALLET_ADDR, operator=OTHER_ADDR
        )
    client.local_account.sign_transaction.assert_not_called()


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
    wallet_names = {
        e["name"] for e in VALIDATOR_WALLET_ABI if e.get("type") == "function"
    }
    assert {
        "epoch",
        "selectableValidators",
        "selectableValidatorsCount",
        "validatorsJoinedCount",
        "getValidatorsJoined",
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
    assert {
        "validatorDeposit",
        "validatorExit",
        "setOperatorPubKey",
        "setIdentity",
    }.issubset(wallet_names)
    assert "setOperator" not in wallet_names
    # Withdrawn from the staking contract: keeping them in the bundled ABI lets
    # callers reach entrypoints that revert.
    assert (
        not {
            "activeValidators",
            "activeValidatorsCount",
            "activeWeights",
            "validatorsRoot",
        }
        & names
    )


class _PagedStakingStub:
    """Stands in for selectable and joined Staking reads."""

    def __init__(self, registry, selectable=None, page_len=None):
        self._registry = registry
        self._selectable = registry if selectable is None else selectable
        self._page_len = page_len
        self.pages_requested = []
        self.functions = self

    def selectableValidators(self):
        return SimpleNamespace(call=lambda: self._selectable)

    def selectableValidatorsCount(self):
        return SimpleNamespace(call=lambda: len(self._selectable))

    def validatorsJoinedCount(self):
        return SimpleNamespace(call=lambda: len(self._registry))

    def getValidatorsJoined(self, start, size):
        self.pages_requested.append((start, size))
        take = self._page_len or size
        return SimpleNamespace(call=lambda: self._registry[start : start + take])


def _client_with_staking_stub(monkeypatch, stub):
    client = _make_client()
    monkeypatch.setattr(staking_actions, "_staking", lambda self: stub)
    return client


def test_active_validators_are_strictly_selectable(monkeypatch):
    joined_but_not_selectable = "0x" + "a1" * 20
    selectable = "0x" + "b2" * 20
    stub = _PagedStakingStub(
        [joined_but_not_selectable, selectable], selectable=[selectable]
    )
    client = _client_with_staking_stub(monkeypatch, stub)

    assert staking_actions.active_validators(self=client) == [selectable]
    assert staking_actions.active_validators_count(self=client) == 1
    assert stub.pages_requested == []


def test_joined_validators_pages_the_registry(monkeypatch):
    registry = [f"0x{str(i) * 40}" for i in range(1, 6)]
    stub = _PagedStakingStub(registry, page_len=2)
    client = _client_with_staking_stub(monkeypatch, stub)

    monkeypatch.setattr(staking_actions, "VALIDATORS_JOINED_PAGE_SIZE", 2)
    result = staking_actions.joined_validators(self=client)

    assert result == registry
    assert stub.pages_requested == [(0, 2), (2, 2), (4, 2)]


def test_joined_validators_stops_on_a_short_page(monkeypatch):
    """An empty page means the registry shrank mid-walk: stop, do not spin."""
    stub = _PagedStakingStub([])
    stub._registry = ["0x" + "a1" * 20]
    # Report a count far larger than what the pages actually yield.
    stub.validatorsJoinedCount = lambda: SimpleNamespace(call=lambda: 500)
    client = _client_with_staking_stub(monkeypatch, stub)

    result = staking_actions.joined_validators(self=client)

    assert result == ["0x" + "a1" * 20]
    assert len(stub.pages_requested) == 2


def test_joined_validators_filters_zero_address(monkeypatch):
    zero = "0x" + "00" * 20
    stub = _PagedStakingStub(["0x" + "a1" * 20, zero])
    client = _client_with_staking_stub(monkeypatch, stub)

    assert staking_actions.joined_validators(self=client) == ["0x" + "a1" * 20]


def test_joined_validators_count_reads_the_registry(monkeypatch):
    stub = _PagedStakingStub(["0x" + "a1" * 20, "0x" + "b2" * 20])
    client = _client_with_staking_stub(monkeypatch, stub)

    assert staking_actions.joined_validators_count(self=client) == 2
