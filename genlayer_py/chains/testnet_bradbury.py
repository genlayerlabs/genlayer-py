from genlayer_py.types import GenLayerChain, NativeCurrency, ContractInfo
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI_V06, CONSENSUS_DATA_ABI_V06


TESTNET_JSON_RPC_URL = "https://zksync-os-testnet-genlayer.zksync.dev"
TESTNET_WS_URL = "wss://zksync-os-testnet-genlayer.zksync.dev/ws"
EXPLORER_URL = "https://explorer-bradbury.genlayer.com/"

CONSENSUS_MAIN_CONTRACT: ContractInfo = {
    "address": "0x0112Bf6e83497965A5fdD6Dad1E447a6E004271D",
    "abi": CONSENSUS_MAIN_ABI_V06,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT: ContractInfo = {
    "address": "0x85D7bf947A512Fc640C75327A780c90847267697",
    "abi": CONSENSUS_DATA_ABI_V06,
    "bytecode": "",
}


testnet_bradbury: GenLayerChain = GenLayerChain(
    id=4221,
    name="Genlayer Bradbury Testnet",
    rpc_urls={
        "default": {"http": [TESTNET_JSON_RPC_URL]},
    },
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Bradbury Explorer",
            "url": EXPLORER_URL,
        }
    },
    testnet=True,
    consensus_main_contract=CONSENSUS_MAIN_CONTRACT,
    consensus_data_contract=CONSENSUS_DATA_CONTRACT,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
