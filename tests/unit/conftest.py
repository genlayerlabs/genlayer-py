"""
Shared pytest fixtures for unit tests.

This file contains common fixtures that can be used across all unit tests,
including mocked clients, transaction data, and other reusable test utilities.
"""

import pytest
from unittest.mock import Mock
from .sample_data import (
    RAW_DEPLOY_TRANSACTION_DATA,
    RAW_WRITE_TRANSACTION_DATA,
    FULL_DEPLOY_TRANSACTION_DATA,
    FULL_WRITE_TRANSACTION_DATA,
    SIMPLIFIED_DEPLOY_TRANSACTION_DATA,
    SIMPLIFIED_WRITE_TRANSACTION_DATA,
    DEPLOY_TRANSACTION_HASH,
    WRITE_TRANSACTION_HASH,
)


@pytest.fixture
def mock_client(raw_deploy_transaction_data, raw_write_transaction_data):
    """Mock GenLayerClient instance with common methods"""
    client = Mock()

    # Mock common client methods
    client.get_transaction = Mock()
    client.w3 = Mock()
    client.w3.eth = Mock()
    client.w3.to_hex = Mock(
        side_effect=lambda x: x if isinstance(x, str) else "0x" + x.hex()
    )
    client.provider = Mock()

    # Mock provider.make_request for different transaction types
    def mock_make_request(method, params):
        if method == "eth_getTransactionByHash":
            tx_hash = params[0]
            if tx_hash == DEPLOY_TRANSACTION_HASH:
                # Deploy transaction
                return {"result": raw_deploy_transaction_data}
            elif tx_hash == WRITE_TRANSACTION_HASH:
                # Write transaction (transfer call)
                return {"result": raw_write_transaction_data}
            else:
                # Return a generic transaction for other hashes
                return {
                    "result": {
                        "hash": tx_hash,
                        "status": "FINALIZED",
                        "from_address": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
                        "to_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
                        "consensus_data": {"leader_receipt": []},
                        "type": 2,
                    }
                }
        return {"result": None}

    client.provider.make_request = Mock(side_effect=mock_make_request)

    # Mock chain configuration
    client.chain = Mock()
    client.chain.id = "localnet"
    client.chain.consensus_main_contract = {
        "address": "0xConsensusMainContract",
        "abi": [],
    }
    client.chain.consensus_data_contract = {
        "address": "0xConsensusDataContract",
        "abi": [],
    }
    client.chain.default_consensus_max_rotations = 3
    client.chain.default_number_of_initial_validators = 5

    # Mock account if needed
    client.local_account = Mock()
    client.local_account.address = "0xd650f318A0C1F940a3b6dFeA695747fA9804D685"

    return client


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing - simplified version"""
    return {
        "hash": "0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
        "tx_id": "0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
        "from_address": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
        "to_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
        "sender": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
        "recipient": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
        "value": 0,
        "gaslimit": 2,
        "nonce": 1,
        "type": 2,
        "status": 7,  # FINALIZED
        "status_name": "FINALIZED",
        "result": "6",
        "result_name": "MAJORITY_AGREE",
        "created_at": "2025-07-22T19:58:39.866436+00:00",
        "data": {
            "calldata": {
                "readable": '{"args":[500,"0x4C76986555e8C63bD0D9CFAFbf8e68C338556b6b"],"method":"transfer"}'
            }
        },
        "contract_snapshot": {
            "contract_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA"
        },
    }


@pytest.fixture
def pending_transaction_data():
    """Transaction in pending state"""
    return {
        "hash": "0x4b8037744adab7ea8335b4f839979d20031d83a8ccdf706e0ae61312930335f6",
        "status": 1,  # PENDING
        "status_name": "PENDING",
        "from_address": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
        "to_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
        "value": 0,
        "nonce": 1,
    }


@pytest.fixture
def accepted_transaction_data(sample_transaction_data):
    """Transaction in accepted state"""
    data = sample_transaction_data.copy()
    data["status"] = 5  # ACCEPTED
    data["status_name"] = "ACCEPTED"
    return data


@pytest.fixture
def mock_account():
    """Mock LocalAccount for testing"""
    account = Mock()
    account.address = "0xd650f318A0C1F940a3b6dFeA695747fA9804D685"
    account.private_key = (
        "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    )
    account.sign_transaction = Mock()
    return account


@pytest.fixture
def raw_deploy_transaction_data():
    """Deploy transaction data for hash 0xb7a93f0199dd16cf4ce0055d4e615ba05450c1dd4f3986575d1468378111af80"""
    return RAW_DEPLOY_TRANSACTION_DATA


@pytest.fixture
def raw_write_transaction_data():
    """Write transaction data for hash 0x426f0fa344f7c382dcaf978cc0965ee5b330f0b6aef7f64d4a2bd8d7cc7d5893"""
    return RAW_WRITE_TRANSACTION_DATA


@pytest.fixture
def full_write_transaction_data():
    """Full decoded write transaction data with consensus data and all fields"""
    return FULL_WRITE_TRANSACTION_DATA


@pytest.fixture
def full_deploy_transaction_data():
    """Full decoded deploy transaction data with consensus data and all fields"""
    return FULL_DEPLOY_TRANSACTION_DATA


@pytest.fixture
def simplified_write_transaction_data():
    """Simplified write transaction data with non-essential fields removed"""
    return SIMPLIFIED_WRITE_TRANSACTION_DATA


@pytest.fixture
def simplified_deploy_transaction_data():
    """Simplified deploy transaction data with non-essential fields removed"""
    return SIMPLIFIED_DEPLOY_TRANSACTION_DATA


@pytest.fixture
def mock_web3_contract():
    """Mock Web3 contract instance"""
    contract = Mock()
    contract.functions = Mock()
    contract.get_event_by_name = Mock()
    return contract
