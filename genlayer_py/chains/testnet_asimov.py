from genlayer_py.types import GenLayerChain, NativeCurrency, SimpleContractInfo
from genlayer_py.consensus.abi import (
    APPEALS_ABI,
    CONSENSUS_MAIN_ABI,
    CONSENSUS_DATA_ABI,
)

TESTNET_JSON_RPC_URL = "https://rpc-asimov.genlayer.com"
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

FEE_MANAGER_CONTRACT: SimpleContractInfo = {
    "address": "0x21737AA4bea8FF12E202BF1BAB23751A95617533",
    "abi": [
        {
            "type": "function",
            "name": "calculateMinAppealBond",
            "stateMutability": "view",
            "inputs": [
                {"name": "_txId", "type": "bytes32"},
                {"name": "_round", "type": "uint256"},
                {"name": "_status", "type": "uint8"},
            ],
            "outputs": [{"name": "totalFeesToPay", "type": "uint256"}],
        },
    ],
}

ROUNDS_STORAGE_CONTRACT: SimpleContractInfo = {
    "address": "0x1F595c0D549DE0812F127508ea1039636CFA62Cc",
    "abi": [
        {
            "type": "function",
            "name": "getRoundNumber",
            "stateMutability": "view",
            "inputs": [{"name": "txId", "type": "bytes32"}],
            "outputs": [{"name": "", "type": "uint256"}],
        },
        {
            "type": "function",
            "name": "getRoundData",
            "stateMutability": "view",
            "inputs": [
                {"name": "txId", "type": "bytes32"},
                {"name": "round", "type": "uint256"},
            ],
            "outputs": [
                {
                    "name": "",
                    "type": "tuple",
                    "components": [
                        {"name": "round", "type": "uint256"},
                        {"name": "leaderIndex", "type": "uint256"},
                        {"name": "votesCommitted", "type": "uint256"},
                        {"name": "votesRevealed", "type": "uint256"},
                        {"name": "appealBond", "type": "uint256"},
                        {"name": "rotationsLeft", "type": "uint256"},
                        {"name": "result", "type": "uint8"},
                        {"name": "roundValidators", "type": "address[]"},
                        {"name": "validatorVotes", "type": "uint8[]"},
                        {"name": "validatorVotesHash", "type": "bytes32[]"},
                        {"name": "validatorResultHash", "type": "bytes32[]"},
                    ],
                }
            ],
        },
        {
            "type": "function",
            "name": "getLastRoundData",
            "stateMutability": "view",
            "inputs": [{"name": "txId", "type": "bytes32"}],
            "outputs": [
                {"name": "round", "type": "uint256"},
                {
                    "name": "roundData",
                    "type": "tuple",
                    "components": [
                        {"name": "round", "type": "uint256"},
                        {"name": "leaderIndex", "type": "uint256"},
                        {"name": "votesCommitted", "type": "uint256"},
                        {"name": "votesRevealed", "type": "uint256"},
                        {"name": "appealBond", "type": "uint256"},
                        {"name": "rotationsLeft", "type": "uint256"},
                        {"name": "result", "type": "uint8"},
                        {"name": "roundValidators", "type": "address[]"},
                        {"name": "validatorVotes", "type": "uint8[]"},
                        {"name": "validatorVotesHash", "type": "bytes32[]"},
                        {"name": "validatorResultHash", "type": "bytes32[]"},
                    ],
                },
            ],
        },
    ],
}

APPEALS_CONTRACT: SimpleContractInfo = {
    "address": "0x0F739Dd8f5322b9547c7d19a9621BC2ac8DF4089",
    "abi": APPEALS_ABI,
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
    fee_manager_contract=FEE_MANAGER_CONTRACT,
    rounds_storage_contract=ROUNDS_STORAGE_CONTRACT,
    appeals_contract=APPEALS_CONTRACT,
    staking_contract=None,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
