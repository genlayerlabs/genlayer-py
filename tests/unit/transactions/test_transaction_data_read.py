"""Train-only transaction reads use bounded surfaces at one block snapshot."""

from types import SimpleNamespace
from unittest.mock import Mock

import genlayer_py.transactions.actions as transaction_actions
import pytest
from genlayer_py.consensus.abi import (
    CONSENSUS_DATA_ABI,
    CONSENSUS_DATA_ABI_V06,
    CONSENSUS_DATA_BIG_ROUNDS_ABI,
    ROUNDS_STORAGE_READ_ABI,
    TRANSACTION_MANAGER_READ_ABI,
)
from genlayer_py.types import (
    EXECUTION_RESULT_NUMBER_TO_NAME,
    VOTE_TYPE_NUMBER_TO_NAME,
    ExecutionResult,
    VoteType,
)
from genlayer_py.types.transactions import (
    ProtocolTransactionStatus,
    ResolutionAction,
    ResolutionSource,
)
from genlayer_py.chains import localnet

TX_HASH = "0x" + "ab" * 32
CONSENSUS_DATA_ADDRESS = "0x" + "11" * 20
ADDRESS_MANAGER_ADDRESS = "0x" + "22" * 20
BIG_ROUNDS_ADDRESS = "0x" + "33" * 20
TRANSACTION_MANAGER_ADDRESS = "0x" + "44" * 20
ROUNDS_STORAGE_ADDRESS = "0x" + "55" * 20
VALIDATORS = ["0x" + f"{index:040x}" for index in range(1, 4)]
CONSUMED_VALIDATORS = ["0x" + f"{index:040x}" for index in range(4, 6)]


class _Call:
    def __init__(self, value, calls, name, args):
        self._value = value
        self._calls = calls
        self._name = name
        self._args = args

    def call(self, block_identifier=None):
        self._calls.append((self._name, self._args, block_identifier))
        return self._value() if callable(self._value) else self._value


class _Contract:
    def __init__(self, handlers):
        self._handlers = handlers
        self.calls = []
        self.functions = self

    def __getattr__(self, name):
        def function(*args):
            value = self._handlers[name](*args)
            return _Call(value, self.calls, name, args)

        return function


def _light_transaction():
    return (
        1_000,
        "0x" + "66" * 20,
        "0x" + "77" * 20,
        3,
        4,
        900,
        950,
        bytes.fromhex("88" * 32),
        1,
        bytes.fromhex("99" * 32),
        b"",
        b"",
        [],
        0,
        2,
        "0x" + "aa" * 20,
        VALIDATORS[0],
        5,
        bytes.fromhex("ab" * 32),
        (10, 11, 12),
        0,
        (0, 0, 2, 2, 0, 1, 1, len(VALIDATORS)),
        len(CONSUMED_VALIDATORS),
    )


def _client_and_contracts():
    manager = _Contract(
        {
            "getAddressNonZero": lambda name: {
                "ConsensusDataBigRounds": BIG_ROUNDS_ADDRESS,
                "TransactionManager": TRANSACTION_MANAGER_ADDRESS,
                "RoundsStorage": ROUNDS_STORAGE_ADDRESS,
            }[name]
        }
    )
    big_rounds = _Contract(
        {
            "getStoredTransactionDataLight": lambda tx_id: _light_transaction(),
            "getRoundValidatorsPaged": lambda tx_id, round_number, offset, limit: (
                VALIDATORS[offset : offset + limit],
                len(VALIDATORS),
            ),
            "getConsumedValidatorsPaged": lambda tx_id, offset, limit: (
                CONSUMED_VALIDATORS[offset : offset + limit],
                len(CONSUMED_VALIDATORS),
            ),
        }
    )
    transaction_manager = _Contract(
        {
            "getTxExecutionResult": lambda tx_id: 1,
            "getNumOfInitialValidators": lambda tx_id: 5,
        }
    )
    rounds_storage = _Contract(
        {
            "getValidatorVotes": lambda tx_id, round_number: [1, 2, 3],
            "getValidatorVotesHash": lambda tx_id, round_number: [
                bytes.fromhex("01" * 32),
                bytes.fromhex("02" * 32),
                bytes.fromhex("03" * 32),
            ],
            "getValidatorResultHash": lambda tx_id, round_number: [
                bytes.fromhex("11" * 32),
                bytes.fromhex("12" * 32),
                bytes.fromhex("13" * 32),
            ],
        }
    )
    resolution = (
        TX_HASH,
        5,
        6,
        6,
        1,
        bytes(32),
        6,
        0,
        0,
        bytes(32),
        bytes(32),
        0,
        0,
        0,
        0,
        bytes(32),
        0,
        1_000,
    )
    latest_decision = (True, 42)
    consensus_data = _Contract(
        {
            "addressManager": lambda: ADDRESS_MANAGER_ADDRESS,
            "getTransactionLifecycle": lambda tx_id, timestamp: (
                5,
                resolution,
                latest_decision,
                True,
            ),
            "canFinalize": lambda tx_id, timestamp, decision_id: (True, 1_000, 999),
        }
    )
    contracts = {
        CONSENSUS_DATA_ADDRESS: consensus_data,
        ADDRESS_MANAGER_ADDRESS: manager,
        BIG_ROUNDS_ADDRESS: big_rounds,
        TRANSACTION_MANAGER_ADDRESS: transaction_manager,
        ROUNDS_STORAGE_ADDRESS: rounds_storage,
    }
    eth = SimpleNamespace(
        block_number=123,
        contract=lambda address, abi: contracts[address],
    )
    client = SimpleNamespace(
        chain=SimpleNamespace(
            id=4221,
            consensus_data_contract={
                "address": CONSENSUS_DATA_ADDRESS,
                "abi": [],
            },
        ),
        w3=SimpleNamespace(eth=eth),
    )
    return client, contracts


def test_train_transaction_read_composes_light_and_split_array_surfaces(monkeypatch):
    client, contracts = _client_and_contracts()
    monkeypatch.setattr(transaction_actions, "TRANSACTION_ARRAY_PAGE_SIZE", 2)

    result = transaction_actions._read_train_transaction_data(
        client,
        contracts[CONSENSUS_DATA_ADDRESS],
        TX_HASH,
        123,
    )

    (
        tx_data,
        validators,
        votes,
        vote_hashes,
        result_hashes,
        consumed_validators,
        execution_result,
        num_of_initial_validators,
    ) = result
    assert tx_data == _light_transaction()
    assert validators == VALIDATORS
    assert votes == [1, 2, 3]
    assert vote_hashes[0] == bytes.fromhex("01" * 32)
    assert result_hashes[0] == bytes.fromhex("11" * 32)
    assert consumed_validators == CONSUMED_VALIDATORS
    assert execution_result == 1
    assert num_of_initial_validators == 5
    assert [
        call[1][2]
        for call in contracts[BIG_ROUNDS_ADDRESS].calls
        if call[0] == "getRoundValidatorsPaged"
    ] == [0, 2]
    assert [
        call[1][1]
        for call in contracts[BIG_ROUNDS_ADDRESS].calls
        if call[0] == "getConsumedValidatorsPaged"
    ] == [0]
    assert all(
        block == 123
        for contract in contracts.values()
        for _, _, block in contract.calls
    )
    assert not any(
        name == "getTransactionAllData"
        for contract in contracts.values()
        for name, _, _ in contract.calls
    )


def test_get_transaction_exposes_only_stored_consumer_lifecycle(monkeypatch):
    client, contracts = _client_and_contracts()
    monkeypatch.setattr(
        transaction_actions, "_decode_triggered_txs", lambda self, tx: []
    )

    result = transaction_actions.get_transaction(client, TX_HASH)

    assert result["lifecycle"] == {"state": "decided", "outcome": "accepted"}
    assert "status" not in result
    assert "status_name" not in result
    assert "stored_status" not in result
    assert "resolution_action" not in result
    assert "can_finalize" not in result
    assert result["last_round"]["round_validators"] == VALIDATORS
    assert result["last_round"]["validator_votes"] == [1, 2, 3]
    assert result["last_round"]["validator_result_hash"] == [
        "0x" + "11" * 32,
        "0x" + "12" * 32,
        "0x" + "13" * 32,
    ]
    assert result["consumed_validators"] == CONSUMED_VALIDATORS
    assert result["tx_execution_hash"] == "0x" + "99" * 32
    assert result["tx_receipt"] is None
    assert result["tx_execution_result_name"] == "FINISHED_WITH_RETURN"
    assert result["num_of_initial_validators"] == "5"
    assert result["initial_rotations"] == "3"

    lifecycle_calls = contracts[CONSENSUS_DATA_ADDRESS].calls
    assert not any(call[0] == "getTransactionLifecycle" for call in lifecycle_calls)
    assert not any(call[0] == "canFinalize" for call in lifecycle_calls)


def test_advanced_transaction_lifecycle_keeps_projection_explicit():
    client, contracts = _client_and_contracts()

    result = transaction_actions.get_transaction_lifecycle(client, TX_HASH)

    assert result == {
        "stored_status": 5,
        "stored_status_name": ProtocolTransactionStatus.ACCEPTED,
        "projected_status": 6,
        "projected_status_name": ProtocolTransactionStatus.UNDETERMINED,
        "resolution_action": 6,
        "resolution_action_name": ResolutionAction.FINALIZE,
        "resolution_source": 6,
        "resolution_source_name": ResolutionSource.FULL_REVEAL,
        "decision_id": "42",
        "decision_active": True,
        "evaluated_at": 1_000,
    }
    lifecycle_calls = contracts[CONSENSUS_DATA_ADDRESS].calls
    assert ("getTransactionLifecycle", (TX_HASH, 0), 123) in lifecycle_calls
    assert not any(call[0] == "canFinalize" for call in lifecycle_calls)


def test_local_transaction_lifecycle_decodes_the_exact_node_rpc_schema():
    provider = Mock()
    provider.make_request.return_value = {
        "result": {
            "storedStatus": "Accepted",
            "storedStatusCode": 5,
            "projectedStatus": "Undetermined",
            "projectedStatusCode": 6,
            "resolutionAction": "Finalize",
            "resolutionActionCode": 6,
            "resolutionSource": "FullReveal",
            "resolutionSourceCode": 6,
            "decisionId": "42",
            "decisionActive": True,
            "evaluatedAt": 1_000,
        }
    }
    client = SimpleNamespace(
        chain=SimpleNamespace(id=localnet.id),
        provider=provider,
    )

    result = transaction_actions.get_transaction_lifecycle(
        client, bytes.fromhex("ab" * 32), timestamp=999
    )

    assert result == {
        "stored_status": 5,
        "stored_status_name": ProtocolTransactionStatus.ACCEPTED,
        "projected_status": 6,
        "projected_status_name": ProtocolTransactionStatus.UNDETERMINED,
        "resolution_action": 6,
        "resolution_action_name": ResolutionAction.FINALIZE,
        "resolution_source": 6,
        "resolution_source_name": ResolutionSource.FULL_REVEAL,
        "decision_id": "42",
        "decision_active": True,
        "evaluated_at": 1_000,
    }
    provider.make_request.assert_called_once_with(
        method="gen_getTransactionLifecycle",
        params=[{"txId": TX_HASH, "timestamp": 999}],
    )


def test_local_transaction_lifecycle_rejects_code_name_drift():
    provider = Mock()
    provider.make_request.return_value = {
        "result": {
            "storedStatus": "Finalized",
            "storedStatusCode": 5,
            "projectedStatus": "Undetermined",
            "projectedStatusCode": 6,
            "resolutionAction": "Finalize",
            "resolutionActionCode": 6,
            "resolutionSource": "FullReveal",
            "resolutionSourceCode": 6,
            "decisionId": None,
            "decisionActive": False,
            "evaluatedAt": 1_000,
        }
    }
    client = SimpleNamespace(
        chain=SimpleNamespace(id=localnet.id),
        provider=provider,
    )

    with pytest.raises(transaction_actions.GenLayerError, match="storedStatus"):
        transaction_actions.get_transaction_lifecycle(client, TX_HASH)


def test_packaged_consensus_abis_expose_only_the_train_lifecycle_signature():
    for abi in (CONSENSUS_DATA_ABI, CONSENSUS_DATA_ABI_V06):
        functions = {
            entry["name"]: entry for entry in abi if entry.get("type") == "function"
        }
        assert "getTransactionData" not in functions
        assert "getStoredTransactionData" in functions
        assert "getTransactionLifecycle" in functions
        assert len(functions["canFinalize"]["inputs"]) == 3
        transaction_components = functions["getTransactionAllData"]["outputs"][0][
            "components"
        ]
        assert transaction_components[2]["name"] == "status"
        assert transaction_components[-1]["name"] == "queueContext"

    big_round_functions = {
        entry["name"]
        for entry in CONSENSUS_DATA_BIG_ROUNDS_ABI
        if entry.get("type") == "function"
    }
    assert big_round_functions == {
        "getStoredTransactionDataLight",
        "getRoundValidatorsPaged",
        "getConsumedValidatorsPaged",
    }

    rounds_storage_functions = {
        entry["name"]
        for entry in ROUNDS_STORAGE_READ_ABI
        if entry.get("type") == "function"
    }
    assert rounds_storage_functions == {
        "getValidatorVotes",
        "getValidatorVotesHash",
        "getValidatorResultHash",
    }

    transaction_manager_functions = {
        entry["name"]
        for entry in TRANSACTION_MANAGER_READ_ABI
        if entry.get("type") == "function"
    }
    assert transaction_manager_functions == {
        "getTxExecutionResult",
        "getNumOfInitialValidators",
    }


def test_train_vote_and_execution_enums_cover_every_contract_ordinal():
    expected = {
        "0": VoteType.NOT_VOTED,
        "1": VoteType.FINISHED_WITH_RETURN,
        "2": VoteType.FINISHED_WITH_ERROR,
        "3": VoteType.TIMEOUT,
        "4": VoteType.NONDET_DISAGREE,
        "5": VoteType.DETERMINISTIC_VIOLATION,
    }
    assert VOTE_TYPE_NUMBER_TO_NAME == expected
    assert EXECUTION_RESULT_NUMBER_TO_NAME == {
        ordinal: ExecutionResult(member.value) for ordinal, member in expected.items()
    }
