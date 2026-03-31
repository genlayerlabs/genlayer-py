from genlayer_py.types import GenLayerChain, NativeCurrency, ContractInfo, SimpleContractInfo
from genlayer_py.consensus.abi import CONSENSUS_MAIN_ABI_V06, CONSENSUS_DATA_ABI_V06


TESTNET_JSON_RPC_URL = "https://rpc-bradbury.genlayer.com"
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

FEE_MANAGER_CONTRACT: SimpleContractInfo = {
    "address": "0xF205868bf5db79d2162843742D18D0900A9E462a",
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
    "address": "0x7134D05af13A14c0b66Fe129fb930b1d0C420e33",
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
    "address": "0xbb8C35AA878D09b9830aFF9e5aAC6492BFbd5471",
    "abi": [
        {
            "type": "function",
            "name": "canAppeal",
            "stateMutability": "view",
            "inputs": [{"name": "_txId", "type": "bytes32"}],
            "outputs": [{"name": "", "type": "bool"}],
        },
    ],
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
    default_number_of_initial_validators=5,
    default_consensus_max_rotations=3,
)
