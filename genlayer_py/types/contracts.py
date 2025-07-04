from typing import Dict, Any, TypedDict, List


class ContractMethodBase(TypedDict):
    params: List[Any]
    kwparams: Dict[str, Any]


class ContractMethod:
    ret: Any
    readonly: bool


class ContractSchema(TypedDict):
    ctor: ContractMethodBase
    methods: Dict[str, ContractMethod]


class SimConfig(TypedDict):
    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]
