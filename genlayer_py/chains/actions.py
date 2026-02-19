from __future__ import annotations

from genlayer_py.exceptions import GenLayerError
from .localnet import localnet
from .studionet import studionet
from .testnet_asimov import testnet_asimov

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


def initialize_consensus_smart_contract(
    self: GenLayerClient,
    force_reset: bool = False,
) -> None:
    if self.chain.id == testnet_asimov.id:
        return

    has_static_consensus_contract = (
        self.chain.consensus_main_contract is not None
        and bool(self.chain.consensus_main_contract.get("address"))
        and bool(self.chain.consensus_main_contract.get("abi"))
    )
    is_local_or_studio_chain = self.chain.id in (localnet.id, studionet.id)

    if (
        not force_reset
        and has_static_consensus_contract
        and not is_local_or_studio_chain
    ):
        return

    try:
        response = self.provider.make_request(
            method="sim_getConsensusContract", params=["ConsensusMain"]
        )
        result = response.get("result")
        if (
            not isinstance(result, dict)
            or not result.get("address")
            or not result.get("abi")
        ):
            raise GenLayerError(
                "ConsensusMain response did not include a valid contract"
            )

        self.chain.consensus_main_contract = result
        setattr(self.chain, "__consensus_abi_fetched_from_rpc", True)
    except Exception:
        # Some local simulators do not expose sim_getConsensusContract.
        # If we already have a chain-baked ABI, continue using it.
        if has_static_consensus_contract:
            setattr(self.chain, "__consensus_abi_fetched_from_rpc", False)
            return
        raise
