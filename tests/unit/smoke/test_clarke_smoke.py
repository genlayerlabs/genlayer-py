"""
Smoke tests to verify Clarke testnet chain configuration and RPC connectivity.
"""

import pytest
from web3 import Web3

from genlayer_py.chains.testnet_clarke import (
    testnet_clarke,
    CONSENSUS_MAIN_CONTRACT,
)
from genlayer_py.client import create_client

CLARKE_ADDRESS_MANAGER = "0xA79dA7c238905fD0F10298cD579B0733ad1B1d0E"


@pytest.mark.testnet
class TestClarkeConnectivity:
    def test_chain_id_matches(self):
        client = create_client(chain=testnet_clarke)
        assert client.chain_id == testnet_clarke.id

    def test_block_number_positive(self):
        client = create_client(chain=testnet_clarke)
        assert client.block_number > 0


@pytest.mark.testnet
class TestClarkeConsensusContract:
    def test_consensus_main_belongs_to_the_clarke_deployment(self):
        client = create_client(chain=testnet_clarke)
        contract = client.contract(
            address=Web3.to_checksum_address(CONSENSUS_MAIN_CONTRACT["address"]),
            abi=CONSENSUS_MAIN_CONTRACT["abi"],
        )
        assert contract.functions.getAddressManager().call() == CLARKE_ADDRESS_MANAGER
