import genlayer_py
import genlayer_py.types as public_types
import pytest
from types import SimpleNamespace

from genlayer_py.chains import localnet
from genlayer_py.transactions.actions import get_transaction
from genlayer_py.types.transactions import (
    CanceledTransactionLifecycle,
    DecidedTransactionLifecycle,
    FinalizedTransactionLifecycle,
    ProcessingTransactionLifecycle,
    PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME,
    ProtocolTransactionStatus,
    ResolutionAction,
    ResolutionSource,
    transaction_lifecycle_from_protocol_status,
    transaction_outcome_from_protocol_result,
)

EXPECTED_LIFECYCLES = {
    0: {"state": "processing", "phase": "uninitialized"},
    1: {"state": "processing", "phase": "pending"},
    2: {"state": "processing", "phase": "proposing"},
    3: {"state": "processing", "phase": "committing"},
    4: {"state": "processing", "phase": "revealing"},
    5: {"state": "decided", "outcome": "accepted"},
    6: {"state": "decided", "outcome": "undetermined"},
    7: {"state": "finalized"},
    8: {"state": "canceled"},
    9: {"state": "processing", "phase": "appeal_revealing"},
    10: {"state": "processing", "phase": "appeal_committing"},
    11: {"state": "decided", "outcome": "validators_timeout"},
    12: {"state": "decided", "outcome": "leader_timeout"},
    13: {"state": "processing", "phase": "leader_revealing"},
}


@pytest.mark.parametrize("protocol_status, expected", EXPECTED_LIFECYCLES.items())
def test_every_protocol_status_has_one_public_lifecycle(protocol_status, expected):
    assert transaction_lifecycle_from_protocol_status(protocol_status) == expected
    assert transaction_lifecycle_from_protocol_status(str(protocol_status)) == expected
    assert (
        transaction_lifecycle_from_protocol_status(
            PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[str(protocol_status)]
        )
        == expected
    )


@pytest.mark.parametrize("value", [-1, 14, "unknown"])
def test_unknown_or_removed_protocol_status_is_rejected(value):
    with pytest.raises(ValueError, match="Unknown protocol transaction status"):
        transaction_lifecycle_from_protocol_status(value)


def test_public_lifecycle_is_a_discriminated_union():
    assert ProcessingTransactionLifecycle.__required_keys__ == {"state", "phase"}
    assert DecidedTransactionLifecycle.__required_keys__ == {"state", "outcome"}
    assert FinalizedTransactionLifecycle.__required_keys__ == {"state"}
    assert FinalizedTransactionLifecycle.__optional_keys__ == {"outcome"}
    assert CanceledTransactionLifecycle.__required_keys__ == {"state"}


@pytest.mark.parametrize(
    "protocol_result, expected",
    [
        (0, None),
        (1, "accepted"),
        (2, "undetermined"),
        (3, "validators_timeout"),
        (4, "undetermined"),
        (5, "undetermined"),
    ],
)
def test_finalized_outcome_is_added_only_when_the_result_proves_it(
    protocol_result, expected
):
    assert transaction_outcome_from_protocol_result(protocol_result) == expected


def test_raw_protocol_types_are_advanced_only():
    assert not hasattr(genlayer_py, "ResolutionAction")
    assert not hasattr(genlayer_py, "ProtocolTransactionStatus")
    assert not hasattr(public_types, "ResolutionAction")
    assert not hasattr(public_types, "ResolutionSource")
    assert not hasattr(public_types, "ProtocolTransactionStatus")
    assert len(ProtocolTransactionStatus) == 14
    assert len(ResolutionSource) == 12
    assert ResolutionAction.FINALIZE.value == "Finalize"


@pytest.mark.parametrize(
    "raw_transaction, expected",
    [
        (
            {"status": "ACTIVATED", "data": None},
            {"state": "processing", "phase": "pending"},
        ),
        (
            {
                "status": "FINALIZED",
                "result_name": "MAJORITY_AGREE",
                "data": None,
            },
            {"state": "finalized", "outcome": "accepted"},
        ),
    ],
)
def test_local_transaction_runtime_exposes_only_public_lifecycle(
    raw_transaction, expected
):
    client = SimpleNamespace(
        chain=SimpleNamespace(id=localnet.id),
        provider=SimpleNamespace(
            make_request=lambda method, params: {"result": dict(raw_transaction)}
        ),
    )

    transaction = get_transaction(client, "0x" + "ab" * 32)

    assert transaction["lifecycle"] == expected
    assert "status" not in transaction
    assert "status_name" not in transaction
