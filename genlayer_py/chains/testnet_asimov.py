from genlayer_py.types import GenLayerChain, NativeCurrency
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI, CONSENSUS_DATA_ABI


TESTNET_JSON_RPC_URL = "https://zksync-os-testnet-genlayer.zksync.dev"
TESTNET_WS_URL = "wss://zksync-os-testnet-genlayer.zksync.dev/ws"
EXPLORER_URL = "https://explorer-asimov.genlayer.com/"

CONSENSUS_MAIN_CONTRACT = {
    "address": "0x6CAFF6769d70824745AD895663409DC70aB5B28E",
    "abi": CONSENSUS_MAIN_ABI,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT = {
    "address": "0x0D9d1d74d72Fa5eB94bcf746C8FCcb312a722c9B",
    "abi": CONSENSUS_DATA_ABI,
    "bytecode": "",
}


testnet_asimov: GenLayerChain = GenLayerChain(
    id=4221,
    name="Genlayer Asimov Testnet",
    rpc_urls={
        "default": {"http": [TESTNET_JSON_RPC_URL]},
    },
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Asimov Explorer",
            "url": EXPLORER_URL,
        }
    },
    testnet=True,
    consensus_main_contract=CONSENSUS_MAIN_CONTRACT,
    consensus_data_contract=CONSENSUS_DATA_CONTRACT,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
