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


@pytest.mark.parametrize(
    "chain_config",
    [
        pytest.param(
            {
                "chain": localnet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
                "retries": None,
                "contract_file": "log_indexer.py",
            },
            marks=pytest.mark.localnet,
        ),
        pytest.param(
            {
                "chain": studionet,
                "account_kwargs": {},
                "contract_address_path": ["data", "contract_address"],
                "retries": None,
                "contract_file": "log_indexer.py",
            },
            marks=pytest.mark.studionet,
        ),
        pytest.param(
            {
                "chain": testnet_asimov,
                "account_kwargs": {"account_private_key": account_private_key_1},
                "contract_address_path": ["tx_data_decoded", "contract_address"],
                "retries": 40,
                "contract_file": "log_indexer_testnet.py",
            },
            marks=pytest.mark.testnet,
        ),
    ],
)
def test_log_indexer(chain_config):
    # Create account based on chain requirements
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    with open(f"{CONTRACTS_DIR}/{chain_config['contract_file']}", "r") as f:
        code = f.read()

    # Deploy Contract
    deploy_tx_hash = client.deploy_contract(code=code, account=account, args=[])

    print("deploy_tx_hash", deploy_tx_hash)
    # Wait for transaction with retries if specified
    wait_kwargs = {
        "transaction_hash": deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        wait_kwargs["retries"] = chain_config["retries"]

    deploy_receipt = client.wait_for_transaction_receipt(**wait_kwargs)
    print("deploy_receipt", deploy_receipt)
    # Handle assertion style differences
    assert tx_execution_succeeded(deploy_receipt)

    # Extract contract address based on chain-specific path
    contract_address = deploy_receipt
    for key in chain_config["contract_address_path"]:
        contract_address = contract_address[key]

    # Get closest vector when empty
    closest_vector_log_0 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["I like mango"],
    )
    assert closest_vector_log_0 is None

    # Add log 0
    add_log_0_tx_hash = client.write_contract(
        address=contract_address,
        function_name="add_log",
        args=["I like to eat mango", 0],
    )
    print("add_log_0_tx_hash", add_log_0_tx_hash)
    # Wait for add_log transaction
    add_log_0_wait_kwargs = {
        "transaction_hash": add_log_0_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        add_log_0_wait_kwargs["retries"] = chain_config["retries"]

    add_log_0_receipt = client.wait_for_transaction_receipt(**add_log_0_wait_kwargs)
    print("add_log_0_receipt", add_log_0_receipt)
    assert tx_execution_succeeded(add_log_0_receipt)

    # Get closest vector to log 0
    closest_vector_log_0 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["I like mango"],
    )
    assert float(closest_vector_log_0["similarity"]) > 0.94
    assert float(closest_vector_log_0["similarity"]) < 0.95

    # Add log 1
    add_log_1_tx_hash = client.write_contract(
        address=contract_address,
        function_name="add_log",
        args=["I like carrots", 1],
    )
    print("add_log_1_tx_hash", add_log_1_tx_hash)
    # Wait for add_log transaction
    add_log_1_wait_kwargs = {
        "transaction_hash": add_log_1_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        add_log_1_wait_kwargs["retries"] = chain_config["retries"]

    add_log_1_receipt = client.wait_for_transaction_receipt(**add_log_1_wait_kwargs)
    print("add_log_1_receipt", add_log_1_receipt)
    assert tx_execution_succeeded(add_log_1_receipt)

    # Get closest vector to log 1
    closest_vector_log_1 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["I like carrots"],
    )
    assert float(closest_vector_log_1["similarity"]) == 1

    # Update log 0
    update_log_0_tx_hash = client.write_contract(
        address=contract_address,
        function_name="update_log",
        args=[0, "I like to eat a lot of mangoes"],
    )
    print("update_log_0_tx_hash", update_log_0_tx_hash)
    # Wait for update_log transaction
    update_log_0_wait_kwargs = {
        "transaction_hash": update_log_0_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_log_0_wait_kwargs["retries"] = chain_config["retries"]

    update_log_0_receipt = client.wait_for_transaction_receipt(
        **update_log_0_wait_kwargs
    )
    print("update_log_0_receipt", update_log_0_receipt)
    assert tx_execution_succeeded(update_log_0_receipt)

    # Get closest vector to log 0
    closest_vector_log_0_2 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["I like mango a lot"],
    )
    assert float(closest_vector_log_0_2["similarity"]) > 0.94
    assert float(closest_vector_log_0_2["similarity"]) < 0.95

    # Remove log 0
    remove_log_0_tx_hash = client.write_contract(
        address=contract_address,
        function_name="remove_log",
        args=[0],
    )

    # Wait for remove_log transaction
    remove_log_0_wait_kwargs = {
        "transaction_hash": remove_log_0_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        remove_log_0_wait_kwargs["retries"] = chain_config["retries"]

    remove_log_0_receipt = client.wait_for_transaction_receipt(
        **remove_log_0_wait_kwargs
    )
    assert tx_execution_succeeded(remove_log_0_receipt)

    # Get closest vector to log 0
    closest_vector_log_0_3 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["I like to eat mango"],
    )
    assert float(closest_vector_log_0_3["similarity"]) > 0.67
    assert float(closest_vector_log_0_3["similarity"]) < 0.68

    # Add third log
    add_log_2_tx_hash = client.write_contract(
        address=contract_address,
        function_name="add_log",
        args=["This is the third log", 3],
    )

    # Wait for add_log transaction
    add_log_2_wait_kwargs = {
        "transaction_hash": add_log_2_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        add_log_2_wait_kwargs["retries"] = chain_config["retries"]

    add_log_2_receipt = client.wait_for_transaction_receipt(**add_log_2_wait_kwargs)
    assert tx_execution_succeeded(add_log_2_receipt)

    # Check if new item got id 2
    closest_vector_log_2 = client.read_contract(
        address=contract_address,
        function_name="get_closest_vector",
        args=["This is the third log"],
    )
    assert float(closest_vector_log_2["similarity"]) > 0.99
    assert closest_vector_log_2["id"] == 3
    assert closest_vector_log_2["text"] == "This is the third log"
