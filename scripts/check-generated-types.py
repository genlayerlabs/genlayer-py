"""Check generated bindings against the installed wheel, outside the source tree.

Run with an isolated environment containing the built wheel and mypy.
The unit suite invokes this through test_codegen_wheel.py.
"""

from pathlib import Path
import subprocess
import sys
import tempfile

import genlayer_py
from genlayer_py.contracts.codegen import generate_contract_types

package = Path(genlayer_py.__file__).parent.resolve()
repository = Path(__file__).resolve().parents[1]
assert not package.is_relative_to(repository), "Install the wheel, not the source tree"
assert (package / "py.typed").is_file(), "Wheel is missing the PEP 561 marker"

schema = {
    "ctor": {"params": [], "kwparams": {}},
    "methods": {
        "get_user": {
            "readonly": True,
            "params": [["owner", "address"]],
            "kwparams": {"label": "string"},
            "ret": {
                "owner": "address",
                "profile": {"name": "string"},
                "scores": {"$dict": {"$or": ["int", "null"]}},
                "pair": ["int", "string"],
            },
        },
        "nothing": {"readonly": True, "params": [], "kwparams": {}, "ret": "null"},
    },
}

with tempfile.TemporaryDirectory(prefix="genlayer-wheel-typing-") as directory:
    root = Path(directory)
    (root / "storage_types.py").write_text(generate_contract_types(schema, "Storage"))
    valid = """from storage_types import Storage
from genlayer_py.types.calldata import CalldataAddress

def read(storage: Storage, owner: CalldataAddress) -> str:
    result = storage.get_user(owner, label="primary")
    address: CalldataAddress = result["owner"]
    storage.nothing()
    return result["profile"]["name"]
"""
    (root / "valid.py").write_text(valid)
    command = [sys.executable, "-m", "mypy", "--strict", "--no-incremental"]
    subprocess.run(command + ["storage_types.py", "valid.py"], cwd=root, check=True)
    invalid = """from storage_types import Storage
from genlayer_py.types.calldata import CalldataAddress

def read(storage: Storage, owner: CalldataAddress) -> None:
    storage.get_user("0x00", label="primary")
    storage.get_user(owner)
    result = storage.get_user(owner, label="primary")
    result["missing"]
"""
    (root / "invalid.py").write_text(invalid)
    result = subprocess.run(
        command + ["invalid.py"], cwd=root, text=True, capture_output=True
    )
    print(result.stdout, end="")
    assert result.returncode == 1, result.stderr
    for diagnostic in ("[arg-type]", "[call-arg]", "[typeddict-item]"):
        assert diagnostic in result.stdout, result.stdout
    assert "Found 3 errors in 1 file" in result.stdout, result.stdout
print("Installed wheel: strict typing passes and invalid usage is rejected")
