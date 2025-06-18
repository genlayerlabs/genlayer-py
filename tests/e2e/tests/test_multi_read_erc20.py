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
def test_multi_read_erc20(chain_config):
    """
    This test verifies the functionality of a multi-read ERC20 contract. It deploys two separate ERC20 token contracts
    (referred to as 'doge' and 'shiba') and a multi-read ERC20 contract. The test aims to:

    1. Deploy two different ERC20 token contracts with a total supply of 1000 tokens each.
    2. Deploy a multi-read ERC20 contract that can interact with multiple ERC20 tokens.
    3. Test the ability of the multi-read contract to update and retrieve token balances for multiple ERC20 tokens
       and multiple accounts simultaneously.
    4. Ensure the multi-read contract correctly maintains and reports balances for different account-token combinations.

    This test demonstrates the integration contract to contract reads
    """
    # Create accounts based on chain requirements
    if "account_kwargs_1" in chain_config:
        # For testnet - use specific private keys
        from_account_doge = create_account(**chain_config["account_kwargs_1"])
        from_account_shiba = create_account(**chain_config["account_kwargs_2"])
    else:
        # For localnet/studionet - generate random accounts
        from_account_doge = create_account()
        from_account_shiba = create_account()

    client_doge = create_client(chain=chain_config["chain"], account=from_account_doge)
    client_shiba = create_client(chain=chain_config["chain"], account=from_account_shiba)

    TOKEN_TOTAL_SUPPLY = 1000

    # Load contract codes
    with open(f"{CONTRACTS_DIR}/llm_erc20.py", "r") as f:
        llm_erc20_code = f.read()
    
    with open(f"{CONTRACTS_DIR}/multi_read_erc20.py", "r") as f:
        multi_read_erc20_code = f.read()

    # Deploy first LLM ERC20 Contract (doge)
    doge_deploy_tx_hash = client_doge.deploy_contract(
        code=llm_erc20_code, account=from_account_doge, args=[TOKEN_TOTAL_SUPPLY]
    )

    # Wait for doge deployment
    doge_wait_kwargs = {
        "transaction_hash": doge_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        doge_wait_kwargs["retries"] = chain_config["retries"]

    doge_deploy_receipt = client_doge.wait_for_transaction_receipt(**doge_wait_kwargs)
    assert tx_execution_succeeded(doge_deploy_receipt)

    # Extract doge contract address
    doge_contract_address = doge_deploy_receipt
    for key in chain_config["contract_address_path"]:
        doge_contract_address = doge_contract_address[key]

    # Deploy second LLM ERC20 Contract (shiba)
    shiba_deploy_tx_hash = client_shiba.deploy_contract(
        code=llm_erc20_code, account=from_account_shiba, args=[TOKEN_TOTAL_SUPPLY]
    )

    # Wait for shiba deployment
    shiba_wait_kwargs = {
        "transaction_hash": shiba_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        shiba_wait_kwargs["retries"] = chain_config["retries"]

    shiba_deploy_receipt = client_shiba.wait_for_transaction_receipt(**shiba_wait_kwargs)
    assert tx_execution_succeeded(shiba_deploy_receipt)

    # Extract shiba contract address
    shiba_contract_address = shiba_deploy_receipt
    for key in chain_config["contract_address_path"]:
        shiba_contract_address = shiba_contract_address[key]

    # Deploy Multi Read ERC20 Contract
    multi_read_deploy_tx_hash = client_doge.deploy_contract(
        code=multi_read_erc20_code, account=from_account_doge, args=[]
    )

    # Wait for multi-read deployment
    multi_read_wait_kwargs = {
        "transaction_hash": multi_read_deploy_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        multi_read_wait_kwargs["retries"] = chain_config["retries"]

    multi_read_deploy_receipt = client_doge.wait_for_transaction_receipt(**multi_read_wait_kwargs)
    assert tx_execution_succeeded(multi_read_deploy_receipt)

    # Extract multi-read contract address
    multi_read_contract_address = multi_read_deploy_receipt
    for key in chain_config["contract_address_path"]:
        multi_read_contract_address = multi_read_contract_address[key]

    # Update balances for doge account
    update_balances_doge_tx_hash = client_doge.write_contract(
        address=multi_read_contract_address,
        function_name="update_token_balances",
        args=[from_account_doge.address, [doge_contract_address, shiba_contract_address]],
    )

    # Wait for update_token_balances transaction
    update_balances_doge_wait_kwargs = {
        "transaction_hash": update_balances_doge_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_balances_doge_wait_kwargs["retries"] = chain_config["retries"]

    update_balances_doge_receipt = client_doge.wait_for_transaction_receipt(**update_balances_doge_wait_kwargs)
    assert tx_execution_succeeded(update_balances_doge_receipt)

    # Check balances
    balances_1 = client_doge.read_contract(
        address=multi_read_contract_address,
        function_name="get_balances",
    )
    assert balances_1 == {
        from_account_doge.address: {
            doge_contract_address: TOKEN_TOTAL_SUPPLY,
            shiba_contract_address: 0,
        }
    }

    # Update balances for shiba account
    update_balances_shiba_tx_hash = client_shiba.write_contract(
        address=multi_read_contract_address,
        function_name="update_token_balances",
        args=[from_account_shiba.address, [doge_contract_address, shiba_contract_address]],
    )

    # Wait for update_token_balances transaction
    update_balances_shiba_wait_kwargs = {
        "transaction_hash": update_balances_shiba_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        update_balances_shiba_wait_kwargs["retries"] = chain_config["retries"]

    update_balances_shiba_receipt = client_shiba.wait_for_transaction_receipt(**update_balances_shiba_wait_kwargs)
    assert tx_execution_succeeded(update_balances_shiba_receipt)

    # Check balances
    balances_2 = client_shiba.read_contract(
        address=multi_read_contract_address,
        function_name="get_balances",
    )

    assert balances_2 == {
        from_account_doge.address: {
            doge_contract_address: TOKEN_TOTAL_SUPPLY,
            shiba_contract_address: 0,
        },
        from_account_shiba.address: {
            doge_contract_address: 0,
            shiba_contract_address: TOKEN_TOTAL_SUPPLY,
        },
    }
