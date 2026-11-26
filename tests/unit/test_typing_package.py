from importlib.resources import files
from typing import is_typeddict

from genlayer_py.types.contracts import ContractMethod


def test_typing_marker_present():
    assert files("genlayer_py").joinpath("py.typed").is_file()


def test_contract_method_describes_schema_dictionary():
    assert is_typeddict(ContractMethod)
    assert ContractMethod.__required_keys__ == {"params", "kwparams", "ret", "readonly"}
