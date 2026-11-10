"""Unit tests for the vesting action module.

The tests here are structural, matching the staking action tests: write
helpers are checked for ABI selectors and target addresses, while read
helpers use mocked contract calls instead of a live node.
"""

from types import SimpleNamespace
from unittest.mock import Mock

from eth_utils import keccak
import pytest
from web3 import Web3

import genlayer_py.vesting.actions as vesting_actions
from genlayer_py.vesting.abi import VESTING_ABI


VESTING_ADDR = "0x1111111111111111111111111111111111111111"
FACTORY_ADDR = "0x2222222222222222222222222222222222222222"
SENDER_ADDR = "0x3333333333333333333333333333333333333333"
VALIDATOR_ADDR = "0x4444444444444444444444444444444444444444"
BENEFICIARY_ADDR = "0x5555555555555555555555555555555555555555"
CREATOR_ADDR = "0x6666666666666666666666666666666666666666"
REVOKER_ADDR = "0x7777777777777777777777777777777777777777"
WALLET_ADDR = "0x8888888888888888888888888888888888888888"
NEW_OPERATOR_ADDR = "0x9999999999999999999999999999999999999999"

SEL_VESTING_DELEGATOR_JOIN = keccak(
    text="vestingDelegatorJoin(address,uint256)"
)[:4].hex()
SEL_VESTING_DELEGATOR_EXIT = keccak(
    text="vestingDelegatorExit(address,uint256)"
)[:4].hex()
SEL_VESTING_DELEGATOR_CLAIM = keccak(text="vestingDelegatorClaim(address)")[
    :4
].hex()
SEL_VESTING_VALIDATOR_JOIN = keccak(
    text="vestingValidatorJoin(address,uint256)"
)[:4].hex()
SEL_VESTING_VALIDATOR_DEPOSIT = keccak(
    text="vestingValidatorDeposit(address,uint256)"
)[:4].hex()
SEL_VESTING_VALIDATOR_EXIT = keccak(
    text="vestingValidatorExit(address,uint256)"
)[:4].hex()
SEL_VESTING_VALIDATOR_CLAIM = keccak(text="vestingValidatorClaim(address)")[
    :4
].hex()
SEL_VESTING_VALIDATOR_INITIATE_OPERATOR_TRANSFER = keccak(
    text="vestingValidatorInitiateOperatorTransfer(address,address)"
)[:4].hex()
SEL_VESTING_VALIDATOR_COMPLETE_OPERATOR_TRANSFER = keccak(
    text="vestingValidatorCompleteOperatorTransfer(address)"
)[:4].hex()
SEL_VESTING_VALIDATOR_CANCEL_OPERATOR_TRANSFER = keccak(
    text="vestingValidatorCancelOperatorTransfer(address)"
)[:4].hex()
SEL_VESTING_VALIDATOR_SET_IDENTITY = keccak(
    text=(
        "vestingValidatorSetIdentity("
        "address,string,string,string,string,string,string,string,string,bytes)"
    )
)[:4].hex()
SEL_VESTING_WITHDRAW = keccak(text="vestingWithdraw(uint256)")[:4].hex()


def _make_client():
    """SimpleNamespace stand-in for GenLayerClient.

    Uses a real Web3().eth for contract encoding, but patches the eth
    methods that would otherwise hit a live node.
    """
    signed = SimpleNamespace(raw_transaction=b"\x00")
    w3 = Web3()
    w3.eth.get_transaction_count = Mock(return_value=1)
    w3.eth.estimate_gas = Mock(return_value=100_000)
    w3.eth.send_raw_transaction = Mock(return_value=b"\xde\xad" * 16)
    type(w3.eth).gas_price = 1_000_000_000  # type: ignore[assignment]

    local_account = SimpleNamespace(
        address=SENDER_ADDR,
        sign_transaction=Mock(return_value=signed),
    )
    chain = SimpleNamespace(id=61999)
    return SimpleNamespace(chain=chain, local_account=local_account, w3=w3)


def _last_tx(client):
    """Return the tx dict the client's sign_transaction was called with."""
    return client.local_account.sign_transaction.call_args.args[0]


def _call_result(value):
    return SimpleNamespace(call=Mock(return_value=value))


def _decode_vesting_tx(client, data):
    contract = client.w3.eth.contract(
        address=client.w3.to_checksum_address(VESTING_ADDR), abi=VESTING_ABI
    )
    return contract.decode_function_input(data)


def test_vesting_delegator_join_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_delegator_join(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        validator=VALIDATOR_ADDR,
        amount=10,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["value"] == 0
    assert tx["data"][2:10] == SEL_VESTING_DELEGATOR_JOIN


def test_vesting_delegator_exit_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_delegator_exit(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        validator=VALIDATOR_ADDR,
        shares=42,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_DELEGATOR_EXIT


def test_vesting_delegator_claim_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_delegator_claim(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        validator=VALIDATOR_ADDR,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_DELEGATOR_CLAIM


def test_vesting_withdraw_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_withdraw(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        amount=7,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_WITHDRAW


def test_vesting_validator_join_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_join(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        operator=VALIDATOR_ADDR,
        amount=10,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["value"] == 0
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_JOIN


def test_vesting_validator_deposit_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_deposit(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
        amount=25,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["value"] == 0
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_DEPOSIT


def test_vesting_validator_exit_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_exit(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
        shares=42,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_EXIT


def test_vesting_validator_claim_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_claim(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_CLAIM


def test_vesting_validator_initiate_operator_transfer_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_initiate_operator_transfer(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
        new_operator=NEW_OPERATOR_ADDR,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_INITIATE_OPERATOR_TRANSFER


def test_vesting_validator_complete_operator_transfer_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_complete_operator_transfer(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_COMPLETE_OPERATOR_TRANSFER


def test_vesting_validator_cancel_operator_transfer_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_cancel_operator_transfer(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
    )
    tx = _last_tx(client)
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_CANCEL_OPERATOR_TRANSFER


def test_vesting_validator_set_identity_targets_vesting_contract():
    client = _make_client()
    vesting_actions.vesting_validator_set_identity(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
        moniker="validator",
        logo_uri="logo",
        website="site",
        description="desc",
        email="email",
        twitter="tw",
        telegram="tg",
        github="gh",
        extra_cid="cid",
    )
    tx = _last_tx(client)
    _, args = _decode_vesting_tx(client, tx["data"])
    assert tx["to"].lower() == VESTING_ADDR.lower()
    assert tx["data"][2:10] == SEL_VESTING_VALIDATOR_SET_IDENTITY
    assert args["extraCid"] == b"cid"


def test_vesting_validator_set_identity_preserves_hex_extra_cid():
    client = _make_client()
    vesting_actions.vesting_validator_set_identity(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
        moniker="validator",
        logo_uri="logo",
        website="site",
        description="desc",
        email="email",
        twitter="tw",
        telegram="tg",
        github="gh",
        extra_cid="0x1234",
    )
    tx = _last_tx(client)
    _, args = _decode_vesting_tx(client, tx["data"])
    assert args["extraCid"] == b"\x12\x34"


def test_write_requires_account():
    client = _make_client()
    client.local_account = None
    with pytest.raises(Exception, match="No account provided"):
        vesting_actions.vesting_withdraw(
            self=client,
            vesting_contract_address=VESTING_ADDR,
            amount=7,
        )


def test_vested_unvested_and_withdrawable_amount_reads():
    client = _make_client()
    functions = SimpleNamespace(
        vestedAmount=Mock(return_value=_call_result(11)),
        unvestedAmount=Mock(return_value=_call_result(22)),
        withdrawableAmount=Mock(return_value=_call_result(33)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    assert (
        vesting_actions.vested_amount(
            self=client, vesting_contract_address=VESTING_ADDR
        )
        == 11
    )
    assert (
        vesting_actions.unvested_amount(
            self=client, vesting_contract_address=VESTING_ADDR
        )
        == 22
    )
    assert (
        vesting_actions.withdrawable_amount(
            self=client, vesting_contract_address=VESTING_ADDR
        )
        == 33
    )


def test_get_vesting_schedule_reads_schedule_fields():
    client = _make_client()
    functions = SimpleNamespace(
        name=Mock(return_value=_call_result("Founder")),
        category=Mock(return_value=_call_result(1)),
        beneficiary=Mock(return_value=_call_result(BENEFICIARY_ADDR)),
        creator=Mock(return_value=_call_result(CREATOR_ADDR)),
        revoker=Mock(return_value=_call_result(REVOKER_ADDR)),
        factory=Mock(return_value=_call_result(FACTORY_ADDR)),
        totalAmount=Mock(return_value=_call_result(1000)),
        startDate=Mock(return_value=_call_result(100)),
        cliffDuration=Mock(return_value=_call_result(200)),
        periodDuration=Mock(return_value=_call_result(300)),
        numberOfPeriods=Mock(return_value=_call_result(4)),
        cliffUnlockBps=Mock(return_value=_call_result(500)),
        needsManualUnlock=Mock(return_value=_call_result(False)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    schedule = vesting_actions.get_vesting_schedule(
        self=client, vesting_contract_address=VESTING_ADDR
    )

    assert schedule == {
        "name": "Founder",
        "category": 1,
        "beneficiary": BENEFICIARY_ADDR,
        "creator": CREATOR_ADDR,
        "revoker": REVOKER_ADDR,
        "factory": FACTORY_ADDR,
        "total_amount": 1000,
        "start_date": 100,
        "cliff_duration": 200,
        "period_duration": 300,
        "number_of_periods": 4,
        "cliff_unlock_bps": 500,
        "needs_manual_unlock": False,
    }


def test_get_vesting_state_reads_state_fields():
    client = _make_client()
    functions = SimpleNamespace(
        manualUnlocked=Mock(return_value=_call_result(True)),
        revoked=Mock(return_value=_call_result(False)),
        vestingStopped=Mock(return_value=_call_result(False)),
        totalWithdrawn=Mock(return_value=_call_result(1)),
        vestedAtRevocation=Mock(return_value=_call_result(2)),
        totalAmountAtRevocation=Mock(return_value=_call_result(3)),
        revokedAt=Mock(return_value=_call_result(4)),
        vestingStoppedAt=Mock(return_value=_call_result(5)),
        vestedAtStop=Mock(return_value=_call_result(6)),
        accumulatedRewards=Mock(return_value=_call_result(7)),
        accumulatedLosses=Mock(return_value=_call_result(8)),
        vestedAmount=Mock(return_value=_call_result(9)),
        unvestedAmount=Mock(return_value=_call_result(10)),
        withdrawableAmount=Mock(return_value=_call_result(11)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    state = vesting_actions.get_vesting_state(
        self=client, vesting_contract_address=VESTING_ADDR
    )

    assert state == {
        "manual_unlocked": True,
        "revoked": False,
        "vesting_stopped": False,
        "total_withdrawn": 1,
        "vested_at_revocation": 2,
        "total_amount_at_revocation": 3,
        "revoked_at": 4,
        "vesting_stopped_at": 5,
        "vested_at_stop": 6,
        "accumulated_rewards": 7,
        "accumulated_losses": 8,
        "vested_amount": 9,
        "unvested_amount": 10,
        "withdrawable_amount": 11,
    }


def test_get_vesting_stake_info_reads_validator_state():
    client = _make_client()
    functions = SimpleNamespace(
        depositedPerValidator=Mock(return_value=_call_result(123)),
        pendingExitDeposited=Mock(return_value=_call_result(45)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    stake_info = vesting_actions.get_vesting_stake_info(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        validator=VALIDATOR_ADDR,
    )

    assert stake_info == {"deposited": 123, "pending_exit_deposited": 45}
    checksum_validator = client.w3.to_checksum_address(VALIDATOR_ADDR)
    functions.depositedPerValidator.assert_called_once_with(checksum_validator)
    functions.pendingExitDeposited.assert_called_once_with(checksum_validator)


def test_get_validator_wallets_reads_wallet_list():
    client = _make_client()
    functions = SimpleNamespace(
        getValidatorWallets=Mock(return_value=_call_result([WALLET_ADDR])),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    wallets = vesting_actions.get_validator_wallets(
        self=client, vesting_contract_address=VESTING_ADDR
    )

    assert wallets == [WALLET_ADDR]


def test_validator_wallet_count_reads_wallet_count():
    client = _make_client()
    functions = SimpleNamespace(
        validatorWalletCount=Mock(return_value=_call_result(3)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    assert (
        vesting_actions.validator_wallet_count(
            self=client, vesting_contract_address=VESTING_ADDR
        )
        == 3
    )


def test_validator_deposited_reads_wallet_deposit():
    client = _make_client()
    functions = SimpleNamespace(
        validatorDeposited=Mock(return_value=_call_result(123)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    deposited = vesting_actions.validator_deposited(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
    )

    assert deposited == 123
    functions.validatorDeposited.assert_called_once_with(
        client.w3.to_checksum_address(WALLET_ADDR)
    )


def test_is_validator_wallet_reads_membership():
    client = _make_client()
    functions = SimpleNamespace(
        isValidatorWallet=Mock(return_value=_call_result(True)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    is_wallet = vesting_actions.is_validator_wallet(
        self=client,
        vesting_contract_address=VESTING_ADDR,
        wallet=WALLET_ADDR,
    )

    assert is_wallet is True
    functions.isValidatorWallet.assert_called_once_with(
        client.w3.to_checksum_address(WALLET_ADDR)
    )


def test_get_vesting_contract_reads_factory_mapping():
    client = _make_client()
    functions = SimpleNamespace(
        getVesting=Mock(return_value=_call_result(VESTING_ADDR)),
    )
    client.w3.eth.contract = Mock(return_value=SimpleNamespace(functions=functions))

    vesting_contract = vesting_actions.get_vesting_contract(
        self=client,
        vesting_factory_address=FACTORY_ADDR,
        beneficiary=BENEFICIARY_ADDR,
    )

    assert vesting_contract == client.w3.to_checksum_address(VESTING_ADDR)
    client.w3.eth.contract.assert_called_once_with(
        address=client.w3.to_checksum_address(FACTORY_ADDR), abi=VESTING_ABI
    )
    functions.getVesting.assert_called_once_with(
        client.w3.to_checksum_address(BENEFICIARY_ADDR)
    )


def test_abi_includes_expected_functions_and_events():
    """Guard against the bundled ABI JSON drifting or truncating."""
    names = {e["name"] for e in VESTING_ABI if e.get("type") == "function"}
    events = {e["name"] for e in VESTING_ABI if e.get("type") == "event"}
    assert {
        "vestingDelegatorJoin",
        "vestingDelegatorExit",
        "vestingDelegatorClaim",
        "vestingValidatorJoin",
        "vestingValidatorDeposit",
        "vestingValidatorExit",
        "vestingValidatorClaim",
        "vestingValidatorInitiateOperatorTransfer",
        "vestingValidatorCompleteOperatorTransfer",
        "vestingValidatorCancelOperatorTransfer",
        "vestingValidatorSetIdentity",
        "vestingWithdraw",
        "vestedAmount",
        "unvestedAmount",
        "withdrawableAmount",
        "depositedPerValidator",
        "pendingExitDeposited",
        "getValidatorWallets",
        "validatorWalletCount",
        "validatorDeposited",
        "isValidatorWallet",
        "getVesting",
    }.issubset(names)
    assert {
        "TokensWithdrawn",
        "DelegatorJoined",
        "DelegatorExited",
        "DelegatorClaimed",
        "ValidatorJoined",
        "ValidatorDeposited",
        "ValidatorExited",
        "ValidatorClaimed",
        "VestingCreated",
    }.issubset(events)
