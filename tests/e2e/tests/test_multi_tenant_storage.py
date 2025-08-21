import pytest
import os
from dotenv import load_dotenv

from genlayer_py import create_client, create_account
from genlayer_py.chains import localnet, studionet, testnet_asimov
from genlayer_py.types import TransactionStatus, GenLayerTransaction
from genlayer_py.client import GenLayerClient
from genlayer_py.assertions import tx_execution_succeeded

# Load environment variables from .env file
load_dotenv()

account_private_key_1 = os.getenv("ACCOUNT_PRIVATE_KEY_1")
account_private_key_2 = os.getenv("ACCOUNT_PRIVATE_KEY_2")
account_private_key_3 = os.getenv("ACCOUNT_PRIVATE_KEY_3")

CONTRACTS_DIR = "tests/e2e/contracts"


def wait_for_triggered_transactions(
    client: GenLayerClient, tx_receipt: GenLayerTransaction
) -> None:
    for triggered_transaction in tx_receipt["triggered_transactions"]:
        client.wait_for_transaction_receipt(
            transaction_hash=triggered_transaction,
            status=TransactionStatus.FINALIZED,
        )


@pytest.mark.parametrize(
    "chain_config",
    [
        pytest.param(
            {
                "chain": localnet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
                "retries": None,
            },
            marks=pytest.mark.localnet,
        ),
        pytest.param(
            {
                "chain": studionet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
                "retries": None,
            },
            marks=pytest.mark.studionet,
        ),
        pytest.param(
            {
                "chain": testnet_asimov,
                "account_kwargs_deployer": {
                    "account_private_key": account_private_key_3
                },
                "account_kwargs_1": {"account_private_key": account_private_key_1},
                "account_kwargs_2": {"account_private_key": account_private_key_2},
                "contract_address_path": ["tx_data_decoded", "contract_address"],
                "retries": 40,
            },
            marks=pytest.mark.testnet,
        ),
    ],
)
def test_multi_tenant_storage(chain_config):
    """
    This test verifies the functionality of a multi-tenant storage contract. It deploys two separate storage contracts
    and a multi-tenant storage contract that manages them. The test aims to:

    1. Deploy two different storage contracts with initial storage values.
    2. Deploy a multi-tenant storage contract that can interact with multiple storage contracts.
    3. Test the ability of the multi-tenant contract to update and retrieve storage values for multiple users
       across different storage contracts.
    4. Ensure the multi-tenant contract correctly assigns users to storage contracts and manages their data.

    This test demonstrates contract-to-contract interactions and multi-tenant data management.
    """
    # Create accounts based on chain requirements
    if "account_kwargs_deployer" in chain_config:
        # For testnet - use specific private keys
        deployer_account = create_account(**chain_config["account_kwargs_deployer"])
        user_account_a = create_account(**chain_config["account_kwargs_1"])
        user_account_b = create_account(**chain_config["account_kwargs_2"])
    else:
        # For localnet/studionet - generate random accounts
        deployer_account = create_account()
        user_account_a = create_account()
        user_account_b = create_account()

    deployer_client = create_client(
        chain=chain_config["chain"], account=deployer_account
    )
    client_a = create_client(chain=chain_config["chain"], account=user_account_a)
    client_b = create_client(chain=chain_config["chain"], account=user_account_b)

    # Load contract codes
    with open(f"{CONTRACTS_DIR}/storage.py", "r") as f:
        storage_code = f.read()

    with open(f"{CONTRACTS_DIR}/multi_tenant_storage.py", "r") as f:
        multi_tenant_storage_code = f.read()

    # Deploy first Storage Contract
    first_storage_deploy_tx_hash = deployer_client.deploy_contract(
        code=storage_code, account=deployer_account, args=["initial_storage_a"]
    )

    # Wait for first storage deployment
    first_storage_wait_kwargs = {
        "transaction_hash": first_storage_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        first_storage_wait_kwargs["retries"] = chain_config["retries"]

    first_storage_deploy_receipt = deployer_client.wait_for_transaction_receipt(
        **first_storage_wait_kwargs
    )
    assert tx_execution_succeeded(first_storage_deploy_receipt)

    # Extract first storage contract address
    first_storage_contract_address = first_storage_deploy_receipt
    for key in chain_config["contract_address_path"]:
        first_storage_contract_address = first_storage_contract_address[key]

    # Deploy second Storage Contract
    second_storage_deploy_tx_hash = deployer_client.deploy_contract(
        code=storage_code, account=deployer_account, args=["initial_storage_b"]
    )

    # Wait for second storage deployment
    second_storage_wait_kwargs = {
        "transaction_hash": second_storage_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        second_storage_wait_kwargs["retries"] = chain_config["retries"]

    second_storage_deploy_receipt = deployer_client.wait_for_transaction_receipt(
        **second_storage_wait_kwargs
    )
    assert tx_execution_succeeded(second_storage_deploy_receipt)

    # Extract second storage contract address
    second_storage_contract_address = second_storage_deploy_receipt
    for key in chain_config["contract_address_path"]:
        second_storage_contract_address = second_storage_contract_address[key]

    # Deploy Multi Tenant Storage Contract
    multi_tenant_storage_deploy_tx_hash = deployer_client.deploy_contract(
        code=multi_tenant_storage_code,
        account=deployer_account,
        args=[[first_storage_contract_address, second_storage_contract_address]],
    )

    # Wait for multi-tenant storage deployment
    multi_tenant_storage_wait_kwargs = {
        "transaction_hash": multi_tenant_storage_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        multi_tenant_storage_wait_kwargs["retries"] = chain_config["retries"]

    multi_tenant_storage_deploy_receipt = deployer_client.wait_for_transaction_receipt(
        **multi_tenant_storage_wait_kwargs
    )
    assert tx_execution_succeeded(multi_tenant_storage_deploy_receipt)

    # Extract multi-tenant storage contract address
    multi_tenant_storage_contract_address = multi_tenant_storage_deploy_receipt
    for key in chain_config["contract_address_path"]:
        multi_tenant_storage_contract_address = multi_tenant_storage_contract_address[
            key
        ]

    # Update storage for first user
    update_storage_a_tx_hash = client_a.write_contract(
        address=multi_tenant_storage_contract_address,
        function_name="update_storage",
        args=["user_a_storage"],
    )

    # Wait for update_storage transaction
    update_storage_a_wait_kwargs = {
        "transaction_hash": update_storage_a_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_storage_a_wait_kwargs["retries"] = chain_config["retries"]

    update_storage_a_receipt = client_a.wait_for_transaction_receipt(
        **update_storage_a_wait_kwargs
    )
    wait_for_triggered_transactions(client_a, update_storage_a_receipt)

    assert tx_execution_succeeded(update_storage_a_receipt)

    # Update storage for second user
    update_storage_b_tx_hash = client_b.write_contract(
        address=multi_tenant_storage_contract_address,
        function_name="update_storage",
        args=["user_b_storage"],
    )

    # Wait for update_storage transaction
    update_storage_b_wait_kwargs = {
        "transaction_hash": update_storage_b_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_storage_b_wait_kwargs["retries"] = chain_config["retries"]

    update_storage_b_receipt = client_b.wait_for_transaction_receipt(
        **update_storage_b_wait_kwargs
    )
    wait_for_triggered_transactions(client_b, update_storage_b_receipt)

    assert tx_execution_succeeded(update_storage_b_receipt)

    # Get all storages
    storages = deployer_client.read_contract(
        address=multi_tenant_storage_contract_address,
        function_name="get_all_storages",
    )

    assert storages == {
        second_storage_contract_address: "user_a_storage",
        first_storage_contract_address: "user_b_storage",
    }
