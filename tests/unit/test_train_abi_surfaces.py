import hashlib
import json

import genlayer_py.staking as staking
from genlayer_py.consensus.abi import (
    APPEALS_ABI,
    CONSENSUS_DATA_ABI,
    CONSENSUS_DATA_ABI_V06,
    CONSENSUS_MAIN_ABI,
    CONSENSUS_MAIN_ABI_V06,
)
from genlayer_py.staking.abi import STAKING_ABI, VALIDATOR_WALLET_ABI

# Hashes of the recursively canonicalized function surfaces generated from the
# genlayer-consensus v0.6.0 artifacts (8805afba138cb98ca9142cb94c01acca7e4b5d80),
# the release Bradbury Phase 3 runs: ConsensusData, ConsensusMainWithFees,
# Appeals, IGenLayerStaking and ValidatorWalletBlueprint.
# This covers every nested tuple component, not just top-level selectors or
# function names.
EXPECTED_TRAIN_FUNCTION_SURFACE_HASHES = {
    "ConsensusData": "de78eb7b9b950bf3ad7c1b4e4486f123f3b32faf90c3576ca0fc326940b4c850",
    "ConsensusMain": "4b553fbf4b43e1ce9f2a7ad46a482b0970ef204077a5d4fb2698ea8dcb6cb2d0",
    "Appeals": "8f73cc982a95ed727f165d1b221eb227a40fe68862cef51a51cfbbcb7ef560e1",
    "IGenLayerStaking": "2fa0b1287b943f719f5e900b14b55a24f196554edbfd8230cff605466bca24a1",
    "ValidatorWalletBlueprint": "3befb78d9eed9d50a60cac7508bc8c9b076ad43d5b523f15eba15f673051fedb",
}


def _canonical_parameter(parameter):
    canonical = {
        "name": parameter.get("name", ""),
        "type": parameter["type"],
    }
    if parameter["type"].startswith("tuple"):
        canonical["components"] = [
            _canonical_parameter(component)
            for component in parameter.get("components", [])
        ]
    return canonical


def _function_surface_hash(abi):
    functions = [
        {
            "name": entry["name"],
            "stateMutability": entry.get("stateMutability"),
            "inputs": [
                _canonical_parameter(parameter) for parameter in entry.get("inputs", [])
            ],
            "outputs": [
                _canonical_parameter(parameter)
                for parameter in entry.get("outputs", [])
            ],
        }
        for entry in abi
        if entry.get("type") == "function"
    ]
    functions.sort(
        key=lambda entry: json.dumps(entry, sort_keys=True, separators=(",", ":"))
    )
    encoded = json.dumps(functions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_bundled_function_surfaces_match_the_exact_consensus_train():
    bundled = {
        "ConsensusData": CONSENSUS_DATA_ABI,
        "ConsensusMain": CONSENSUS_MAIN_ABI,
        "Appeals": APPEALS_ABI,
        "IGenLayerStaking": STAKING_ABI,
        "ValidatorWalletBlueprint": VALIDATOR_WALLET_ABI,
    }

    assert {
        name: _function_surface_hash(abi) for name, abi in bundled.items()
    } == EXPECTED_TRAIN_FUNCTION_SURFACE_HASHES


def test_historical_consensus_abi_imports_are_train_only_aliases():
    assert CONSENSUS_DATA_ABI_V06 is CONSENSUS_DATA_ABI
    assert CONSENSUS_MAIN_ABI_V06 is CONSENSUS_MAIN_ABI


def test_staking_package_exports_the_proof_based_join_helpers():
    expected = {
        "get_validator_join_context",
        "OperatorRegistrationContext",
        "OperatorRegistrationProof",
        "create_operator_registration",
        "verify_operator_registration",
    }

    assert expected.issubset(staking.__all__)
    assert all(hasattr(staking, name) for name in expected)
