from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from genlayer_py.chains.actions import initialize_consensus_smart_contract
from genlayer_py.chains.localnet import localnet
from genlayer_py.exceptions import GenLayerError


def _make_client(chain_id, consensus_main_contract):
    provider = Mock()
    chain = SimpleNamespace(
        id=chain_id,
        consensus_main_contract=consensus_main_contract,
    )
    return SimpleNamespace(chain=chain, provider=provider)


def test_initialize_consensus_skips_rpc_fetch_for_non_local_when_static_contract_exists():
    client = _make_client(
        chain_id=1,
        consensus_main_contract={"address": "0x1", "abi": [{"type": "function"}]},
    )

    initialize_consensus_smart_contract(self=client)

    client.provider.make_request.assert_not_called()


def test_initialize_consensus_refreshes_runtime_contract_for_local_chain():
    client = _make_client(
        chain_id=localnet.id,
        consensus_main_contract={"address": "0x1", "abi": [{"type": "function"}]},
    )
    rpc_contract = {"address": "0x2", "abi": [{"type": "function", "name": "foo"}]}
    client.provider.make_request.return_value = {"result": rpc_contract}

    initialize_consensus_smart_contract(self=client)

    client.provider.make_request.assert_called_once_with(
        method="sim_getConsensusContract", params=["ConsensusMain"]
    )
    assert client.chain.consensus_main_contract == rpc_contract
    assert getattr(client.chain, "__consensus_abi_fetched_from_rpc") is True


def test_initialize_consensus_falls_back_to_static_contract_on_local_rpc_failure():
    static_contract = {"address": "0x1", "abi": [{"type": "function"}]}
    client = _make_client(
        chain_id=localnet.id,
        consensus_main_contract=static_contract,
    )
    client.provider.make_request.side_effect = GenLayerError("rpc unavailable")

    initialize_consensus_smart_contract(self=client)

    assert client.chain.consensus_main_contract == static_contract
    assert getattr(client.chain, "__consensus_abi_fetched_from_rpc") is False


def test_initialize_consensus_raises_when_rpc_fails_and_no_static_contract():
    client = _make_client(
        chain_id=localnet.id,
        consensus_main_contract=None,
    )
    client.provider.make_request.side_effect = GenLayerError("rpc unavailable")

    with pytest.raises(GenLayerError, match="rpc unavailable"):
        initialize_consensus_smart_contract(self=client)
