from dataclasses import dataclass
from typing import List, Any, Optional, Dict, TypedDict


@dataclass
class NativeCurrency:
    name: str
    symbol: str
    decimals: int


@dataclass
class Chain:
    id: int
    name: str
    rpc_urls: Dict
    native_currency: NativeCurrency
    block_explorers: Dict
    testnet: bool


class ContractInfo(TypedDict):
    address: str
    abi: List[Any]
    bytecode: str


class SimpleContractInfo(TypedDict):
    address: str
    abi: List[Any]


@dataclass
class GenLayerChain(Chain):
    consensus_main_contract: Optional[ContractInfo]
    consensus_data_contract: Optional[ContractInfo]
    fee_manager_contract: Optional[SimpleContractInfo]
    rounds_storage_contract: Optional[SimpleContractInfo]
    appeals_contract: Optional[SimpleContractInfo]
    staking_contract: Optional[SimpleContractInfo]
    default_number_of_initial_validators: int
    default_consensus_max_rotations: int
