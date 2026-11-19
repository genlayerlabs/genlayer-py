"""Generate statically typed read bindings from a GenVM contract schema."""

import keyword
from typing import Any

from genlayer_py.types import ContractSchema


def _identifier(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isidentifier()
        or keyword.iskeyword(value)
        or value.startswith("_")
    ):
        raise ValueError(f"Unsupported Python identifier: {value!r}")
    return value


class _Types:
    def __init__(self):
        self.records: list[str] = []

    def render(self, schema: Any) -> str:
        primitives = {
            "any": "_typing.Any",
            "null": "None",
            "bool": "_builtins.bool",
            "int": "_builtins.int",
            "string": "_builtins.str",
            "bytes": "_builtins.bytes",
            "address": "_CalldataAddress",
            "array": "_builtins.list[_typing.Any]",
            "dict": "_builtins.dict[_builtins.str, _typing.Any]",
        }
        if isinstance(schema, str) and schema in primitives:
            return primitives[schema]
        if isinstance(schema, list):
            # Calldata decodes both fixed and repeated arrays to Python lists.
            members = []
            for item in schema:
                if isinstance(item, dict) and set(item) == {"$rep"}:
                    item = item["$rep"]
                members.append(self.render(item))
            return (
                f"_builtins.list[{self.union(members) if members else '_typing.Never'}]"
            )
        if isinstance(schema, dict):
            if set(schema) == {"$or"}:
                variants = schema["$or"]
                if not isinstance(variants, list) or not variants:
                    raise ValueError("$or must contain a nonempty list")
                return self.union([self.render(item) for item in variants])
            if set(schema) == {"$dict"}:
                return f"_builtins.dict[_builtins.str, {self.render(schema['$dict'])}]"
            fields = []
            for key, value in sorted(schema.items()):
                if not isinstance(key, str) or (
                    key.startswith("$") and not key.startswith("$$")
                ):
                    raise ValueError(f"Unsupported schema field: {key!r}")
                key = key[1:] if key.startswith("$$") else key
                fields.append(f"{key!r}: {self.render(value)}")
            name = f"_Record{len(self.records) + 1}"
            self.records.append(
                f"{name} = _typing.TypedDict({name!r}, {{{', '.join(fields)}}})"
            )
            return name
        raise ValueError(f"Unsupported schema type: {schema!r}")

    @staticmethod
    def union(members: list[str]) -> str:
        members = list(dict.fromkeys(members))
        return (
            members[0] if len(members) == 1 else f"_typing.Union[{', '.join(members)}]"
        )


def generate_contract_types(
    schema: ContractSchema, class_name: str = "Contract"
) -> str:
    """Return Python source for a typed read-only contract binding.

    Write the result to a ``.py`` module and import its generated class. Bind it
    to a client and contract address, then call view methods directly. Return
    values retain the SDK's decoded representation; no runtime validation or
    conversion is performed. Unsupported types or unsafe identifiers raise
    ``ValueError``. Write methods and deployment remain on the existing client.
    """
    _identifier(class_name)
    types = _Types()
    methods = []
    aliases = []
    for name, method in sorted(schema["methods"].items()):
        if not method["readonly"]:
            continue
        _identifier(name)
        params = method["params"]
        kwparams = method["kwparams"]
        names = [_identifier(param[0]) for param in params]
        kwnames = [_identifier(key) for key in sorted(kwparams)]
        if len(set(names + kwnames)) != len(names + kwnames):
            raise ValueError(f"Duplicate parameters in {name!r}")
        signature = ["_binding"]
        signature.extend(f"{key}: {types.render(value)}" for key, value in params)
        signature.append("/")
        if kwnames:
            signature.append("*")
            signature.extend(f"{key}: {types.render(kwparams[key])}" for key in kwnames)
        result = f"{class_name}_{name}_Result"
        aliases.append(f"_{result}: _typing.TypeAlias = {types.render(method['ret'])}")
        aliases.append(f"{result}: _typing.TypeAlias = _{result}")
        result = "_" + result
        kwargs = ", ".join(f"{key!r}: {key}" for key in kwnames)
        methods.append(
            f"    def {name}({', '.join(signature)}) -> {result}:\n"
            f"        return _typing.cast({result!r}, _binding._client.read_contract(\n"
            f"            address=_binding._address, function_name={name!r},\n"
            f"            args=_typing.cast('_builtins.list[_CalldataEncodable]', [{', '.join(names)}]),\n"
            f"            kwargs=_typing.cast('_builtins.dict[_builtins.str, _CalldataEncodable]', {{{kwargs}}}),\n"
            f"        ))\n"
        )
    return "\n".join(
        [
            "# Generated by genlayer_py.generate_contract_types. Do not edit.",
            "from __future__ import annotations",
            "import builtins as _builtins",
            "import typing as _typing",
            "from genlayer_py.client.genlayer_client import GenLayerClient as _GenLayerClient",
            "from genlayer_py.types.calldata import CalldataAddress as _CalldataAddress, CalldataEncodable as _CalldataEncodable",
            "from eth_typing import Address as _Address, ChecksumAddress as _ChecksumAddress",
            "",
            *types.records,
            *aliases,
            "",
            f"class {class_name}:",
            "    def __init__(self, client: _GenLayerClient, address: _Address | _ChecksumAddress) -> None:",
            "        self._client = client",
            "        self._address = address",
            "",
            *methods,
        ]
    )
