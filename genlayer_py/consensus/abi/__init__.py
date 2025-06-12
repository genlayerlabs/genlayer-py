import json
import importlib.resources

consensus_data_abi_path = importlib.resources.files("genlayer_py").joinpath(
    "consensus/abi/consensus_data_abi.json"
)
consensus_main_abi_path = importlib.resources.files("genlayer_py").joinpath(
    "consensus/abi/consensus_main_abi.json"
)

with open(consensus_data_abi_path, "r") as f:
    CONSENSUS_DATA_ABI = json.load(f)

with open(consensus_main_abi_path, "r") as f:
    CONSENSUS_MAIN_ABI = json.load(f)
