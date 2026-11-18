"""Cross-language vector for the operator proof of possession.

The expected values below are the ones genlayer-js asserts in
tests/operator-registration.test.ts. Both SDKs sign proofs the same contract
verifies, so a divergence here is a real interoperability break rather than a
cosmetic difference — pin the exact bytes, not just internal consistency.
"""

from genlayer_py.staking.operator_registration import (
    OPERATOR_REGISTRATION_DOMAIN,
    OperatorRegistrationContext,
    create_operator_registration,
    operator_possession_message,
    verify_operator_registration,
)

OPERATOR_KEY = "0x0000000000000000000000000000000000000000000000000000000000000002"
OTHER_OPERATOR_KEY = "0x0000000000000000000000000000000000000000000000000000000000000003"
CONTEXT = OperatorRegistrationContext(
    registrar="0x1111111111111111111111111111111111111111",
    owner="0x2222222222222222222222222222222222222222",
    chain_id=61999,
)


def test_matches_the_genlayer_js_vector():
    registration = create_operator_registration(OPERATOR_KEY, CONTEXT)

    assert (
        "0x" + OPERATOR_REGISTRATION_DOMAIN.hex()
        == "0x56a1f863be2956668ca2fd6b4010d6fde7a54f2b5a02d6c624a2bad7e5fd5ada"
    )
    assert registration.operator == "0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF"
    assert registration.operator_pub_key == (
        89565891926547004231252920425935692360644145829622209833684329913297188986597,
        12158399299693830322967808612713398636155367887041628176798871954788371653930,
    )
    assert (
        "0x" + operator_possession_message(registration.operator_pub_key, CONTEXT).hex()
        == "0x7823e1bdaf3a8cea679a7bafaf8ddc39c379ac690f35696328650c3a712f36e0"
    )
    assert (
        "0x" + registration.possession_proof.hex()
        == "0x30cedc70f8ab478fbc1a13a3f36e7f6a10eed631f59db4c451e38fe6d94dc640"
        "586d7a3202471043dbad68a3850655d39114aaca647df5734b171f8db7e88f161c"
    )
    assert verify_operator_registration(registration, CONTEXT)


def test_rejects_wrong_key_and_cross_domain_proofs():
    registration = create_operator_registration(OPERATOR_KEY, CONTEXT)
    wrong_key = create_operator_registration(OTHER_OPERATOR_KEY, CONTEXT)

    assert not verify_operator_registration(
        OperatorRegistrationProofLike(registration, wrong_key.possession_proof), CONTEXT
    )
    for field, value in (
        ("registrar", "0x3333333333333333333333333333333333333333"),
        ("owner", "0x4444444444444444444444444444444444444444"),
        ("chain_id", CONTEXT.chain_id + 1),
    ):
        mutated = OperatorRegistrationContext(
            registrar=value if field == "registrar" else CONTEXT.registrar,
            owner=value if field == "owner" else CONTEXT.owner,
            chain_id=value if field == "chain_id" else CONTEXT.chain_id,
        )
        assert not verify_operator_registration(registration, mutated)


def test_binds_rotation_proofs_to_the_wallet_not_the_factory():
    """Join proofs are verified by the factory, rotation proofs by the wallet.

    Reusing one for the other is the easy mistake, and it fails silently — the
    proof simply does not verify — so pin it.
    """
    factory = "0x1111111111111111111111111111111111111111"
    wallet = "0x5555555555555555555555555555555555555555"
    owner = "0x2222222222222222222222222222222222222222"

    join = create_operator_registration(
        OPERATOR_KEY,
        OperatorRegistrationContext(registrar=factory, owner=owner, chain_id=61999),
    )
    rotation_context = OperatorRegistrationContext(
        registrar=wallet, owner=owner, chain_id=61999
    )
    rotation = create_operator_registration(OPERATOR_KEY, rotation_context)

    assert verify_operator_registration(rotation, rotation_context)
    assert not verify_operator_registration(join, rotation_context)
    assert rotation.possession_proof != join.possession_proof
    assert rotation.operator == join.operator


class OperatorRegistrationProofLike:
    """Swaps in a foreign signature while keeping the advertised identity."""

    def __init__(self, registration, possession_proof):
        self.operator = registration.operator
        self.operator_pub_key = registration.operator_pub_key
        self.possession_proof = possession_proof
