import json
import importlib.resources

with importlib.resources.as_file(
    importlib.resources.files("genlayer_py.vesting.abi").joinpath("vesting_abi.json")
) as path, open(path, "r", encoding="utf-8") as f:
    VESTING_ABI = json.load(f)

__all__ = ["VESTING_ABI"]
