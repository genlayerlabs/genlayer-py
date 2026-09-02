from genlayer_py.types import GenLayerChain, NativeCurrency

from .studionet import (
    CONSENSUS_DATA_CONTRACT,
    CONSENSUS_MAIN_CONTRACT,
)


STUDIO_DEVNET_JSON_RPC_URL = "https://studio-dev.genlayer.com/api"
STUDIO_DEVNET_EXPLORER_URL = "https://explorer-studio-dev.genlayer.com"

studio_devnet: GenLayerChain = GenLayerChain(
    id=61997,
    name="GenLayer Studio Devnet",
    rpc_urls={"default": {"http": [STUDIO_DEVNET_JSON_RPC_URL]}},
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Explorer",
            "url": STUDIO_DEVNET_EXPLORER_URL,
        }
    },
    testnet=True,
    consensus_main_contract=dict(CONSENSUS_MAIN_CONTRACT),
    consensus_data_contract=dict(CONSENSUS_DATA_CONTRACT),
    fee_manager_contract=None,
    rounds_storage_contract=None,
    appeals_contract=None,
    staking_contract=None,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
