from __future__ import annotations

from typing import TYPE_CHECKING
from genlayer_py.chains import localnet
from hexbytes import HexBytes
from web3.types import Nonce, BlockIdentifier, ENS
from genlayer_py.exceptions import GenLayerError
from eth_typing import (
    Address,
    ChecksumAddress,
)
from typing import Optional, Union

if TYPE_CHECKING:
    from genlayer_py.client import GenLayerClient


def fund_account(
    self: GenLayerClient, address: Union[Address, ChecksumAddress, ENS], amount: int
) -> HexBytes:
    if self.chain.id != localnet.id:
        raise GenLayerError("Client is not connected to the localhost")
    try:
        response = self.provider.make_request(
            method="sim_fundAccount",
            params=[address, amount],
        )
        return HexBytes(response["result"])
    except Exception as e:
        raise GenLayerError(str(e))


def get_current_nonce(
    self: GenLayerClient,
    address: Optional[Union[Address, ChecksumAddress, ENS]] = None,
    block_identifier: Optional[BlockIdentifier] = None,
) -> Nonce:
    if address is None and self.account is None:
        raise GenLayerError("No address provided and no account is connected")
    address_to_use = address or self.account.address
    # Include locally pending transactions by default so consecutive
    # submissions do not reuse the same nonce before the first is mined.
    resolved_block_identifier = (
        "pending" if block_identifier is None else block_identifier
    )
    return self.get_transaction_count(address_to_use, resolved_block_identifier)
