import pytest
import os
import io
import zipfile
from pathlib import Path
from dotenv import load_dotenv

from genlayer_py import create_client, create_account
from genlayer_py.chains import localnet, studionet, testnet_asimov
from genlayer_py.types import TransactionStatus
from genlayer_py.assertions import tx_execution_succeeded

# Load environment variables from .env file
load_dotenv()

account_private_key_1 = os.getenv("ACCOUNT_PRIVATE_KEY_1")

CONTRACTS_DIR = "tests/e2e/contracts"


def compute_multi_file_contract_code(contract_dir_path: Path) -> bytes:
    """Compute the contract code for multi-file contracts by creating a zip file."""
    main_file_path = contract_dir_path / "__init__.py"
    runner_file_path = contract_dir_path / "runner.json"

    if not main_file_path.exists():
        raise FileNotFoundError(f"Main contract file not found at: {main_file_path}")

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, mode="w") as zip_file:
        # Add main contract file as contract/__init__.py
        zip_file.write(main_file_path, "contract/__init__.py")

        # Add all other files in the directory
        for file_path in contract_dir_path.rglob("*"):
            if file_path.name in ["runner.json", "__init__.py"] or file_path.is_dir():
                continue
            rel_path = file_path.relative_to(contract_dir_path)
            zip_file.write(file_path, f"contract/{rel_path}")

        # Add runner.json if it exists
        if runner_file_path.exists():
            zip_file.write(runner_file_path, "runner.json")

    buffer.flush()
    return buffer.getvalue()


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
def test_multi_file_contract(chain_config):
    # Create account based on chain requirements
    if chain_config["account_kwargs"]:
        account = create_account(**chain_config["account_kwargs"])
    else:
        account = create_account()

    client = create_client(chain=chain_config["chain"], account=account)

    # Load multi-file contract code
    contract_dir_path = Path(CONTRACTS_DIR) / "multi_file_contract"
    if not contract_dir_path.exists():
        raise FileNotFoundError(
            f"Multi-file contract directory not found at: {contract_dir_path}"
        )

    contract_code = compute_multi_file_contract_code(contract_dir_path)

    # Deploy Contract
    deploy_tx_hash = client.deploy_contract(
        code=contract_code, account=account, args=[]
    )
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
    assert tx_execution_succeeded(deploy_receipt)

    # Extract contract address based on chain-specific path
    contract_address = deploy_receipt
    for key in chain_config["contract_address_path"]:
        contract_address = contract_address[key]

    # Call wait method
    wait_tx_hash = client.write_contract(
        address=contract_address,
        function_name="wait",
        args=[],
    )
    print("wait_tx_hash", wait_tx_hash)
    # Wait for wait transaction
    wait_wait_kwargs = {
        "transaction_hash": wait_tx_hash,
        "status": TransactionStatus.FINALIZED,
    }
    if chain_config["retries"]:
        wait_wait_kwargs["retries"] = chain_config["retries"]

    wait_receipt = client.wait_for_transaction_receipt(**wait_wait_kwargs)
    print("wait_receipt", wait_receipt)
    assert tx_execution_succeeded(wait_receipt)

    # Call test method
    # contract_address = "0x18556f39288cBb53F1F88BefEda2DA805D890cB6"
    res = client.read_contract(
        address=contract_address,
        function_name="test",
    )
    assert res == "123"
