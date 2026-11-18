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
    "address": "0x2E2766cbc3E5e61Ce93bBcdCBb3eAcB82082A019",
    "abi": CONSENSUS_MAIN_ABI,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT: ContractInfo = {
    "address": "0xc5FA6f82BEe53598825d6edf7E3e24613082c75B",
    "abi": CONSENSUS_DATA_ABI,
    "bytecode": "",
}

FEE_MANAGER_CONTRACT: SimpleContractInfo = {
    "address": "0x7678587A847712f2A96082AC07883A88D0fc7245",
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
    "address": "0x4038d4F72C7aAbA5a442cC0dA946012B9E3f4B8a",
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
    "address": "0xdc953c3bCf8837987853ca05a78D52fFC3E18651",
    "abi": APPEALS_ABI,
}

STAKING_CONTRACT: SimpleContractInfo = {
    "address": "0xD8fBa96C0dBB0257028dBc0107060b958e5c7113",
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
