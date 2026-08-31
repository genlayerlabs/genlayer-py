import pytest
from unittest.mock import patch
from genlayer_py.transactions.actions import (
    wait_for_decision,
    wait_for_finalization,
    wait_for_transaction_receipt,
    _simplify_transaction_receipt,
    is_successful,
)
from genlayer_py.types import ExecutionResult
from genlayer_py.exceptions import GenLayerError

TX_HASH = "0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6"


def _transaction(lifecycle, **extra):
    return {"hash": TX_HASH, "lifecycle": lifecycle, **extra}


class TestTransactionWaits:
    @pytest.mark.parametrize(
        "lifecycle",
        [
            {"state": "decided", "outcome": "accepted"},
            {"state": "decided", "outcome": "undetermined"},
            {"state": "decided", "outcome": "validators_timeout"},
            {"state": "decided", "outcome": "leader_timeout"},
            {"state": "finalized"},
            {"state": "canceled"},
        ],
    )
    def test_wait_for_decision_uses_materialized_lifecycle(
        self, mock_client, lifecycle
    ):
        transaction = _transaction(lifecycle)
        mock_client.get_transaction.return_value = transaction

        assert (
            wait_for_decision(mock_client, TX_HASH, full_transaction=True)
            == transaction
        )

    def test_wait_for_finalization_ignores_nonfinal_stored_state(self, mock_client):
        processing = _transaction({"state": "processing", "phase": "pending"})
        decided = _transaction({"state": "decided", "outcome": "accepted"})
        finalized = _transaction({"state": "finalized"})
        mock_client.get_transaction.side_effect = [processing, decided, finalized]

        with patch("time.sleep") as sleep:
            result = wait_for_finalization(
                mock_client, TX_HASH, interval=100, full_transaction=True
            )

        assert result == finalized
        assert mock_client.get_transaction.call_count == 3
        assert sleep.call_count == 2
        sleep.assert_called_with(0.1)

    def test_receipt_default_waits_for_decision_and_simplifies(self, mock_client):
        transaction = _transaction({"state": "decided", "outcome": "accepted"})
        mock_client.get_transaction.return_value = transaction
        simplified = {"hash": TX_HASH, "lifecycle": transaction["lifecycle"]}

        with patch(
            "genlayer_py.transactions.actions._simplify_transaction_receipt",
            return_value=simplified,
        ) as simplify:
            result = wait_for_transaction_receipt(mock_client, TX_HASH)

        assert result == simplified
        simplify.assert_called_once_with(transaction)

    def test_receipt_can_wait_for_finalization(self, mock_client):
        transaction = _transaction({"state": "finalized"})
        mock_client.get_transaction.return_value = transaction

        assert (
            wait_for_transaction_receipt(
                mock_client,
                TX_HASH,
                wait_until="finalized",
                full_transaction=True,
            )
            == transaction
        )

    def test_processing_timeout_reports_public_phase(self, mock_client):
        mock_client.get_transaction.return_value = _transaction(
            {"state": "processing", "phase": "leader_revealing"}
        )

        with pytest.raises(
            GenLayerError, match="Last observed lifecycle state: 'processing'"
        ):
            wait_for_decision(mock_client, TX_HASH, retries=1, interval=1)

    def test_wait_for_finalization_fails_fast_when_canceled(self, mock_client):
        mock_client.get_transaction.return_value = _transaction({"state": "canceled"})

        with pytest.raises(GenLayerError, match="canceled before finalization"):
            wait_for_finalization(mock_client, TX_HASH)

        mock_client.get_transaction.assert_called_once()

    def test_nonexistent_transaction(self, mock_client):
        mock_client.get_transaction.return_value = None

        with pytest.raises(GenLayerError, match="Transaction .* not found"):
            wait_for_decision(mock_client, TX_HASH)

    def test_invalid_lifecycle_is_rejected(self, mock_client):
        mock_client.get_transaction.return_value = {"hash": TX_HASH}

        with pytest.raises(GenLayerError, match="has no valid lifecycle"):
            wait_for_decision(mock_client, TX_HASH)

    def test_invalid_receipt_wait_target_is_rejected(self, mock_client):
        with pytest.raises(ValueError, match="wait_until"):
            wait_for_transaction_receipt(mock_client, TX_HASH, wait_until="projected")


class TestIsSuccessful:
    def test_truth_table(self):
        assert is_successful(
            {
                "lifecycle": {"state": "decided", "outcome": "accepted"},
                "tx_execution_result": "1",
            }
        )
        assert not is_successful(
            {
                "lifecycle": {"state": "decided", "outcome": "undetermined"},
                "tx_execution_result": "1",
            }
        )
        assert not is_successful(
            {
                "lifecycle": {"state": "decided", "outcome": "accepted"},
                "tx_execution_result": "2",
            }
        )
        assert is_successful(
            {
                "lifecycle": {"state": "finalized"},
                "tx_execution_result_name": ExecutionResult.FINISHED_WITH_RETURN,
            }
        )
        assert is_successful(
            {
                "lifecycle": {"state": "finalized", "outcome": "accepted"},
                "tx_execution_result_name": ExecutionResult.FINISHED_WITH_RETURN,
            }
        )
        assert not is_successful(
            {
                "lifecycle": {"state": "finalized", "outcome": "undetermined"},
                "tx_execution_result_name": ExecutionResult.FINISHED_WITH_RETURN,
            }
        )


class TestSimplifyTransactionReceipt:
    """Test suite for _simplify_transaction_receipt function"""

    def test_simplify_removes_unwanted_fields(self, full_write_transaction_data):
        """Test that unwanted fields are removed"""
        result = _simplify_transaction_receipt(full_write_transaction_data)

        # These fields should be removed
        unwanted_fields = [
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
            "timestamp_awaiting_finalization",
        ]

        for field in unwanted_fields:
            assert field not in result, f"Field '{field}' should have been removed"

    def test_simplify_preserves_essential_fields(self, full_write_transaction_data):
        """Test that essential fields are preserved"""
        result = _simplify_transaction_receipt(full_write_transaction_data)

        # These fields should be preserved
        essential_fields = [
            "hash",
            "lifecycle",
            "from_address",
            "to_address",
            "value",
            "gaslimit",
            "nonce",
            "created_at",
        ]

        for field in essential_fields:
            assert field in result, f"Essential field '{field}' should be preserved"
            assert result[field] == full_write_transaction_data[field]

    def test_simplify_processes_consensus_data(
        self, full_write_transaction_data, simplified_write_transaction_data
    ):
        """Test that consensus_data is properly processed"""
        result = _simplify_transaction_receipt(full_write_transaction_data)
        assert result == simplified_write_transaction_data

    def test_simplify_handles_contract_snapshot(self, full_write_transaction_data):
        """Test that contract_snapshot is simplified"""
        result = _simplify_transaction_receipt(full_write_transaction_data)

        assert "contract_snapshot" in result
        snapshot = result["contract_snapshot"]

        # contract_address should be preserved
        assert (
            snapshot["contract_address"] == "0xf72aa51B6350C18966923073d3609e1356a3fbBA"
        )

        # contract_code and states should be removed
        assert "contract_code" not in snapshot
        assert "states" not in snapshot

    def test_simplify_handles_various_value_types(self):
        """Test handling of various value types including empty and falsy values"""
        data = {
            "hash": "0x123",
            "empty_list": [],
            "empty_string": "",
            "null_value": None,
            "zero_value": 0,
            "false_value": False,
            "nested_empty": {
                "will_be_removed": []  # Empty nested structures are filtered out
            },
        }

        result = _simplify_transaction_receipt(data)

        # Simple fields are preserved regardless of value
        assert result["hash"] == "0x123"
        assert result["empty_string"] == ""
        assert result["null_value"] is None
        assert result["zero_value"] == 0
        assert result["false_value"] == False

        # Note: The current implementation filters out empty lists and dicts
        # due to the `if result:` check for nested structures
        assert "empty_list" not in result  # Empty list is filtered out
        assert (
            "nested_empty" not in result
        )  # Nested object with only empty values is filtered

    def test_simplify_nested_filtering(self):
        """Test that filtering works recursively on nested objects"""
        data = {
            "hash": "0x123",
            "nested": {
                "raw": [1, 2, 3],  # Should be removed
                "readable": "keep this",  # Should be kept
                "deeper": {
                    "contract_state": "remove",  # Should be removed
                    "important": "keep",  # Should be kept
                },
            },
        }

        result = _simplify_transaction_receipt(data)

        assert "nested" in result
        assert "raw" not in result["nested"]
        assert result["nested"]["readable"] == "keep this"
        assert "contract_state" not in result["nested"]["deeper"]
        assert result["nested"]["deeper"]["important"] == "keep"
