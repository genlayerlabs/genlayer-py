import json
import importlib.resources

with importlib.resources.as_file(
    importlib.resources.files("genlayer_py.staking.abi").joinpath("staking_abi.json")
) as path, open(path, "r", encoding="utf-8") as f:
    STAKING_ABI = json.load(f)

with importlib.resources.as_file(
    importlib.resources.files("genlayer_py.staking.abi").joinpath(
        "validator_wallet_abi.json"
    )
) as path, open(path, "r", encoding="utf-8") as f:
    VALIDATOR_WALLET_ABI = json.load(f)

__all__ = ["STAKING_ABI", "VALIDATOR_WALLET_ABI"]
