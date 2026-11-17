"""
Smoke tests to verify Bradbury testnet chain configuration and RPC connectivity.
"""

import pytest
from web3 import Web3

from genlayer_py.chains.testnet_bradbury import (
    testnet_bradbury,
    TESTNET_JSON_RPC_URL,
    CONSENSUS_MAIN_CONTRACT,
    CONSENSUS_DATA_CONTRACT,
)
from genlayer_py.types.transactions import GenLayerRawTransaction
from genlayer_py.client import create_client


class TestBradburyConfig:
    """Verify Bradbury chain configuration values."""

    def test_rpc_url(self):
        assert TESTNET_JSON_RPC_URL == "https://rpc.testnet-chain.genlayer.com"

    def test_chain_id(self):
        assert testnet_bradbury.id == 4221

    def test_consensus_main_address(self):
        assert (
            CONSENSUS_MAIN_CONTRACT["address"]
            == "0x2E2766cbc3E5e61Ce93bBcdCBb3eAcB82082A019"
        )

    def test_consensus_data_address(self):
        assert (
            CONSENSUS_DATA_CONTRACT["address"]
            == "0xc5FA6f82BEe53598825d6edf7E3e24613082c75B"
        )


@pytest.mark.testnet
class TestBradburyConnectivity:
    """Verify RPC connectivity to Bradbury testnet.

    Uses create_client() rather than a stock Web3.HTTPProvider: the
    Bradbury RPC rejects JSON-RPC requests with id=0 as an "Invalid
    Request" (server-side go-playground/validator `required` tag treats
    int zero as unset). Stock web3.py's HTTPProvider starts its request
    counter at 0, so the first probe on any fresh Web3() fails. The SDK
    provider (GenLayerProvider) ids requests by timestamp and is the
    path real consumers take."""

    def test_rpc_connects(self):
        # Success of any RPC call is what we actually care about;
        # GenLayerProvider doesn't implement the BaseProvider.is_connected
        # liveness check web3.py calls from Web3().is_connected.
        client = create_client(chain=testnet_bradbury)
        assert client.chain_id == 4221

    def test_chain_id_matches(self):
        client = create_client(chain=testnet_bradbury)
        assert client.chain_id == 4221

    def test_block_number_positive(self):
        client = create_client(chain=testnet_bradbury)
        assert client.block_number > 0


@pytest.mark.testnet
class TestBradburyConsensusContract:
    """Verify the Bradbury consensus main contract ABI matches the deployed contract."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI_V06

        client = create_client(chain=testnet_bradbury)
        self.w3 = client
        self.contract = client.contract(
            address=Web3.to_checksum_address(CONSENSUS_MAIN_CONTRACT["address"]),
            abi=CONSENSUS_MAIN_ABI_V06,
        )

    def test_get_address_manager(self):
        """Call getAddressManager() — zero-arg view function."""
        result = self.contract.functions.getAddressManager().call()
        assert Web3.is_address(result)
        assert result != "0x0000000000000000000000000000000000000000"

    def test_is_ghost_contract_zero_address(self):
        """Call isGhostContract with the zero address."""
        result = self.contract.functions.isGhostContract(
            "0x0000000000000000000000000000000000000000"
        ).call()
        assert isinstance(result, bool)

    def test_get_pending_transaction_value_zero(self):
        """Call getPendingTransactionValue with a zero txId."""
        result = self.contract.functions.getPendingTransactionValue(b"\x00" * 32).call()
        assert isinstance(result, int)
        assert result == 0


@pytest.mark.testnet
class TestBradburyTransactionRead:
    """Verify the transaction read returns txExecutionResult."""

    def test_get_transaction_returns_execution_result(self):
        """Use the actual SDK client to fetch a known finalized tx and verify tx_execution_result."""
        client = create_client(chain=testnet_bradbury)
        tx = client.get_transaction(
            transaction_hash=bytes.fromhex(
                "1ec24f069f8dd00c63e822d1fe969681d9199d5f2268470d9e8a8ed191055564"
            )
        )
        assert tx["tx_execution_result"] in [0, 1, 2, 3, 4, 5]
        assert tx["tx_execution_result_name"] in [
            "NOT_VOTED",
            "FINISHED_WITH_RETURN",
            "FINISHED_WITH_ERROR",
            "TIMEOUT",
            "NONDET_DISAGREE",
            "DETERMINISTIC_VIOLATION",
        ]
        assert tx["lifecycle"]["state"] in {
            "processing",
            "decided",
            "finalized",
            "canceled",
        }
        assert tx["result_name"] is not None

    def test_get_transaction_includes_messages(self):
        """Verify messages array is present on decoded transaction."""
        client = create_client(chain=testnet_bradbury)
        tx = client.get_transaction(
            transaction_hash=bytes.fromhex(
                "1ec24f069f8dd00c63e822d1fe969681d9199d5f2268470d9e8a8ed191055564"
            )
        )
        assert "messages" in tx
        assert isinstance(tx["messages"], list)

    def test_get_triggered_transaction_ids_returns_list(self):
        """Verify get_triggered_transaction_ids returns a list."""
        client = create_client(chain=testnet_bradbury)
        result = client.get_triggered_transaction_ids(
            transaction_hash=bytes.fromhex(
                "1ec24f069f8dd00c63e822d1fe969681d9199d5f2268470d9e8a8ed191055564"
            )
        )
        assert isinstance(result, list)
