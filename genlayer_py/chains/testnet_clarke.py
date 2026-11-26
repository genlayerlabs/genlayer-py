from genlayer_py.types import GenLayerChain, NativeCurrency

# TODO(clarke): placeholders until the Clarke deployment publishes its
# coordinates; Clarke runs the Bradbury Phase 3 contracts, so its ABIs will be
# the ones testnet_bradbury uses. Contracts stay unset so that nothing can be
# sent before then.
TESTNET_JSON_RPC_URL = "https://rpc-clarke.genlayer.com"
EXPLORER_URL = "https://explorer-clarke.genlayer.com"


testnet_clarke: GenLayerChain = GenLayerChain(
    id=4221,
    name="Genlayer Clarke Testnet",
    rpc_urls={
        "default": {"http": [TESTNET_JSON_RPC_URL]},
    },
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Clarke Explorer",
            "url": EXPLORER_URL,
        }
    },
    testnet=True,
    consensus_main_contract=None,
    consensus_data_contract=None,
    fee_manager_contract=None,
    rounds_storage_contract=None,
    appeals_contract=None,
    staking_contract=None,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
