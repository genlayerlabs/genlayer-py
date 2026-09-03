from __future__ import annotations

from genlayer_py.types import GenLayerChain


STUDIO_CHAIN_IDS = frozenset({61997, 61999})


def is_studio_chain(chain: GenLayerChain) -> bool:
    """Return whether *chain* uses the Studio simulator RPC surface."""

    return chain.id in STUDIO_CHAIN_IDS
