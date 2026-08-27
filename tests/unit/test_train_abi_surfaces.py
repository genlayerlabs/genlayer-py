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
# exact consensus train artifacts at 1292a9e0be17cd0746c6c3dd05eebbfd847cd48a.
# This covers every nested tuple component, not just top-level selectors or
# function names.
EXPECTED_TRAIN_FUNCTION_SURFACE_HASHES = {
    "ConsensusData": "3a7d39f4ed6c6aaa8dc1cfd5035387191f68c737ba499cd9732cf89fc97b7d34",
    "ConsensusMain": "5b72222c57d28e69f52d7f96100ed6489475f7374a3b53e96f8907c9bab9449d",
    "Appeals": "7ff07eb47a1e801645e55141bcf75aaae022d46f06c8a94f29806a9fc61a0857",
    "IGenLayerStaking": "1fd78e63d480800d93d41d3f5bdfd17f572bc5f394cccc7c796098f5ce8156b4",
    "ValidatorWalletBlueprint": "6960726132fd77007eec8a90f036ef4be8d8efdcb6c6b79136c8835bb0b17800",
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
