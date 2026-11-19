import rlp

import genlayer_py
from genlayer_py import CalldataAddress, abi


ADDRESS = "0x" + "11" * 20


def test_abi_is_exported_from_package_root():
    assert genlayer_py.abi is abi
    assert callable(abi.calldata.encode)
    assert callable(abi.calldata.decode)
    assert callable(abi.calldata.to_str)
    assert callable(abi.calldata.make_calldata_object)
    assert callable(abi.transactions.serialize)


def test_calldata_round_trip():
    value = {
        "int": -42,
        "big": 2**200,
        "str": "hello",
        "bytes": b"\x00\x01",
        "list": [1, None, True, False],
        "address": CalldataAddress(ADDRESS),
    }
    decoded = abi.calldata.decode(abi.calldata.encode(value))
    assert decoded == value


def test_make_calldata_object_matches_contract_call_shape():
    obj = abi.calldata.make_calldata_object(
        method="transfer", args=[CalldataAddress(ADDRESS), 10], kwargs={"memo": "x"}
    )
    assert obj == {
        "": "transfer",
        "args": [CalldataAddress(ADDRESS), 10],
        "kwargs": {"memo": "x"},
    }
    assert abi.calldata.make_calldata_object() == {}
    assert abi.calldata.decode(abi.calldata.encode(obj)) == obj


def test_to_str_is_human_readable():
    assert abi.calldata.to_str([1, "a", None]) == '[1,"a",null]'


def test_transactions_serialize_is_rlp_hex():
    assert (
        abi.transactions.serialize([b"a", b"bc"])
        == "0x" + rlp.encode([b"a", b"bc"]).hex()
    )


def test_make_calldata_object_legacy_path_is_same_function():
    from genlayer_py.contracts.utils import make_calldata_object

    assert make_calldata_object is abi.calldata.make_calldata_object


def test_abi_package_does_not_import_contracts_package():
    # Keep the dependency one-way: contracts -> abi, never abi -> contracts.
    from pathlib import Path

    abi_dir = Path(abi.__file__).parent
    offenders = [
        str(path.relative_to(abi_dir))
        for path in abi_dir.rglob("*.py")
        if "genlayer_py.contracts" in path.read_text()
    ]
    assert offenders == []
