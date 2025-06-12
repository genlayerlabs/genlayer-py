from eth_account import Account
from eth_account.signers.local import LocalAccount

from genlayer_py.accounts.account import generate_private_key, create_account


def test_generate_private_key():
    private_key = generate_private_key()

    # Check that the private key is of the correct type
    assert isinstance(private_key, bytes)
    assert len(private_key) == 32  # Genlayer Private keys are 32 bytes

    # Verify that the private key can be used to create a valid account
    account = Account.from_key(private_key)
    assert isinstance(account, LocalAccount)
    assert account.address is not None
    assert (
        len(account.address) == 42
    )  # Genlayer Addresses are 42 characters (0x + 40 hex chars)


def test_create_account_without_private_key():
    account = create_account()
    assert isinstance(account, LocalAccount)
    assert account.address is not None
    assert len(account.address) == 42


def test_create_account_with_private_key():
    # Generate a private key first
    private_key = generate_private_key()

    # Create an account with the private key
    account = create_account(account_private_key=private_key)

    assert isinstance(account, LocalAccount)
    assert account.address is not None
    assert len(account.address) == 42

    # Create another account with the same private key to verify consistency
    account2 = create_account(account_private_key=private_key)
    assert (
        account.address == account2.address
    )  # Same private key should give same address


def test_create_account_with_none_private_key():
    account1 = create_account()
    account2 = create_account(account_private_key=None)

    assert isinstance(account1, LocalAccount)
    assert isinstance(account2, LocalAccount)
    assert (
        account1.address != account2.address
    )  # Different addresses since different random keys
