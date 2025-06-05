from genlayer_py import create_client, create_account
from genlayer_py.chains import testnet_asimov
from genlayer_py.types import TransactionStatus
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

account_private_key = os.getenv("ACCOUNT_PRIVATE_KEY")


def test_storage_interaction():
    account = create_account(account_private_key=account_private_key)
    client = create_client(chain=testnet_asimov, account=account)

    with open("contracts/storage.py", "r") as f:
        code = f.read()

    initial_storage = "initial storage"
    deploy_tx_hash = client.deploy_contract(
        code=code, account=account, args=[initial_storage]
    )
    deploy_receipt = client.wait_for_transaction_receipt(
        transaction_hash=deploy_tx_hash, status=TransactionStatus.FINALIZED, retries=40
    )
    # Different than localnet
    contract_address = deploy_receipt["tx_data_decoded"]["contract_address"]

    storage = client.read_contract(
        address=contract_address,
        function_name="get_storage",
    )

    assert storage == initial_storage

    new_storage = "new storage"
    write_tx_hash = client.write_contract(
        address=contract_address,
        function_name="update_storage",
        args=[new_storage],
    )

    write_receipt = client.wait_for_transaction_receipt(
        transaction_hash=write_tx_hash, status=TransactionStatus.FINALIZED, retries=40
    )

    storage = client.read_contract(
        address=contract_address,
        function_name="get_storage",
    )

    assert storage == new_storage
