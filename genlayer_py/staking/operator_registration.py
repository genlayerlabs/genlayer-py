"""Proof of possession for operator keys.

Consensus requires an operator to prove control of its key before that key is
bound to a validator wallet. The proof is an EIP-191 signature, by the operator
key, over a domain-separated hash of (chainId, registrar, owner, pubKey).

`registrar` is whichever contract verifies the proof, and it differs by flow:
the ValidatorWalletFactory for a validator join, the wallet itself for an
operator rotation (ValidatorWalletBlueprint.initiateOperatorTransfer calls
PubKeyUtils.validateWithPossession(pubKey, address(this), owner(), proof)).
Passing the wrong one produces a proof that simply fails to verify.

The encoding mirrors genlayer-js's createOperatorRegistration exactly — the
shared vector in tests/unit/test_operator_registration.py pins the two
implementations together.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from eth_abi.abi import encode as abi_encode
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address
from eth_utils.crypto import keccak

OPERATOR_REGISTRATION_DOMAIN = keccak(
    text="GenLayer/operatorPubKey/proof-of-possession/v1"
)

OperatorPublicKey = Tuple[int, int]


@dataclass(frozen=True)
class OperatorRegistrationContext:
    """Who verifies the proof, on whose behalf, and on which chain."""

    registrar: ChecksumAddress
    owner: ChecksumAddress
    chain_id: int


@dataclass(frozen=True)
class OperatorRegistrationProof:
    operator: ChecksumAddress
    operator_pub_key: OperatorPublicKey
    possession_proof: bytes


def operator_public_key_from_private_key(private_key: str) -> OperatorPublicKey:
    """Splits the uncompressed secp256k1 public key into the contract's
    uint256[2] tuple."""
    account = Account.from_key(private_key)
    public_key = account._key_obj.public_key.to_bytes()
    return (
        int.from_bytes(public_key[0:32], "big"),
        int.from_bytes(public_key[32:64], "big"),
    )


def operator_address_from_public_key(pub_key: OperatorPublicKey) -> ChecksumAddress:
    raw = pub_key[0].to_bytes(32, "big") + pub_key[1].to_bytes(32, "big")
    return to_checksum_address(keccak(raw)[-20:])


def operator_possession_message(
    pub_key: OperatorPublicKey, context: OperatorRegistrationContext
) -> bytes:
    return keccak(
        abi_encode(
            ["bytes32", "uint256", "address", "address", "uint256", "uint256"],
            [
                OPERATOR_REGISTRATION_DOMAIN,
                context.chain_id,
                context.registrar,
                context.owner,
                pub_key[0],
                pub_key[1],
            ],
        )
    )


def create_operator_registration(
    private_key: str, context: OperatorRegistrationContext
) -> OperatorRegistrationProof:
    """Builds the proof package the proof-bearing calls consume.

    The private key is used only to sign and is never retained in the result.
    """
    account = Account.from_key(private_key)
    pub_key = operator_public_key_from_private_key(private_key)
    operator = operator_address_from_public_key(pub_key)

    if operator != to_checksum_address(account.address):
        raise ValueError(
            "Operator private key and public key derive different identities."
        )

    signed = Account.sign_message(
        encode_defunct(operator_possession_message(pub_key, context)),
        private_key=private_key,
    )

    return OperatorRegistrationProof(
        operator=operator,
        operator_pub_key=pub_key,
        possession_proof=bytes(signed.signature),
    )


def verify_operator_registration(
    registration: OperatorRegistrationProof,
    context: OperatorRegistrationContext,
) -> bool:
    """Checks key identity and the exact registrar/owner/chain binding."""
    if operator_address_from_public_key(registration.operator_pub_key) != to_checksum_address(
        registration.operator
    ):
        return False

    message = encode_defunct(
        operator_possession_message(registration.operator_pub_key, context)
    )
    try:
        recovered = Account.recover_message(
            message, signature=registration.possession_proof
        )
    except Exception:
        return False

    return to_checksum_address(recovered) == to_checksum_address(registration.operator)
