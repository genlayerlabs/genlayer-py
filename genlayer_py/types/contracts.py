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


class SimValidatorConfig(TypedDict):
    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]


class SimConfig(TypedDict):
    validators: List[SimValidatorConfig]
    genvm_datetime: str  # ISO format datetime string

    # Deprecated values - don't use these, we'll remove them in a future version
    provider: str
    model: str
    config: Dict[str, Any]
    plugin: str
    plugin_config: Dict[str, Any]
