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
account_private_key_2 = os.getenv("ACCOUNT_PRIVATE_KEY_2")

CONTRACTS_DIR = "tests/e2e/contracts"

INITIAL_STATE_USER_A = "user_a_initial_state"
UPDATED_STATE_USER_A = "user_a_updated_state"
INITIAL_STATE_USER_B = "user_b_initial_state"
UPDATED_STATE_USER_B = "user_b_updated_state"


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
                "account_kwargs_1": {"account_private_key": account_private_key_1},
                "account_kwargs_2": {"account_private_key": account_private_key_2},
                "contract_address_path": ["tx_data_decoded", "contract_address"],
                "retries": 40,
            },
            marks=pytest.mark.testnet,
        ),
    ],
)
def test_user_storage(chain_config):
    # Create accounts based on chain requirements
    if "account_kwargs_1" in chain_config:
        # For testnet - use specific private keys
        from_account_a = create_account(**chain_config["account_kwargs_1"])
        from_account_b = create_account(**chain_config["account_kwargs_2"])
    else:
        # For localnet/studionet - generate random accounts
        from_account_a = create_account()
        from_account_b = create_account()

    client_a = create_client(chain=chain_config["chain"], account=from_account_a)
    client_b = create_client(chain=chain_config["chain"], account=from_account_b)

    with open(f"{CONTRACTS_DIR}/user_storage.py", "r") as f:
        code = f.read()

    # Deploy Contract
    deploy_tx_hash = client_a.deploy_contract(
        code=code, account=from_account_a, args=[]
    )

    # Wait for transaction with retries if specified
    wait_kwargs = {
        "transaction_hash": deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        wait_kwargs["retries"] = chain_config["retries"]

    deploy_receipt = client_a.wait_for_transaction_receipt(**wait_kwargs)

    # Handle assertion style differences
    assert tx_execution_succeeded(deploy_receipt)

    # Extract contract address based on chain-specific path
    contract_address = deploy_receipt
    for key in chain_config["contract_address_path"]:
        contract_address = contract_address[key]

    # GET Initial State
    contract_state_1 = client_a.read_contract(
        address=contract_address,
        function_name="get_complete_storage",
    )
    assert contract_state_1 == {}

    # ADD User A State
    update_storage_a_tx_hash = client_a.write_contract(
        address=contract_address,
        function_name="update_storage",
        args=[INITIAL_STATE_USER_A],
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
    assert tx_execution_succeeded(update_storage_a_receipt)

    # Get Updated State
    contract_state_2_1 = client_a.read_contract(
        address=contract_address,
        function_name="get_complete_storage",
    )
    assert contract_state_2_1[from_account_a.address] == INITIAL_STATE_USER_A

    # Get Updated State
    contract_state_2_2 = client_a.read_contract(
        address=contract_address,
        function_name="get_account_storage",
        args=[from_account_a.address],
    )
    assert contract_state_2_2 == INITIAL_STATE_USER_A

    # ADD User B State
    update_storage_b_tx_hash = client_b.write_contract(
        address=contract_address,
        function_name="update_storage",
        args=[INITIAL_STATE_USER_B],
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
    assert tx_execution_succeeded(update_storage_b_receipt)

    # Get Updated State
    contract_state_3 = client_a.read_contract(
        address=contract_address,
        function_name="get_complete_storage",
    )
    assert contract_state_3[from_account_a.address] == INITIAL_STATE_USER_A
    assert contract_state_3[from_account_b.address] == INITIAL_STATE_USER_B

    # UPDATE User A State
    update_storage_a2_tx_hash = client_a.write_contract(
        address=contract_address,
        function_name="update_storage",
        args=[UPDATED_STATE_USER_A],
    )

    # Wait for update_storage transaction
    update_storage_a2_wait_kwargs = {
        "transaction_hash": update_storage_a2_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_storage_a2_wait_kwargs["retries"] = chain_config["retries"]

    update_storage_a2_receipt = client_a.wait_for_transaction_receipt(
        **update_storage_a2_wait_kwargs
    )
    assert tx_execution_succeeded(update_storage_a2_receipt)

    # Get Updated State
    contract_state_4_1 = client_a.read_contract(
        address=contract_address,
        function_name="get_complete_storage",
    )
    assert contract_state_4_1[from_account_a.address] == UPDATED_STATE_USER_A
    assert contract_state_4_1[from_account_b.address] == INITIAL_STATE_USER_B

    # Get Updated State
    contract_state_4_2 = client_a.read_contract(
        address=contract_address,
        function_name="get_account_storage",
        args=[from_account_b.address],
    )
    assert contract_state_4_2 == INITIAL_STATE_USER_B
