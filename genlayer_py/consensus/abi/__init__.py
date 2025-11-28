import json
import importlib.resources

with (
    importlib.resources.as_file(
        importlib.resources.files("genlayer_py.consensus.abi").joinpath(
            "consensus_data_abi.json"
        )
    ) as path,
    open(path, "r", encoding="utf-8") as f,
):
    CONSENSUS_DATA_ABI = json.load(f)

with (
    importlib.resources.as_file(
        importlib.resources.files("genlayer_py.consensus.abi").joinpath(
            "consensus_main_abi.json"
        )
    ) as path,
    open(path, "r", encoding="utf-8") as f,
):
    CONSENSUS_MAIN_ABI = json.load(f)

__all__ = ["CONSENSUS_DATA_ABI", "CONSENSUS_MAIN_ABI"]
