import dataclasses
from unittest.mock import Mock

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
from genlayer_py.types import GenLayerChain


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
    assert not is_studio_chain(testnet_bradbury)


def test_studio_presets_carry_the_studio_flag_and_testnets_do_not():
    assert localnet.is_studio
    assert studionet.is_studio
    assert studio_devnet.is_studio
    assert not testnet_asimov.is_studio
    assert not testnet_bradbury.is_studio


def test_studio_preset_with_custom_chain_id_is_still_studio():
    hosted = dataclasses.replace(studio_devnet, id=61998)

    assert hosted.id == 61998
    assert hosted.is_studio
    assert is_studio_chain(hosted)


def _hand_built_chain(chain_id: int) -> GenLayerChain:
    return GenLayerChain(
        chain_id,
        "Hand-built",
        {"default": {"http": ["http://127.0.0.1:4000/api"]}},
        studionet.native_currency,
        {},
        True,
        None,
        None,
        None,
        None,
        None,
        None,
        5,
        3,
    )


def test_hand_built_chain_without_flag_falls_back_to_known_studio_ids():
    known = _hand_built_chain(61999)
    unknown = _hand_built_chain(61998)

    assert known.is_studio is False
    assert is_studio_chain(known)
    assert not is_studio_chain(unknown)


def test_hand_built_chain_with_flag_and_custom_id_is_studio():
    assert is_studio_chain(
        dataclasses.replace(_hand_built_chain(61998), is_studio=True)
    )


def test_chain_like_objects_without_a_real_flag_use_the_id():
    mock_chain = Mock()
    mock_chain.id = 1

    assert not is_studio_chain(mock_chain)


def test_studio_presets_have_distinct_chain_ids():
    assert len({localnet.id, studio_devnet.id, studionet.id}) == 3


def test_bradbury_targets_the_phase_3_deployment():
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
        "consensus_main_contract": "0x0f4F0e05475723790E4a2ed0598370783C300926",
        "consensus_data_contract": "0x2247b85b7ca7fb1Fea990b4aFAB4328D9c597f28",
        "fee_manager_contract": "0x8E8B6194020dB1CbEf9C6c9dcFeE8FfF1e5E33c3",
        "rounds_storage_contract": "0xa6bdB728B82c23786D6e3CAfc0B97235490A64Fb",
        "appeals_contract": "0x10F2d70ABB8F588f96bEB1a02c99163EB75A2CF1",
        "staking_contract": "0xcE16862EAf10B97A0619BeBb662991fb4a52e346",
    }
    assert testnet_bradbury.staking_contract["abi"] is STAKING_ABI
