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
def test_llm_erc20_interaction(chain_config):
    # Create accounts based on chain requirements
    if "account_kwargs_1" in chain_config:
        # For testnet - use specific private keys
        from_account_a = create_account(**chain_config["account_kwargs_1"])
        from_account_b = create_account(**chain_config["account_kwargs_2"])
    else:
        # For localnet/studionet - generate random accounts
        from_account_a = create_account()
        from_account_b = create_account()

    client = create_client(chain=chain_config["chain"], account=from_account_a)

    with open(f"{CONTRACTS_DIR}/llm_erc20.py", "r") as f:
        code = f.read()

    TOKEN_TOTAL_SUPPLY = 1000
    TRANSFER_AMOUNT = 100

    print("from_account_a", from_account_a.address)
    print("from_account_b", from_account_b.address)

    # Deploy Contract
    deploy_tx_hash = client.deploy_contract(
        code=code, account=from_account_a, args=[TOKEN_TOTAL_SUPPLY]
    )

    # Wait for transaction with retries if specified
    wait_kwargs = {
        "transaction_hash": deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        wait_kwargs["retries"] = chain_config["retries"]

    deploy_receipt = client.wait_for_transaction_receipt(**wait_kwargs)

    # Handle assertion style differences
    assert tx_execution_succeeded(deploy_receipt)

    # Extract contract address based on chain-specific path
    contract_address = deploy_receipt
    for key in chain_config["contract_address_path"]:
        contract_address = contract_address[key]

    # Get Initial State
    contract_state_1 = client.read_contract(
        address=contract_address,
        function_name="get_balances",
    )
    assert contract_state_1[from_account_a.address] == TOKEN_TOTAL_SUPPLY

    # Transfer from User A to User B
    transfer_tx_hash = client.write_contract(
        address=contract_address,
        function_name="transfer",
        args=[TRANSFER_AMOUNT, from_account_b.address],
    )

    # Wait for transfer transaction with retries if specified
    transfer_wait_kwargs = {
        "transaction_hash": transfer_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        transfer_wait_kwargs["retries"] = chain_config["retries"]

    transfer_receipt = client.wait_for_transaction_receipt(**transfer_wait_kwargs)

    # Handle assertion style differences
    assert tx_execution_succeeded(transfer_receipt)

    # Get Updated State - all balances
    contract_state_2_1 = client.read_contract(
        address=contract_address,
        function_name="get_balances",
    )
    assert (
        contract_state_2_1[from_account_a.address]
        == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT
    )
    assert contract_state_2_1[from_account_b.address] == TRANSFER_AMOUNT

    # Get Updated State - individual balance checks
    contract_state_2_2 = client.read_contract(
        address=contract_address,
        function_name="get_balance_of",
        args=[from_account_a.address],
    )
    assert contract_state_2_2 == TOKEN_TOTAL_SUPPLY - TRANSFER_AMOUNT

    # Get Updated State
    contract_state_2_3 = client.read_contract(
        address=contract_address,
        function_name="get_balance_of",
        args=[from_account_b.address],
    )
    assert contract_state_2_3 == TRANSFER_AMOUNT
