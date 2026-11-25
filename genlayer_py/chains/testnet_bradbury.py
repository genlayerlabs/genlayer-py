from genlayer_py.types import (
    GenLayerChain,
    NativeCurrency,
    ContractInfo,
    SimpleContractInfo,
)
from genlayer_py.consensus.abi import (
    APPEALS_ABI,
    CONSENSUS_MAIN_ABI,
    CONSENSUS_DATA_ABI,
)
from genlayer_py.staking.abi import STAKING_ABI

TESTNET_JSON_RPC_URL = "https://rpc.testnet-chain.genlayer.com"
EXPLORER_URL = "https://scan.testnet-chain.genlayer.com"

CONSENSUS_MAIN_CONTRACT: ContractInfo = {
    "address": "0x0f4F0e05475723790E4a2ed0598370783C300926",
    "abi": CONSENSUS_MAIN_ABI,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT: ContractInfo = {
    "address": "0x2247b85b7ca7fb1Fea990b4aFAB4328D9c597f28",
    "abi": CONSENSUS_DATA_ABI,
    "bytecode": "",
}

FEE_MANAGER_CONTRACT: SimpleContractInfo = {
    "address": "0x8E8B6194020dB1CbEf9C6c9dcFeE8FfF1e5E33c3",
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
    "address": "0xa6bdB728B82c23786D6e3CAfc0B97235490A64Fb",
    "abi": [
        {
            "type": "function",
            "name": "getRoundNumber",
            "stateMutability": "view",
            "inputs": [{"name": "_txId", "type": "bytes32"}],
            "outputs": [{"name": "", "type": "uint256"}],
        },
        {
            "type": "function",
            "name": "getRoundData",
            "stateMutability": "view",
            "inputs": [
                {"name": "_txId", "type": "bytes32"},
                {"name": "_round", "type": "uint256"},
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
            "inputs": [{"name": "_txId", "type": "bytes32"}],
            "outputs": [
                {"name": "", "type": "uint256"},
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
                },
            ],
        },
    ],
}

APPEALS_CONTRACT: SimpleContractInfo = {
    "address": "0x10F2d70ABB8F588f96bEB1a02c99163EB75A2CF1",
    "abi": APPEALS_ABI,
}

STAKING_CONTRACT: SimpleContractInfo = {
    "address": "0xcE16862EAf10B97A0619BeBb662991fb4a52e346",
    "abi": STAKING_ABI,
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
    fee_manager_contract=FEE_MANAGER_CONTRACT,
    rounds_storage_contract=ROUNDS_STORAGE_CONTRACT,
    appeals_contract=APPEALS_CONTRACT,
    staking_contract=STAKING_CONTRACT,
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
