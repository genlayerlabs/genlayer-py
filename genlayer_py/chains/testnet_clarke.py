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
from .testnet_bradbury import testnet_bradbury

# Clarke is a separate deployment on the Bradbury chain, so the chain RPC and
# explorer are shared
TESTNET_JSON_RPC_URL = "https://rpc.testnet-chain.genlayer.com"
EXPLORER_URL = "https://scan.testnet-chain.genlayer.com"

CONSENSUS_MAIN_CONTRACT: ContractInfo = {
    "address": "0xa44222E0beDaB12329557499ae6E555b1c9D02ee",
    "abi": CONSENSUS_MAIN_ABI,
    "bytecode": "",
}

CONSENSUS_DATA_CONTRACT: ContractInfo = {
    "address": "0x16Ef1E1EF400A7fE0e572445974b95DA17370de9",
    "abi": CONSENSUS_DATA_ABI,
    "bytecode": "",
}

# Clarke runs the Bradbury Phase 3 contracts, so the narrow ABIs are shared
FEE_MANAGER_CONTRACT: SimpleContractInfo = {
    "address": "0xd072dce2439d46C1F972810C6593D744c919b48a",
    "abi": testnet_bradbury.fee_manager_contract["abi"],
}

ROUNDS_STORAGE_CONTRACT: SimpleContractInfo = {
    "address": "0xefD3b249591a0fBe1cdf6d3b4e36e7D8Dee7d4C4",
    "abi": testnet_bradbury.rounds_storage_contract["abi"],
}

APPEALS_CONTRACT: SimpleContractInfo = {
    "address": "0xd6a836eb592Dd0b216f65bDc954Ca5bCff5DDaa2",
    "abi": APPEALS_ABI,
}

STAKING_CONTRACT: SimpleContractInfo = {
    "address": "0x711d111510Af2Bb35c3929b709677a1E9f8ffce2",
    "abi": STAKING_ABI,
}


testnet_clarke: GenLayerChain = GenLayerChain(
    id=4221,
    name="Genlayer Clarke Testnet",
    rpc_urls={
        "default": {"http": [TESTNET_JSON_RPC_URL]},
    },
    native_currency=NativeCurrency(name="GEN Token", symbol="GEN", decimals=18),
    block_explorers={
        "default": {
            "name": "GenLayer Chain Explorer",
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
