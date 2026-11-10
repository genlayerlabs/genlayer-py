"""Vesting actions for GenLayerClient.

Mirrors the genlayer_py.staking actions module. Beneficiary write
methods operate on a per-beneficiary Vesting contract address. Factory
discovery methods operate on a VestingFactory contract address.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from eth_account.signers.local import LocalAccount
from eth_typing import Address, ChecksumAddress
from hexbytes import HexBytes

from genlayer_py.exceptions import GenLayerError
from genlayer_py.vesting.abi import VESTING_ABI

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


AddressLike = Union[Address, ChecksumAddress, str]
ExtraCidLike = Union[str, bytes, bytearray, HexBytes]


def _vesting_address(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> ChecksumAddress:
    return self.w3.to_checksum_address(vesting_contract_address)


def _vesting(self: "GenLayerClient", vesting_contract_address: AddressLike):
    return self.w3.eth.contract(
        address=_vesting_address(self, vesting_contract_address), abi=VESTING_ABI
    )


def _vesting_factory(self: "GenLayerClient", vesting_factory_address: AddressLike):
    return self.w3.eth.contract(
        address=self.w3.to_checksum_address(vesting_factory_address),
        abi=VESTING_ABI,
    )


def _extra_cid(extra_cid: Optional[ExtraCidLike]) -> bytes:
    if not extra_cid:
        return b""
    if isinstance(extra_cid, str):
        if extra_cid.startswith("0x"):
            return bytes(HexBytes(extra_cid))
        return extra_cid.encode()
    return bytes(extra_cid)


def _sender(
    self: "GenLayerClient", account: Optional[LocalAccount]
) -> LocalAccount:
    acct = account or self.local_account
    if acct is None:
        raise GenLayerError("No account provided and client has no local_account")
    return acct


def _send(
    self: "GenLayerClient",
    account: LocalAccount,
    tx: dict,
) -> HexBytes:
    """Sign and broadcast a prepared transaction dict."""
    signed = account.sign_transaction(tx)
    return self.w3.eth.send_raw_transaction(signed.raw_transaction)


def _build(
    self: "GenLayerClient",
    account: LocalAccount,
    to: ChecksumAddress,
    data: bytes,
    value: int = 0,
    gas: Optional[int] = None,
) -> dict:
    tx = {
        "from": account.address,
        "to": to,
        "data": data,
        "value": value,
        "nonce": self.w3.eth.get_transaction_count(account.address),
        "chainId": self.chain.id,
    }
    # Lean on the node's eth_estimateGas unless caller overrode it.
    tx["gas"] = gas if gas is not None else self.w3.eth.estimate_gas(tx) * 2
    tx["gasPrice"] = self.w3.eth.gas_price
    return tx


# --- read methods -----------------------------------------------------


def vested_amount(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> int:
    return _vesting(self, vesting_contract_address).functions.vestedAmount().call()


def unvested_amount(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> int:
    return _vesting(self, vesting_contract_address).functions.unvestedAmount().call()


def withdrawable_amount(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> int:
    return (
        _vesting(self, vesting_contract_address)
        .functions.withdrawableAmount()
        .call()
    )


def get_vesting_schedule(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> dict:
    contract = _vesting(self, vesting_contract_address)
    return {
        "name": contract.functions.name().call(),
        "category": contract.functions.category().call(),
        "beneficiary": contract.functions.beneficiary().call(),
        "creator": contract.functions.creator().call(),
        "revoker": contract.functions.revoker().call(),
        "factory": contract.functions.factory().call(),
        "total_amount": contract.functions.totalAmount().call(),
        "start_date": contract.functions.startDate().call(),
        "cliff_duration": contract.functions.cliffDuration().call(),
        "period_duration": contract.functions.periodDuration().call(),
        "number_of_periods": contract.functions.numberOfPeriods().call(),
        "cliff_unlock_bps": contract.functions.cliffUnlockBps().call(),
        "needs_manual_unlock": contract.functions.needsManualUnlock().call(),
    }


def get_vesting_state(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> dict:
    contract = _vesting(self, vesting_contract_address)
    return {
        "manual_unlocked": contract.functions.manualUnlocked().call(),
        "revoked": contract.functions.revoked().call(),
        "vesting_stopped": contract.functions.vestingStopped().call(),
        "total_withdrawn": contract.functions.totalWithdrawn().call(),
        "vested_at_revocation": contract.functions.vestedAtRevocation().call(),
        "total_amount_at_revocation": contract.functions.totalAmountAtRevocation()
        .call(),
        "revoked_at": contract.functions.revokedAt().call(),
        "vesting_stopped_at": contract.functions.vestingStoppedAt().call(),
        "vested_at_stop": contract.functions.vestedAtStop().call(),
        "accumulated_rewards": contract.functions.accumulatedRewards().call(),
        "accumulated_losses": contract.functions.accumulatedLosses().call(),
        "vested_amount": contract.functions.vestedAmount().call(),
        "unvested_amount": contract.functions.unvestedAmount().call(),
        "withdrawable_amount": contract.functions.withdrawableAmount().call(),
    }


def get_vesting_stake_info(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    validator: AddressLike,
) -> dict:
    contract = _vesting(self, vesting_contract_address)
    validator_address = self.w3.to_checksum_address(validator)
    return {
        "deposited": contract.functions.depositedPerValidator(
            validator_address
        ).call(),
        "pending_exit_deposited": contract.functions.pendingExitDeposited(
            validator_address
        ).call(),
    }


def get_validator_wallets(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> List[ChecksumAddress]:
    return (
        _vesting(self, vesting_contract_address)
        .functions.getValidatorWallets()
        .call()
    )


def validator_wallet_count(
    self: "GenLayerClient", vesting_contract_address: AddressLike
) -> int:
    return (
        _vesting(self, vesting_contract_address)
        .functions.validatorWalletCount()
        .call()
    )


def validator_deposited(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
) -> int:
    return (
        _vesting(self, vesting_contract_address)
        .functions.validatorDeposited(self.w3.to_checksum_address(wallet))
        .call()
    )


def is_validator_wallet(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
) -> bool:
    return (
        _vesting(self, vesting_contract_address)
        .functions.isValidatorWallet(self.w3.to_checksum_address(wallet))
        .call()
    )


def get_vesting_contract(
    self: "GenLayerClient",
    vesting_factory_address: AddressLike,
    beneficiary: AddressLike,
) -> ChecksumAddress:
    contract = _vesting_factory(self, vesting_factory_address)
    vesting_contract_address = contract.functions.getVesting(
        self.w3.to_checksum_address(beneficiary)
    ).call()
    return self.w3.to_checksum_address(vesting_contract_address)


# --- write methods ----------------------------------------------------


def vesting_delegator_join(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    validator: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Delegates `amount` GEN from a Vesting contract to a validator."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingDelegatorJoin",
        args=[self.w3.to_checksum_address(validator), amount],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_delegator_exit(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    validator: AddressLike,
    shares: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Burns `shares` of a Vesting contract's delegation position."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingDelegatorExit",
        args=[self.w3.to_checksum_address(validator), shares],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_delegator_claim(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    validator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Claims exited staking funds back into the Vesting contract."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingDelegatorClaim", args=[self.w3.to_checksum_address(validator)]
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_join(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    operator: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Creates a validator wallet using GEN from a Vesting contract."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorJoin",
        args=[self.w3.to_checksum_address(operator), amount],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_deposit(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Adds Vesting-held GEN to one of the Vesting validator wallets."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorDeposit",
        args=[self.w3.to_checksum_address(wallet), amount],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_exit(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    shares: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Burns `shares` from a Vesting-owned validator wallet."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorExit",
        args=[self.w3.to_checksum_address(wallet), shares],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_claim(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Claims exited validator self-stake back into the Vesting contract."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorClaim", args=[self.w3.to_checksum_address(wallet)]
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_initiate_operator_transfer(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    new_operator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Begins operator transfer for a Vesting-owned validator wallet."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorInitiateOperatorTransfer",
        args=[
            self.w3.to_checksum_address(wallet),
            self.w3.to_checksum_address(new_operator),
        ],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_complete_operator_transfer(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Completes operator transfer for a Vesting-owned validator wallet."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorCompleteOperatorTransfer",
        args=[self.w3.to_checksum_address(wallet)],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_cancel_operator_transfer(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Cancels operator transfer for a Vesting-owned validator wallet."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorCancelOperatorTransfer",
        args=[self.w3.to_checksum_address(wallet)],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_validator_set_identity(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    wallet: AddressLike,
    moniker: str,
    logo_uri: str,
    website: str,
    description: str,
    email: str,
    twitter: str,
    telegram: str,
    github: str,
    extra_cid: Optional[ExtraCidLike] = None,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Sets identity metadata on a Vesting-owned validator wallet."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi(
        "vestingValidatorSetIdentity",
        args=[
            self.w3.to_checksum_address(wallet),
            moniker,
            logo_uri,
            website,
            description,
            email,
            twitter,
            telegram,
            github,
            _extra_cid(extra_cid),
        ],
    )
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)


def vesting_withdraw(
    self: "GenLayerClient",
    vesting_contract_address: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Withdraws vested tokens from a Vesting contract to its beneficiary."""
    sender = _sender(self, account)
    contract = _vesting(self, vesting_contract_address)
    data = contract.encode_abi("vestingWithdraw", args=[amount])
    vesting_address = _vesting_address(self, vesting_contract_address)
    tx = _build(self, sender, vesting_address, data)
    return _send(self, sender, tx)
