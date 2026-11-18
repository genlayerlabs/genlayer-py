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
from genlayer_py.chains.testnet_bradbury import testnet_bradbury
from genlayer_py.staking.abi import STAKING_ABI
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


def test_bradbury_targets_the_phase_2_deployment():
    assert testnet_bradbury.id == 4221
    assert not is_studio_chain(testnet_bradbury)
    assert testnet_bradbury.rpc_urls == {
        "default": {"http": ["https://rpc.testnet-chain.genlayer.com"]}
    }
    assert (
        testnet_bradbury.block_explorers["default"]["url"]
        == "https://scan.testnet-chain.genlayer.com"
    )
    addresses = {
        field: getattr(testnet_bradbury, field)["address"]
        for field in (
            "consensus_main_contract",
            "consensus_data_contract",
            "fee_manager_contract",
            "rounds_storage_contract",
            "appeals_contract",
            "staking_contract",
        )
    }
    assert addresses == {
        "consensus_main_contract": "0x2E2766cbc3E5e61Ce93bBcdCBb3eAcB82082A019",
        "consensus_data_contract": "0xc5FA6f82BEe53598825d6edf7E3e24613082c75B",
        "fee_manager_contract": "0x7678587A847712f2A96082AC07883A88D0fc7245",
        "rounds_storage_contract": "0x4038d4F72C7aAbA5a442cC0dA946012B9E3f4B8a",
        "appeals_contract": "0xdc953c3bCf8837987853ca05a78D52fFC3E18651",
        "staking_contract": "0xD8fBa96C0dBB0257028dBc0107060b958e5c7113",
    }
    assert testnet_bradbury.staking_contract["abi"] is STAKING_ABI
