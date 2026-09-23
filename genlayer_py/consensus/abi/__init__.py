import json
import importlib.resources


def _load_abi(name: str):
    with (
        importlib.resources.as_file(
            importlib.resources.files("genlayer_py.consensus.abi").joinpath(name)
        ) as path,
        open(path, "r", encoding="utf-8") as file,
    ):
        return json.load(file)


CONSENSUS_DATA_LIFECYCLE_ABI = _load_abi("consensus_data_lifecycle_abi.json")
CONSENSUS_DATA_TRAIN_READS_ABI = _load_abi("consensus_data_train_reads_abi.json")
CONSENSUS_DATA_TRAIN_ABI = CONSENSUS_DATA_LIFECYCLE_ABI + CONSENSUS_DATA_TRAIN_READS_ABI
CONSENSUS_DATA_ABI = _load_abi("consensus_data_abi.json")
CONSENSUS_MAIN_ABI = _load_abi("consensus_main_abi.json")
APPEALS_ABI = _load_abi("appeals_abi.json")

# Preserve the historical import names without preserving an old contract
# surface. This SDK release targets the train ABI only.
CONSENSUS_DATA_ABI_V06 = CONSENSUS_DATA_ABI
CONSENSUS_MAIN_ABI_V06 = CONSENSUS_MAIN_ABI

CONSENSUS_DATA_BIG_ROUNDS_ABI = _load_abi("consensus_data_big_rounds_abi.json")
ADDRESS_MANAGER_ABI = _load_abi("address_manager_abi.json")
TRANSACTION_MANAGER_READ_ABI = _load_abi("transaction_manager_read_abi.json")
ROUNDS_STORAGE_READ_ABI = _load_abi("rounds_storage_read_abi.json")

__all__ = [
    "CONSENSUS_DATA_ABI",
    "CONSENSUS_MAIN_ABI",
    "CONSENSUS_DATA_ABI_V06",
    "CONSENSUS_MAIN_ABI_V06",
    "APPEALS_ABI",
    "CONSENSUS_DATA_LIFECYCLE_ABI",
    "CONSENSUS_DATA_TRAIN_READS_ABI",
    "CONSENSUS_DATA_TRAIN_ABI",
    "CONSENSUS_DATA_BIG_ROUNDS_ABI",
    "ADDRESS_MANAGER_ABI",
    "TRANSACTION_MANAGER_READ_ABI",
    "ROUNDS_STORAGE_READ_ABI",
]
