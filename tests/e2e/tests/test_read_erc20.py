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
                "account_kwargs": {"account_private_key": account_private_key_1},
                "contract_address_path": ["tx_data_decoded", "contract_address"],
                "retries": 40,
            },
            marks=pytest.mark.testnet,
        ),
    ],
)
def test_read_erc20(chain_config):
    """
    Tests that recursive contract calls work by:
    1. creating an LLM ERC20 contract
    2. creating a read_erc20 contract that reads the LLM ERC20 contract
    3. creating a read_erc20 contract that reads the previous read_erc20 contract
    Repeats step 3 a few times.

    It's like a linked list, but with contracts.
    """
    # Create account based on chain requirements
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    TOKEN_TOTAL_SUPPLY = 1000

    # Load contract codes
    with open(f"{CONTRACTS_DIR}/llm_erc20.py", "r") as f:
        llm_erc20_code = f.read()
    
    with open(f"{CONTRACTS_DIR}/read_erc20.py", "r") as f:
        read_erc20_code = f.read()

    # Deploy LLM ERC20 Contract
    llm_erc20_deploy_tx_hash = client.deploy_contract(
        code=llm_erc20_code, account=account, args=[TOKEN_TOTAL_SUPPLY]
    )

    # Wait for LLM ERC20 deployment
    llm_erc20_wait_kwargs = {
        "transaction_hash": llm_erc20_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        llm_erc20_wait_kwargs["retries"] = chain_config["retries"]

    llm_erc20_deploy_receipt = client.wait_for_transaction_receipt(**llm_erc20_wait_kwargs)
    assert tx_execution_succeeded(llm_erc20_deploy_receipt)

    # Extract LLM ERC20 contract address
    llm_erc20_contract_address = llm_erc20_deploy_receipt
    for key in chain_config["contract_address_path"]:
        llm_erc20_contract_address = llm_erc20_contract_address[key]

    last_contract_address = llm_erc20_contract_address

    # Deploy Read ERC20 contracts in a loop
    for i in range(5):
        print(f"Deploying contract, iteration {i}")

        # Deploy read_erc20 contract
        read_erc20_deploy_tx_hash = client.deploy_contract(
            code=read_erc20_code, account=account, args=[last_contract_address]
        )

        # Wait for read_erc20 deployment
        read_erc20_wait_kwargs = {
            "transaction_hash": read_erc20_deploy_tx_hash,
            "status": TransactionStatus.FINALIZED,
        }
        if chain_config["retries"]:
            read_erc20_wait_kwargs["retries"] = chain_config["retries"]

        read_erc20_deploy_receipt = client.wait_for_transaction_receipt(**read_erc20_wait_kwargs)
        assert tx_execution_succeeded(read_erc20_deploy_receipt)

        # Extract read_erc20 contract address
        read_erc20_contract_address = read_erc20_deploy_receipt
        for key in chain_config["contract_address_path"]:
            read_erc20_contract_address = read_erc20_contract_address[key]

        last_contract_address = read_erc20_contract_address

        # Check balance
        contract_state = client.read_contract(
            address=read_erc20_contract_address,
            function_name="get_balance_of",
            args=[account.address],
        )
        assert contract_state == TOKEN_TOTAL_SUPPLY
