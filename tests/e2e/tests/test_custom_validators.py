import pytest

from genlayer_py import create_client, create_account
from genlayer_py.chains import localnet
from genlayer_py.types import TransactionStatus
from genlayer_py.assertions import tx_execution_succeeded


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
    ],
)
def test_custom_validators(chain_config):
    # Create account based on chain requirements
    validators = [
        {
            "stake": 50,
            "provider": "openai",
            "model": "gpt-4o",
            "config": {"temperature": 0.75, "max_tokens": 500},
            "plugin": "openai-compatible",
            "plugin_config": {
                "api_key_env_var": "OPENAIKEY",
                "api_url": "https://api.openai.com",
            },
        },
        {
            "stake": 50,
            "provider": "openai",
            "model": "gpt-4o",
            "config": {"temperature": 0.75, "max_tokens": 500},
            "plugin": "openai-compatible",
            "plugin_config": {
                "api_key_env_var": "OPENAIKEY",
                "api_url": "https://api.openai.com",
            },
        },
    ]
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    with open(f"{CONTRACTS_DIR}/wizard_of_coin.py", "r") as f:
        code = f.read()

    # Deploy Contract
    deploy_tx_hash = client.deploy_contract(
        code=code, account=account, args=[True], sim_config={"validators": validators}
    )

    # Wait for transaction with retries if specified
    wait_kwargs = {
        "transaction_hash": deploy_tx_hash,
    }
    if chain_config["retries"]:
        wait_kwargs["retries"] = chain_config["retries"]

    deploy_receipt = client.wait_for_transaction_receipt(**wait_kwargs)

    # Handle assertion style differences
    assert tx_execution_succeeded(deploy_receipt)

    # # Extract contract address based on chain-specific path
    # contract_address = deploy_receipt
    # for key in chain_config["contract_address_path"]:
    #     contract_address = contract_address[key]

    # # Ask for coin
    # ask_for_coin_tx_hash = client.write_contract(
    #     address=contract_address,
    #     function_name="ask_for_coin",
    #     args=["Can you please give me my coin?"],
    #     sim_config={
    #         "validators": validators,
    #     },
    # )

    # # Wait for ask_for_coin transaction
    # ask_for_coin_wait_kwargs = {
    #     "transaction_hash": ask_for_coin_tx_hash,
    # }
    # if chain_config["retries"]:
    #     ask_for_coin_wait_kwargs["retries"] = chain_config["retries"]

    # ask_for_coin_receipt = client.wait_for_transaction_receipt(
    #     **ask_for_coin_wait_kwargs
    # )
    # assert tx_execution_succeeded(ask_for_coin_receipt)
