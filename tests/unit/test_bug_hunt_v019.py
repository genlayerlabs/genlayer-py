"""Regression tests for high-confidence defects found on v0.19-dev.

These tests are intentionally red until the corresponding production defects
are fixed.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from genlayer_py.abi import calldata
from genlayer_py.chains import localnet
from genlayer_py.client.client import GenLayerClient, create_client
from genlayer_py.contracts.actions import read_contract
from genlayer_py.exceptions import GenLayerError
from genlayer_py.transactions.actions import is_successful


def test_create_client_endpoint_does_not_mutate_caller_chain_config():
    chain = deepcopy(localnet)
    original_endpoints = list(chain.rpc_urls["default"]["http"])

    with patch.object(GenLayerClient, "initialize_consensus_smart_contract"):
        client = create_client(chain=chain, endpoint="http://override.invalid:8545")

    assert client.chain.rpc_urls["default"]["http"] == [
        "http://override.invalid:8545"
    ]
    assert chain.rpc_urls["default"]["http"] == original_endpoints


def test_read_contract_uses_explicit_account_when_client_has_no_default():
    account = SimpleNamespace(
        address="0x1111111111111111111111111111111111111111"
    )
    provider = Mock()
    provider.make_request.return_value = {"result": ""}
    client = SimpleNamespace(local_account=None, provider=provider)

    assert (
        read_contract(
            self=client,
            address="0x2222222222222222222222222222222222222222",
            function_name="balance",
            account=account,
            raw_return=True,
        )
        == "0x"
    )
    request = provider.make_request.call_args.kwargs["params"][0]
    assert request["from"] == account.address


def test_calldata_decoder_rejects_truncated_length_prefixed_bytes():
    declares_two_bytes_but_contains_one = bytes([(2 << 3) | 3, 0xAA])

    with pytest.raises(GenLayerError, match="truncated|unexpected end|invalid"):
        calldata.decode(declares_two_bytes_but_contains_one)


def test_is_successful_recognizes_localnet_consensus_receipt():
    transaction = {
        "status_name": "FINALIZED",
        "consensus_data": {
            "leader_receipt": [
                {
                    "mode": "leader",
                    "execution_result": "SUCCESS",
                }
            ]
        },
    }

    assert is_successful(transaction)
