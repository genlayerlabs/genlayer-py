import pytest
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from genlayer_py import create_client, create_account
from genlayer_py.chains import localnet
from genlayer_py.assertions import tx_execution_succeeded, tx_execution_failed

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
    ],
)
def test_simple_time_contract(chain_config):
    """Test all time-based functionality in a single comprehensive test."""

    # Create account based on chain requirements
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    with open(f"{CONTRACTS_DIR}/simple_time_contract.py", "r") as f:
        code = f.read()

    # Test 1: Deploy with past start date (10 days ago)
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).isoformat()
    deploy_tx_hash = client.deploy_contract(
        code=code, account=account, args=[past_date]
    )

    # Wait for transaction with retries if specified
    wait_kwargs = {
        "transaction_hash": deploy_tx_hash,
    }
    if chain_config["retries"]:
        wait_kwargs["retries"] = chain_config["retries"]

    deploy_receipt = client.wait_for_transaction_receipt(**wait_kwargs)
    assert tx_execution_succeeded(deploy_receipt)

    # Extract contract address based on chain-specific path
    contract_address = deploy_receipt
    for key in chain_config["contract_address_path"]:
        contract_address = contract_address[key]

    # Test 1: Check initial status (10 days after start)
    status = client.read_contract(
        address=contract_address,
        function_name="get_status",
    )
    assert status["is_active"] == False
    assert status["days_since_start"] == 10
    assert status["can_activate"] == True

    # Test 2: Try to activate before start date (simulate going back in time)
    before_start_date = now - timedelta(days=15)  # 5 days before start
    before_start_date_tx_hash = client.write_contract(
            address=contract_address,
            function_name="activate",
            args=[],
            sim_config={
                "genvm_datetime": before_start_date.isoformat(),
            },
        )
    before_start_date_receipt = client.wait_for_transaction_receipt(
        transaction_hash=before_start_date_tx_hash,
    )
    assert tx_execution_failed(before_start_date_receipt)

    # Test 3: Activate after start date
    activate_date = now - timedelta(days=5)  # 5 days after start (15 days ago + 10)
    activate_tx_hash = client.write_contract(
        address=contract_address,
        function_name="activate",
        args=[],
        sim_config={
            "genvm_datetime": activate_date.isoformat(),
        },
    )

    activate_wait_kwargs = {
        "transaction_hash": activate_tx_hash,
    }
    if chain_config["retries"]:
        activate_wait_kwargs["retries"] = chain_config["retries"]

    activate_receipt = client.wait_for_transaction_receipt(**activate_wait_kwargs)
    assert tx_execution_succeeded(activate_receipt)

    # Test 4: Verify activation and check status
    status = client.read_contract(
        address=contract_address,
        function_name="get_status",
        sim_config={
            "genvm_datetime": activate_date.isoformat(),
        },
    )
    assert status["is_active"] == True
    assert status["days_since_start"] == 5
    assert status["can_set_data"] == True

    # Test 5: Set data within valid period (within 30 days)
    set_data_date = now - timedelta(days=2)  # 8 days after start
    test_data = "Test data within valid period"
    set_data_tx_hash = client.write_contract(
        address=contract_address,
        function_name="set_data",
        args=[test_data],
        sim_config={
            "genvm_datetime": set_data_date.isoformat(),
        },
    )

    set_data_wait_kwargs = {
        "transaction_hash": set_data_tx_hash,
    }
    if chain_config["retries"]:
        set_data_wait_kwargs["retries"] = chain_config["retries"]

    set_data_receipt = client.wait_for_transaction_receipt(**set_data_wait_kwargs)
    assert tx_execution_succeeded(set_data_receipt)

    # Test 6: Verify data was set
    status = client.read_contract(
        address=contract_address,
        function_name="get_status",
        sim_config={
            "genvm_datetime": set_data_date.isoformat(),
        },
    )
    assert status["data"] == test_data
    assert status["days_since_start"] == 8

    # Test 7: Try to set data after 30 days (should fail)
    expired_date = now + timedelta(days=25)  # 35 days after start
    expired_date_tx_hash = client.write_contract(
            address=contract_address,
            function_name="set_data",
            args=["Should fail - expired"],
            sim_config={
                "genvm_datetime": expired_date.isoformat(),
            },
        )
    expired_date_receipt = client.wait_for_transaction_receipt(
        transaction_hash=expired_date_tx_hash,
    )
    assert tx_execution_failed(expired_date_receipt)


    # Test 8: Check status shows expired
    status = client.read_contract(
        address=contract_address,
        function_name="get_status",
        sim_config={
            "genvm_datetime": expired_date.isoformat(),
        },
    )
    assert status["is_active"] == True  # Still active
    assert status["can_set_data"] == False  # But can't set data
    assert status["days_since_start"] == 35
