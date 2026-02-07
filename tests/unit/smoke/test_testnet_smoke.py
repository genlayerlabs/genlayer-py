"""
Smoke tests to verify testnet chain configuration and RPC connectivity.
"""

import pytest
from web3 import Web3

from genlayer_py.chains.testnet_asimov import (
    testnet_asimov,
    TESTNET_JSON_RPC_URL,
    CONSENSUS_MAIN_CONTRACT,
    CONSENSUS_DATA_CONTRACT,
)


class TestTestnetConfig:
    """Verify testnet chain configuration values."""

    def test_rpc_url(self):
        assert TESTNET_JSON_RPC_URL == "https://zksync-os-testnet-genlayer.zksync.dev"

    def test_chain_id(self):
        assert testnet_asimov.id == 4221

    def test_consensus_main_address(self):
        assert (
            CONSENSUS_MAIN_CONTRACT["address"]
            == "0x6CAFF6769d70824745AD895663409DC70aB5B28E"
        )

    def test_consensus_data_address(self):
        assert (
            CONSENSUS_DATA_CONTRACT["address"]
            == "0x0D9d1d74d72Fa5eB94bcf746C8FCcb312a722c9B"
        )


@pytest.mark.testnet
class TestTestnetConnectivity:
    """Verify RPC connectivity to testnet. Run with: pytest -m testnet"""

    def test_rpc_connects(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.is_connected()

    def test_chain_id_matches(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.eth.chain_id == 4221

    def test_block_number_positive(self):
        w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        assert w3.eth.block_number > 0
