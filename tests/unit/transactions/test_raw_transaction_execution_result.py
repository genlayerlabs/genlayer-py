"""
GenLayerRawTransaction.from_transaction_data() decodes the *light* getTransaction
ABI response, which structurally has no execution-result field on either the
Asimov (v04, 21-field) or Bradbury (v06, 23-field) shape. Only the heavier
getTransactionAllData response (from_all_transaction_data) actually carries one.

tx_execution_result must therefore come back as None (unknown) from the light
path, not 0 -- 0 is a real, meaningful value (ExecutionResult.NOT_VOTED) and
hardcoding it there silently claims a status the SDK never actually read.
"""

from genlayer_py.types.transactions import GenLayerRawTransaction, ExecutionResult

ZERO_HASH = b"\x00" * 32
ADDR_A = "0x" + "11" * 20
ADDR_B = "0x" + "22" * 20
ADDR_C = "0x" + "33" * 20
ADDR_D = "0x" + "44" * 20
EMPTY_LAST_ROUND = (0, 0, 0, 0, 0, 0, 0, [], [], [])
EMPTY_BLOCK_RANGE = (1, 2, 3)


def _v04_tuple():
    """21-field Asimov/pre-Bradbury raw getTransaction tuple."""
    return (
        1700000000,  # 0 current_timestamp
        ADDR_A,  # 1 sender
        ADDR_B,  # 2 recipient
        5,  # 3 num_of_initial_validators
        0,  # 4 tx_slot
        1700000000,  # 5 created_timestamp
        1700000001,  # 6 last_vote_timestamp
        ZERO_HASH,  # 7 random_seed
        1,  # 8 result
        b"\x01\x02",  # 9 tx_data
        b"\x00",  # 10 tx_receipt
        [],  # 11 messages
        0,  # 12 queue_type
        0,  # 13 queue_position
        ADDR_C,  # 14 activator
        ADDR_D,  # 15 last_leader
        1,  # 16 status
        ZERO_HASH,  # 17 tx_id
        EMPTY_BLOCK_RANGE,  # 18 read_state_block_range
        1,  # 19 num_of_rounds
        EMPTY_LAST_ROUND,  # 20 last_round
    )


def _v06_tuple():
    """23-field Bradbury raw getTransaction tuple."""
    return (
        1700000000,  # 0 current_timestamp
        ADDR_A,  # 1 sender
        ADDR_B,  # 2 recipient
        5,  # 3 num_of_initial_validators / initialRotations
        0,  # 4 tx_slot
        1700000000,  # 5 created_timestamp
        1700000001,  # 6 last_vote_timestamp
        ZERO_HASH,  # 7 random_seed
        1,  # 8 result
        ZERO_HASH,  # 9 txExecutionHash (a hash, NOT a result code)
        b"\x01\x02",  # 10 txCalldata
        b"",  # 11 eqBlocksOutputs
        [],  # 12 messages
        0,  # 13 queue_type
        0,  # 14 queue_position
        ADDR_C,  # 15 activator
        ADDR_D,  # 16 last_leader
        1,  # 17 status
        ZERO_HASH,  # 18 tx_id
        EMPTY_BLOCK_RANGE,  # 19 read_state_block_range
        1,  # 20 num_of_rounds
        EMPTY_LAST_ROUND,  # 21 last_round
        [],  # 22 consumedValidators
    )


class TestRawTransactionLightDecodeExecutionResult:
    def test_v04_tx_execution_result_is_none(self):
        tx = GenLayerRawTransaction.from_transaction_data(_v04_tuple())
        assert tx.tx_execution_result is None

    def test_v06_tx_execution_result_is_none(self):
        tx = GenLayerRawTransaction.from_transaction_data(_v06_tuple())
        assert tx.tx_execution_result is None

    def test_v06_dispatch_still_used_for_23_fields(self):
        # from_transaction_data dispatches on tuple length; confirm the v06 path
        # (not v04) actually ran by checking a field that differs in position.
        tx = GenLayerRawTransaction.from_transaction_data(_v06_tuple())
        assert tx.tx_data == "0x0102"  # txCalldata, at index 10 in v06

    def test_decode_reports_not_voted_name_when_result_unknown(self):
        # Public .decode() output must stay backward compatible: an unknown
        # (None) execution result still surfaces as the NOT_VOTED label.
        tx = GenLayerRawTransaction.from_transaction_data(_v04_tuple())
        decoded = tx.decode()
        assert decoded["tx_execution_result"] is None
        assert decoded["tx_execution_result_name"] == ExecutionResult.NOT_VOTED.value

    def test_all_transaction_data_path_is_unaffected(self):
        # The heavy getTransactionAllData path already reads a real value and
        # must keep doing so -- this fix only touches the light path.
        tx_data = (
            1,  # 0 result
            1,  # 1 tx_execution_result (FINISHED_WITH_RETURN)
            0,
            1,  # 3 status
            0,
            ADDR_A,  # 5 sender
            ADDR_B,  # 6 recipient
            ADDR_C,  # 7 activator/last_leader
            0,  # 8 tx_slot
            5,  # 9 num_of_initial_validators
            0,
            0,
            ZERO_HASH,  # 12 tx_id
            ZERO_HASH,  # 13 random_seed
            0,
            0,
            b"\x01\x02",  # 16 tx_data
            0,
            (EMPTY_BLOCK_RANGE,),  # 18 read_state_block_range history
        )
        tx = GenLayerRawTransaction.from_all_transaction_data(tx_data, rounds_data=[])
        assert tx.tx_execution_result == 1
