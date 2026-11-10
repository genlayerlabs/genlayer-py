"""Private codec constants for the pre-fee ConsensusMain call shape.

The exported ConsensusMain ABI tracks the v0.6 train. These constants exist
only so the SDK can still decode or deliberately produce historical payloads
without letting an old selector leak back into the public contract surface.
"""

import eth_utils

LEGACY_ADD_TRANSACTION_ARGUMENT_TYPES = (
    "address",
    "address",
    "uint256",
    "uint256",
    "bytes",
    "uint256",
)
LEGACY_ADD_TRANSACTION_SIGNATURE = (
    "addTransaction(address,address,uint256,uint256,bytes,uint256)"
)
LEGACY_ADD_TRANSACTION_SELECTOR = eth_utils.keccak(
    text=LEGACY_ADD_TRANSACTION_SIGNATURE
)[:4].hex()
