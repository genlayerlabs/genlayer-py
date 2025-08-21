import time
import pytest
import os
from dotenv import load_dotenv

from genlayer_py import create_client, create_account
from genlayer_py.chains import localnet, studionet, testnet_asimov
from genlayer_py.types import TransactionStatus
from genlayer_py.assertions import tx_execution_succeeded

# Load environment variables from .env file
load_dotenv()

account_private_key_1 = os.getenv("ACCOUNT_PRIVATE_KEY_1")

CONTRACTS_DIR = "tests/e2e/contracts"


def wait_for_contract_deployment(client, contract_address, max_retries=10, delay=5):
    """
    Wait for intelligent oracle contract to be fully deployed by attempting to call a method.
    This is used to check if the triggered deployment did deploy the contract.
    """
    for _ in range(max_retries):
        try:
            client.read_contract(
                address=contract_address,
                function_name="get_dict",
            )
            return True  # If successful, contract is deployed
        except Exception:
            time.sleep(delay)
    return False


@pytest.mark.parametrize(
    "chain_config",
    [
        pytest.param(
            {
                "chain": localnet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
            },
            marks=pytest.mark.localnet,
        ),
        pytest.param(
            {
                "chain": studionet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
            },
            marks=pytest.mark.studionet,
        ),
        pytest.param(
            {
                "chain": testnet_asimov,
                "account_kwargs": {"account_private_key": account_private_key_1},
                "contract_address_path": ["tx_data_decoded", "contract_address"],
            },
            marks=pytest.mark.testnet,
        ),
    ],
)
def test_intelligent_oracle_factory_pattern(chain_config):
    # Create account based on chain requirements
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    # Load contract codes
    with open(f"{CONTRACTS_DIR}/intelligent_oracle.py", "r") as f:
        intelligent_oracle_code = f.read()

    with open(f"{CONTRACTS_DIR}/intelligent_oracle_factory.py", "r") as f:
        registry_code = f.read()

    # Deploy the Registry contract with the IntelligentOracle code
    registry_deploy_tx_hash = client.deploy_contract(
        code=registry_code, account=account, args=[intelligent_oracle_code]
    )

    # Wait for registry deployment
    registry_wait_kwargs = {
        "transaction_hash": registry_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
        "retries": 80,
    }

    registry_deploy_receipt = client.wait_for_transaction_receipt(
        **registry_wait_kwargs
    )
    assert tx_execution_succeeded(registry_deploy_receipt)

    # Extract registry contract address
    registry_contract_address = registry_deploy_receipt
    for key in chain_config["contract_address_path"]:
        registry_contract_address = registry_contract_address[key]

    markets_data = [
        {
            "prediction_market_id": "marathon2024",
            "title": "Marathon Winner Prediction",
            "description": "Predict the male winner of a major marathon event.",
            "potential_outcomes": ["Bekele Fikre", "Tafa Mitku", "Chebii Douglas"],
            "rules": [
                "The outcome is based on the official race results announced by the marathon organizers."
            ],
            "data_source_domains": ["thepostrace.com"],
            "resolution_urls": [],
            "earliest_resolution_date": "2024-01-01T00:00:00+00:00",
            "outcome": "Tafa Mitku",
            "evidence_urls": "https://thepostrace.com/en/blog/marathon-de-madrid-2024-results-and-rankings/?srsltid=AfmBOor1uG6O3_4oJ447hkah_ilOYuy0XXMvl8j70EApe1Z7Bzd94XJl",
        },
        {
            "prediction_market_id": "election2024",
            "title": "Election Prediction",
            "description": "Predict the winner of the 2024 US presidential election.",
            "potential_outcomes": ["Kamala Harris", "Donald Trump"],
            "rules": ["The outcome is based on official election results."],
            "data_source_domains": ["bbc.com"],
            "resolution_urls": [],
            "earliest_resolution_date": "2024-01-01T00:00:00+00:00",
            "outcome": "Donald Trump",
            "evidence_urls": "https://www.bbc.com/news/election/2024/us/results",
        },
    ]
    created_market_contracts = []

    # Create markets through factory
    for market_data in markets_data:
        create_tx_hash = client.write_contract(
            address=registry_contract_address,
            function_name="create_new_prediction_market",
            args=[
                market_data["prediction_market_id"],
                market_data["title"],
                market_data["description"],
                market_data["potential_outcomes"],
                market_data["rules"],
                market_data["data_source_domains"],
                market_data["resolution_urls"],
                market_data["earliest_resolution_date"],
            ],
        )

        # Wait for create_new_prediction_market transaction
        create_wait_kwargs = {
            "transaction_hash": create_tx_hash,
            "status": TransactionStatus.FINALIZED,
            "retries": 80,
        }

        create_receipt = client.wait_for_transaction_receipt(**create_wait_kwargs)
        assert tx_execution_succeeded(create_receipt)

        # Get the latest contract address from factory
        registered_addresses = client.read_contract(
            address=registry_contract_address,
            function_name="get_contract_addresses",
        )
        new_market_address = registered_addresses[-1]
        created_market_contracts.append(new_market_address)

        # Wait for the new market contract to be deployed
        assert wait_for_contract_deployment(
            client, new_market_address, max_retries=80, delay=10
        ), f"Market contract deployment timeout for {market_data['prediction_market_id']}"

    # Verify all markets were registered
    assert len(registered_addresses) == len(markets_data)

    # Verify each market's state
    for i, market_contract_address in enumerate(created_market_contracts):
        market_state = client.read_contract(
            address=market_contract_address,
            function_name="get_dict",
        )
        expected_data = markets_data[i]

        # Verify key market properties
        assert market_state["title"] == expected_data["title"]
        assert market_state["description"] == expected_data["description"]
        assert market_state["potential_outcomes"] == expected_data["potential_outcomes"]
        assert market_state["rules"] == expected_data["rules"]
        assert (
            market_state["data_source_domains"] == expected_data["data_source_domains"]
        )
        assert market_state["resolution_urls"] == expected_data["resolution_urls"]
        assert market_state["status"] == "Active"
        assert (
            market_state["earliest_resolution_date"]
            == expected_data["earliest_resolution_date"]
        )
        assert (
            market_state["prediction_market_id"]
            == expected_data["prediction_market_id"]
        )

    # Resolve markets
    for i, market_contract_address in enumerate(created_market_contracts):
        resolve_tx_hash = client.write_contract(
            address=market_contract_address,
            function_name="resolve",
            args=[markets_data[i]["evidence_urls"]],
        )

        # Wait for resolve transaction
        resolve_wait_kwargs = {
            "transaction_hash": resolve_tx_hash,
            "status": TransactionStatus.FINALIZED,
            "retries": 80,
        }

        resolve_receipt = client.wait_for_transaction_receipt(**resolve_wait_kwargs)
        assert tx_execution_succeeded(resolve_receipt)

        # Verify market was resolved and has the correct outcome
        market_state = client.read_contract(
            address=market_contract_address,
            function_name="get_dict",
        )
        assert market_state["status"] == "Resolved"
        assert market_state["outcome"] == markets_data[i]["outcome"]
