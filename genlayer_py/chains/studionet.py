from genlayer_py.types import GenLayerChain, NativeCurrency
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI, CONSENSUS_DATA_ABI


SIMULATOR_JSON_RPC_URL = "https://studio.genlayer.com/api"
EXPLORER_URL = "https://genlayer-explorer.vercel.app"

CONSENSUS_MAIN_CONTRACT = {
    "address": "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",
    "abi": CONSENSUS_MAIN_ABI,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT = {
    "address": "0x88B0F18613Db92Bf970FfE264E02496e20a74D16",
    "abi": CONSENSUS_DATA_ABI,
    "bytecode": "",
}

studionet: GenLayerChain = GenLayerChain(
    id=61999,
    name="Genlayer Studio Network",
    rpc_urls={"default": {"http": [SIMULATOR_JSON_RPC_URL]}},
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Explorer",
            "url": EXPLORER_URL,
        }
    },
    testnet=True,
    consensus_main_contract=CONSENSUS_MAIN_CONTRACT,
    consensus_data_contract=CONSENSUS_DATA_CONTRACT,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
