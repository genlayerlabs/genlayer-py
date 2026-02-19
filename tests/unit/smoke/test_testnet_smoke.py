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


@pytest.mark.testnet
class TestConsensusContractReadOnly:
    """Verify the consensus main contract ABI matches the deployed contract."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI

        self.w3 = Web3(Web3.HTTPProvider(TESTNET_JSON_RPC_URL))
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONSENSUS_MAIN_CONTRACT["address"]),
            abi=CONSENSUS_MAIN_ABI,
        )

    def test_get_address_manager(self):
        """Call getAddressManager() — zero-arg view function."""
        result = self.contract.functions.getAddressManager().call()
        # Should return a valid non-zero address
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
class TestEncoderDecoderRoundTrip:
    """Verify encode/decode round-trip for addTransaction data."""

    def test_round_trip_call(self):
        from genlayer_py.consensus.consensus_main.encoder import (
            encode_add_transaction_data,
            encode_tx_data_call,
        )
        from genlayer_py.consensus.consensus_main.decoder import (
            decode_add_transaction_data,
        )

        sender = "0xABcdEFABcdEFabcdEfAbCdefAbCdEFaBcDEFabCD"
        recipient = "0x1111111111111111111111111111111111111111"
        num_validators = 7
        max_rotations = 2

        tx_data = encode_tx_data_call(
            function_name="my_method",
            leader_only=True,
            args=["hello"],
            kwargs={"key": "value"},
        )

        encoded = encode_add_transaction_data(
            sender_address=sender,
            recipient_address=recipient,
            num_of_initial_validators=num_validators,
            max_rotations=max_rotations,
            tx_data=tx_data.hex() if isinstance(tx_data, bytes) else tx_data,
        )

        decoded = decode_add_transaction_data(encoded)
        assert decoded["sender_address"].lower() == sender.lower()
        assert decoded["recipient_address"].lower() == recipient.lower()
        assert decoded["num_of_initial_validators"] == num_validators
        assert decoded["max_rotations"] == max_rotations
        assert decoded["tx_data"]["decoded"]["call_data"]["method"] == "my_method"
        assert decoded["tx_data"]["decoded"]["leader_only"] is True
        assert decoded["tx_data"]["decoded"]["type"] == "call"

    def test_round_trip_deploy(self):
        from genlayer_py.consensus.consensus_main.encoder import (
            encode_add_transaction_data,
            encode_tx_data_deploy,
        )
        from genlayer_py.consensus.consensus_main.decoder import (
            decode_add_transaction_data,
        )

        sender = "0xABcdEFABcdEFabcdEfAbCdefAbCdEFaBcDEFabCD"
        recipient = "0x0000000000000000000000000000000000000000"
        code = "print('hello world')"

        tx_data = encode_tx_data_deploy(
            code=code,
            leader_only=False,
            args=[],
            kwargs={},
        )

        encoded = encode_add_transaction_data(
            sender_address=sender,
            recipient_address=recipient,
            num_of_initial_validators=5,
            max_rotations=3,
            tx_data=tx_data,
        )

        decoded = decode_add_transaction_data(encoded)
        assert decoded["sender_address"].lower() == sender.lower()
        assert decoded["recipient_address"].lower() == recipient.lower()
        assert decoded["num_of_initial_validators"] == 5
        assert decoded["max_rotations"] == 3
        assert (
            Web3.to_bytes(hexstr=decoded["tx_data"]["decoded"]["code"]).decode("utf-8")
            == code
        )
        assert decoded["tx_data"]["decoded"]["leader_only"] is False
        assert decoded["tx_data"]["decoded"]["type"] == "deploy"
