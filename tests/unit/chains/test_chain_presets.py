import genlayer_py

from genlayer_py.chains import __all__ as chain_exports
from genlayer_py.chains.localnet import localnet
from genlayer_py.chains.studio_devnet import (
    STUDIO_DEVNET_EXPLORER_URL,
    STUDIO_DEVNET_JSON_RPC_URL,
    studio_devnet,
)
from genlayer_py.chains.studionet import studionet
from genlayer_py.chains.testnet_asimov import testnet_asimov
from genlayer_py.chains.utils import is_studio_chain


def test_localnet_uses_the_canonical_local_studio_chain_id():
    assert localnet.id == 61127
    assert localnet.rpc_urls == {
        "default": {"http": ["http://127.0.0.1:4000/api"]}
    }


def test_studio_devnet_is_exported_with_canonical_preview_coordinates():
    assert "studio_devnet" in chain_exports
    assert genlayer_py.studio_devnet is studio_devnet
    assert studio_devnet.id == 61997
    assert studio_devnet.name == "GenLayer Studio Devnet"
    assert studio_devnet.rpc_urls == {
        "default": {"http": ["https://studio-dev.genlayer.com/api"]}
    }
    assert STUDIO_DEVNET_JSON_RPC_URL == "https://studio-dev.genlayer.com/api"
    assert STUDIO_DEVNET_EXPLORER_URL == "https://explorer-studio-dev.genlayer.com"
    assert studio_devnet.block_explorers == {
        "default": {
            "name": "GenLayer Explorer",
            "url": "https://explorer-studio-dev.genlayer.com",
        }
    }
    assert studio_devnet.consensus_main_contract == studionet.consensus_main_contract
    assert studio_devnet.consensus_data_contract == studionet.consensus_data_contract
    assert studio_devnet.consensus_main_contract is not studionet.consensus_main_contract
    assert studio_devnet.consensus_data_contract is not studionet.consensus_data_contract


def test_stable_studionet_coordinates_do_not_drift_with_preview_preset():
    assert studionet.id == 61999
    assert studionet.rpc_urls == {
        "default": {"http": ["https://studio.genlayer.com/api"]}
    }


def test_studio_chain_classification_includes_preview_but_not_public_testnet():
    assert is_studio_chain(localnet)
    assert is_studio_chain(studionet)
    assert is_studio_chain(studio_devnet)
    assert not is_studio_chain(testnet_asimov)


def test_studio_presets_have_distinct_chain_ids():
    assert len({localnet.id, studio_devnet.id, studionet.id}) == 3
