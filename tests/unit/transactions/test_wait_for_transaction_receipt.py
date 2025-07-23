import pytest
from unittest.mock import patch
from genlayer_py.transactions.actions import (
    wait_for_transaction_receipt,
    _simplify_transaction_receipt,
)
from genlayer_py.types import TransactionStatus
from genlayer_py.exceptions import GenLayerError


class TestWaitForTransactionReceipt:
    """Test suite for wait_for_transaction_receipt function"""

    def test_wait_for_finalized_transaction_success(
        self, mock_client, full_write_transaction_data
    ):
        """Test successful wait for finalized transaction"""
        mock_client.get_transaction.return_value = full_write_transaction_data

        result = wait_for_transaction_receipt(
            self=mock_client,
            transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
            status=TransactionStatus.FINALIZED,
            full_transaction=True,
        )

        assert result == full_write_transaction_data
        mock_client.get_transaction.assert_called_once()

    def test_wait_for_accepted_transaction_with_finalized_status(
        self, mock_client, full_write_transaction_data
    ):
        """Test that ACCEPTED status accepts FINALIZED transactions"""
        mock_client.get_transaction.return_value = full_write_transaction_data

        result = wait_for_transaction_receipt(
            self=mock_client,
            transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
            status=TransactionStatus.ACCEPTED,  # Requesting ACCEPTED
            full_transaction=True,
        )

        # Should accept FINALIZED (status 7) when requesting ACCEPTED
        assert result == full_write_transaction_data

    def test_wait_for_transaction_with_simplified_receipt(
        self, mock_client, full_write_transaction_data
    ):
        """Test wait for transaction with simplified receipt (full_transaction=False)"""
        mock_client.get_transaction.return_value = full_write_transaction_data

        with patch(
            "genlayer_py.transactions.actions._simplify_transaction_receipt"
        ) as mock_simplify:
            simplified_data = {"hash": "0x123", "status": 7, "simplified": True}
            mock_simplify.return_value = simplified_data

            result = wait_for_transaction_receipt(
                self=mock_client,
                transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
                full_transaction=False,
            )

            mock_simplify.assert_called_once_with(full_write_transaction_data)
            assert result == simplified_data

    def test_wait_for_transaction_timeout(self, mock_client, pending_transaction_data):
        """Test timeout when transaction doesn't reach desired status"""
        mock_client.get_transaction.return_value = pending_transaction_data

        with pytest.raises(GenLayerError, match="did not reach desired status"):
            wait_for_transaction_receipt(
                self=mock_client,
                transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
                retries=2,
                interval=1,  # 1ms for fast test
            )

        # Should have tried 2 times
        assert mock_client.get_transaction.call_count == 2

    def test_wait_for_nonexistent_transaction(self, mock_client):
        """Test error when transaction doesn't exist"""
        mock_client.get_transaction.return_value = None

        with pytest.raises(GenLayerError, match="Transaction .* not found"):
            wait_for_transaction_receipt(
                self=mock_client,
                transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
            )

    @patch("time.sleep")
    def test_wait_for_transaction_with_retry_logic(
        self,
        mock_sleep,
        mock_client,
        pending_transaction_data,
        full_write_transaction_data,
    ):
        """Test retry logic with eventual success"""
        # First two calls return pending, third returns finalized
        mock_client.get_transaction.side_effect = [
            pending_transaction_data,
            pending_transaction_data,
            full_write_transaction_data,
        ]

        result = wait_for_transaction_receipt(
            self=mock_client,
            transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
            interval=100,  # 100ms
            full_transaction=True,
        )

        assert result == full_write_transaction_data
        assert mock_client.get_transaction.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.1)  # 100ms / 1000

    def test_wait_for_transaction_with_custom_parameters(
        self, mock_client, full_write_transaction_data
    ):
        """Test with custom interval and retries"""
        mock_client.get_transaction.return_value = full_write_transaction_data

        result = wait_for_transaction_receipt(
            self=mock_client,
            transaction_hash="0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
            status=TransactionStatus.FINALIZED,
            interval=500,
            retries=10,
            full_transaction=True,
        )

        assert result == full_write_transaction_data


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
            "status",
            "status_name",
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
