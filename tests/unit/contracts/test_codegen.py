import importlib.util
from typing import get_type_hints
from unittest.mock import Mock

import pytest

from genlayer_py import generate_contract_types, create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.chains import localnet
from genlayer_py.types import CalldataAddress


def schema(ret, params=None, kwparams=None):
    return {
        "ctor": {"params": [], "kwparams": {}},
        "methods": {
            "read": {
                "params": params or [],
                "kwparams": kwparams or {},
                "ret": ret,
                "readonly": True,
            }
        },
    }


def load_binding(tmp_path, source):
    path = tmp_path / "binding.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location("binding", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "value, expected",
    [
        ("any", "_typing.Any"),
        ("null", "None"),
        ("bool", "_builtins.bool"),
        ("int", "_builtins.int"),
        ("string", "_builtins.str"),
        ("bytes", "_builtins.bytes"),
        ("address", "_CalldataAddress"),
        ("array", "_builtins.list[_typing.Any]"),
        ("dict", "_builtins.dict[_builtins.str, _typing.Any]"),
        ({"$dict": "int"}, "_builtins.dict[_builtins.str, _builtins.int]"),
        ([{"$rep": "int"}], "_builtins.list[_builtins.int]"),
        (
            ["int", "string"],
            "_builtins.list[_typing.Union[_builtins.int, _builtins.str]]",
        ),
        ([], "_builtins.list[_typing.Never]"),
        ({"$or": ["int", "null"]}, "_typing.Union[_builtins.int, None]"),
    ],
)
def test_types(tmp_path, value, expected):
    source = generate_contract_types(schema(value))
    assert f"_Contract_read_Result: _typing.TypeAlias = {expected}" in source
    module = load_binding(tmp_path, source)
    assert get_type_hints(module.Contract.read)["return"] == (
        type(None) if value == "null" else module.Contract_read_Result
    )


def test_nested_records_and_escaped_fields(tmp_path):
    module = load_binding(
        tmp_path,
        generate_contract_types(schema({"user": {"name": "string"}, "$$value": "int"})),
    )
    fields = get_type_hints(module.Contract_read_Result)
    assert fields["$value"] is int
    assert get_type_hints(fields["user"]) == {"name": str}


def test_call_arguments_and_write_exclusion(tmp_path):
    contract_schema = schema("string", [["id", "int"]], {"label": "string"})
    contract_schema["methods"]["write"] = {"readonly": False}
    source = generate_contract_types(contract_schema, "Storage")
    module = load_binding(tmp_path, source)
    client = Mock()
    client.read_contract.return_value = "result"
    binding = module.Storage(client, "0x123")
    assert binding.read(1, label="a") == "result"
    client.read_contract.assert_called_once_with(
        address="0x123", function_name="read", args=[1], kwargs={"label": "a"}
    )
    assert not hasattr(binding, "write")
    assert generate_contract_types(contract_schema, "Storage") == source


@pytest.mark.parametrize("value", ["float", {"$unknown": "int"}, {"$or": []}, 1])
def test_unsupported_types(value):
    with pytest.raises(ValueError):
        generate_contract_types(schema(value))


@pytest.mark.parametrize("name", ["class", "_client", "x;print('oops')", "__init__"])
def test_unsafe_names(name):
    with pytest.raises(ValueError):
        generate_contract_types(schema("int"), name)
    with pytest.raises(ValueError):
        generate_contract_types(schema("int", [[name, "int"]]))
    data = schema("int")
    data["methods"][name] = data["methods"].pop("read")
    with pytest.raises(ValueError):
        generate_contract_types(data)


def test_duplicate_parameters():
    with pytest.raises(ValueError, match="Duplicate"):
        generate_contract_types(schema("int", [["x", "int"]], {"x": "int"}))


def test_empty_contract(tmp_path):
    module = load_binding(tmp_path, generate_contract_types({"methods": {}}))
    assert module.Contract(Mock(), "0x123")


def test_sdk_schema_to_decoded_read_integration(tmp_path):
    """Exercise the real SDK schema/read actions and calldata codec offline."""
    client = create_client(chain=localnet, account=create_account())
    contract_schema = schema(
        {"owner": "address", "values": [{"$rep": "int"}]},
        [["key", "string"]],
    )
    expected = {"owner": CalldataAddress(bytes(20)), "values": [1, 2]}
    client.provider.make_request = Mock(
        side_effect=[
            {"result": contract_schema},
            {"result": calldata.encode(expected).hex()},
        ]
    )
    address = "0x" + "01" * 20
    module = load_binding(
        tmp_path, generate_contract_types(client.get_contract_schema(address))
    )
    assert module.Contract(client, address).read("key") == expected
    assert client.provider.make_request.call_args.kwargs["method"] == "gen_call"


def test_parameter_does_not_shadow_result_alias(tmp_path):
    module = load_binding(
        tmp_path,
        generate_contract_types(schema("int", [["Contract_read_Result", "int"]])),
    )
    client = Mock()
    client.read_contract.return_value = 42
    assert module.Contract(client, "0x123").read(1) == 42
