from genlayer_py.types import GenLayerTransaction


def tx_execution_succeeded(result: GenLayerTransaction) -> bool:
    if "consensus_data" not in result:
        return False
    if "leader_receipt" not in result["consensus_data"]:
        return False
    leader_receipt = result["consensus_data"]["leader_receipt"]
    if isinstance(leader_receipt, dict):
        leader_receipt = [leader_receipt]
    if not isinstance(leader_receipt, list) or len(leader_receipt) == 0:
        return False
    if "execution_result" not in leader_receipt[0]:
        return False
    execution_result = leader_receipt[0]["execution_result"]
    return execution_result == "SUCCESS"


def tx_execution_failed(result: GenLayerTransaction) -> bool:
    return not tx_execution_succeeded(result)
