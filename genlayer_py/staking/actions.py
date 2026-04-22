"""Staking actions for GenLayerClient.

Mirrors the genlayer-js StakingActions module. All methods operate on
the Staking contract at `chain.staking_contract["address"]` except the
validator-wallet-only writes (validatorDeposit, validatorExit), which
route through the ValidatorWallet so msg.sender on Staking is the
wallet contract — not the operator EOA — per the on-chain sender check.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from eth_account.signers.local import LocalAccount
from eth_typing import Address, ChecksumAddress
from hexbytes import HexBytes

from genlayer_py.exceptions import GenLayerError
from genlayer_py.staking.abi import STAKING_ABI, VALIDATOR_WALLET_ABI

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


AddressLike = Union[Address, ChecksumAddress, str]


def _require_staking(self: "GenLayerClient") -> ChecksumAddress:
    if self.chain.staking_contract is None:
        raise GenLayerError(
            "staking_contract not configured for this chain — set chain.staking_contract"
        )
    return self.w3.to_checksum_address(self.chain.staking_contract["address"])


def _staking(self: "GenLayerClient"):
    return self.w3.eth.contract(address=_require_staking(self), abi=STAKING_ABI)


def _wallet(self: "GenLayerClient", validator: AddressLike):
    return self.w3.eth.contract(
        address=self.w3.to_checksum_address(validator), abi=VALIDATOR_WALLET_ABI
    )


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


# ─── read methods ─────────────────────────────────────────────────────


def epoch(self: "GenLayerClient") -> int:
    return _staking(self).functions.epoch().call()


def active_validators(self: "GenLayerClient") -> List[ChecksumAddress]:
    return _staking(self).functions.activeValidators().call()


def active_validators_count(self: "GenLayerClient") -> int:
    return _staking(self).functions.activeValidatorsCount().call()


def is_validator(self: "GenLayerClient", address: AddressLike) -> bool:
    return (
        _staking(self)
        .functions.isValidator(self.w3.to_checksum_address(address))
        .call()
    )


def get_validator_info(self: "GenLayerClient", validator: AddressLike) -> dict:
    """Returns the raw validatorView struct for a validator wallet."""
    return (
        _staking(self)
        .functions.validatorView(self.w3.to_checksum_address(validator))
        .call()
    )


def get_stake_info(
    self: "GenLayerClient", delegator: AddressLike, validator: AddressLike
) -> tuple:
    """Returns (shares, stake) for a delegator on a specific validator."""
    return (
        _staking(self)
        .functions.stakeOf(
            self.w3.to_checksum_address(delegator),
            self.w3.to_checksum_address(validator),
        )
        .call()
    )


def banned_validators(
    self: "GenLayerClient", start_index: int = 0, size: int = 100
) -> List[ChecksumAddress]:
    return _staking(self).functions.banned(start_index, size).call()


def validator_min_stake(self: "GenLayerClient") -> int:
    return _staking(self).functions.validatorMinStake().call()


def delegator_min_stake(self: "GenLayerClient") -> int:
    return _staking(self).functions.delegatorMinStake().call()


# ─── write methods ────────────────────────────────────────────────────


def validator_join(
    self: "GenLayerClient",
    amount: int,
    operator: Optional[AddressLike] = None,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Joins as a validator with `amount` GEN stake. Deploys a new
    ValidatorWallet. Returns the tx hash — call get_validator_info on
    the resulting wallet address to discover it (or parse the receipt
    for the ValidatorJoin event)."""
    sender = _sender(self, account)
    contract = _staking(self)
    # Staking.validatorJoin has two overloads — () and (address) — so
    # web3.py needs the full signature, not the name alone.
    if operator is not None:
        op = self.w3.to_checksum_address(operator)
        data = contract.encode_abi("validatorJoin(address)", args=[op])
    else:
        data = contract.encode_abi("validatorJoin()", args=[])
    tx = _build(self, sender, _require_staking(self), data, value=amount)
    return _send(self, sender, tx)


def validator_deposit(
    self: "GenLayerClient",
    validator: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Adds self-stake to an active validator position. Sent through
    the ValidatorWallet so that Staking sees msg.sender == wallet."""
    sender = _sender(self, account)
    wallet = _wallet(self, validator)
    data = wallet.encode_abi("validatorDeposit", args=[])
    tx = _build(self, sender, self.w3.to_checksum_address(validator), data, value=amount)
    return _send(self, sender, tx)


def validator_exit(
    self: "GenLayerClient",
    validator: AddressLike,
    shares: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Burns `shares` of a validator position. Routed through wallet."""
    sender = _sender(self, account)
    wallet = _wallet(self, validator)
    data = wallet.encode_abi("validatorExit", args=[shares])
    tx = _build(self, sender, self.w3.to_checksum_address(validator), data)
    return _send(self, sender, tx)


def validator_claim(
    self: "GenLayerClient",
    validator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Claims pending withdrawals on a validator. Staking accepts this
    from any caller (it just pays out to the validator wallet owner)."""
    sender = _sender(self, account)
    contract = _staking(self)
    data = contract.encode_abi(
        "validatorClaim", args=[self.w3.to_checksum_address(validator)]
    )
    tx = _build(self, sender, _require_staking(self), data)
    return _send(self, sender, tx)


def validator_prime(
    self: "GenLayerClient",
    validator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Primes a validator for the next epoch."""
    sender = _sender(self, account)
    contract = _staking(self)
    data = contract.encode_abi(
        "validatorPrime", args=[self.w3.to_checksum_address(validator)]
    )
    tx = _build(self, sender, _require_staking(self), data)
    return _send(self, sender, tx)


def set_operator(
    self: "GenLayerClient",
    validator: AddressLike,
    operator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Rotates the operator for an existing ValidatorWallet. Only the
    wallet owner (the EOA that called validator_join) may do this."""
    sender = _sender(self, account)
    wallet = _wallet(self, validator)
    data = wallet.encode_abi(
        "setOperator", args=[self.w3.to_checksum_address(operator)]
    )
    tx = _build(self, sender, self.w3.to_checksum_address(validator), data)
    return _send(self, sender, tx)


def set_identity(
    self: "GenLayerClient",
    validator: AddressLike,
    moniker: str,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Sets the public moniker for a validator wallet."""
    sender = _sender(self, account)
    wallet = _wallet(self, validator)
    data = wallet.encode_abi("setIdentity", args=[moniker])
    tx = _build(self, sender, self.w3.to_checksum_address(validator), data)
    return _send(self, sender, tx)


def delegator_join(
    self: "GenLayerClient",
    validator: AddressLike,
    amount: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Delegates `amount` GEN to a validator."""
    sender = _sender(self, account)
    contract = _staking(self)
    data = contract.encode_abi(
        "delegatorJoin", args=[self.w3.to_checksum_address(validator)]
    )
    tx = _build(self, sender, _require_staking(self), data, value=amount)
    return _send(self, sender, tx)


def delegator_exit(
    self: "GenLayerClient",
    validator: AddressLike,
    shares: int,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Burns `shares` of a delegator position on a specific validator."""
    sender = _sender(self, account)
    contract = _staking(self)
    data = contract.encode_abi(
        "delegatorExit", args=[self.w3.to_checksum_address(validator), shares]
    )
    tx = _build(self, sender, _require_staking(self), data)
    return _send(self, sender, tx)


def delegator_claim(
    self: "GenLayerClient",
    validator: AddressLike,
    account: Optional[LocalAccount] = None,
) -> HexBytes:
    """Claims pending delegator withdrawals from a validator."""
    sender = _sender(self, account)
    contract = _staking(self)
    data = contract.encode_abi(
        "delegatorClaim", args=[self.w3.to_checksum_address(validator)]
    )
    tx = _build(self, sender, _require_staking(self), data)
    return _send(self, sender, tx)
