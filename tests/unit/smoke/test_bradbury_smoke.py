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


class TestBradburyConfig:
    """Verify Bradbury chain configuration values."""

    def test_rpc_url(self):
        assert TESTNET_JSON_RPC_URL == "https://rpc-bradbury.genlayer.com"

    def test_chain_id(self):
        assert testnet_bradbury.id == 4221

    def test_consensus_main_address(self):
        assert (
            CONSENSUS_MAIN_CONTRACT["address"]
            == "0x0112Bf6e83497965A5fdD6Dad1E447a6E004271D"
        )

    def test_consensus_data_address(self):
        assert (
            CONSENSUS_DATA_CONTRACT["address"]
            == "0x85D7bf947A512Fc640C75327A780c90847267697"
        )


@pytest.mark.testnet
class TestBradburyConnectivity:
    """Verify RPC connectivity to Bradbury testnet."""

    def test_rpc_connects(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.is_connected()

    def test_chain_id_matches(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.eth.chain_id == 4221

    def test_block_number_positive(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.eth.block_number > 0


@pytest.mark.testnet
class TestBradburyConsensusContract:
    """Verify the Bradbury consensus main contract ABI matches the deployed contract."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI_V06

        self.w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        self.contract = self.w3.eth.contract(
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
