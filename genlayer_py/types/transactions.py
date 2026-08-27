from genlayer_py.logging import logger
import rlp
import base64
from genlayer_py.abi import calldata
from enum import Enum
from typing import Dict, Optional, Any, TypedDict, List, Tuple, Literal, Union
from eth_typing import Address, HexStr
from web3 import Web3
from dataclasses import dataclass
from genlayer_py.utils.jsonifier import RESULT_CODES
from genlayer_py.consensus.consensus_main import decode_tx_data


class TransactionStatus(str, Enum):
    """Status of a GenLayer transaction in the consensus lifecycle."""

    UNINITIALIZED = "UNINITIALIZED"
    PENDING = "PENDING"
    PROPOSING = "PROPOSING"
    COMMITTING = "COMMITTING"
    REVEALING = "REVEALING"
    ACCEPTED = "ACCEPTED"
    UNDETERMINED = "UNDETERMINED"
    FINALIZED = "FINALIZED"
    CANCELED = "CANCELED"
    APPEAL_REVEALING = "APPEAL_REVEALING"
    APPEAL_COMMITTING = "APPEAL_COMMITTING"
    VALIDATORS_TIMEOUT = "VALIDATORS_TIMEOUT"
    LEADER_TIMEOUT = "LEADER_TIMEOUT"
    LEADER_REVEALING = "LEADER_REVEALING"


class ResolutionAction(str, Enum):
    """Action projected by the transaction lifecycle resolution kernel."""

    NO_OP = "NO_OP"
    CANCEL = "CANCEL"
    REPLACE_ACTOR = "REPLACE_ACTOR"
    ROTATE_LEADER = "ROTATE_LEADER"
    RESOLVE_APPEAL = "RESOLVE_APPEAL"
    MATERIALIZE_DECISION = "MATERIALIZE_DECISION"
    FINALIZE = "FINALIZE"


RESOLUTION_ACTION_NUMBER_TO_NAME = {
    "0": ResolutionAction.NO_OP,
    "1": ResolutionAction.CANCEL,
    "2": ResolutionAction.REPLACE_ACTOR,
    "3": ResolutionAction.ROTATE_LEADER,
    "4": ResolutionAction.RESOLVE_APPEAL,
    "5": ResolutionAction.MATERIALIZE_DECISION,
    "6": ResolutionAction.FINALIZE,
}


# Finalization readiness is a lifecycle resolution action, not a stored or
# projected transaction status. Removing ReadyToFinalize at ordinal 11 shifted
# the three statuses above it down.
TRANSACTION_STATUS_NUMBER_TO_NAME = {
    "0": TransactionStatus.UNINITIALIZED,
    "1": TransactionStatus.PENDING,
    "2": TransactionStatus.PROPOSING,
    "3": TransactionStatus.COMMITTING,
    "4": TransactionStatus.REVEALING,
    "5": TransactionStatus.ACCEPTED,
    "6": TransactionStatus.UNDETERMINED,
    "7": TransactionStatus.FINALIZED,
    "8": TransactionStatus.CANCELED,
    "9": TransactionStatus.APPEAL_REVEALING,
    "10": TransactionStatus.APPEAL_COMMITTING,
    "11": TransactionStatus.VALIDATORS_TIMEOUT,
    "12": TransactionStatus.LEADER_TIMEOUT,
    "13": TransactionStatus.LEADER_REVEALING,
}

TRANSACTION_STATUS_NAME_TO_NUMBER = {
    TransactionStatus.UNINITIALIZED: "0",
    TransactionStatus.PENDING: "1",
    TransactionStatus.PROPOSING: "2",
    TransactionStatus.COMMITTING: "3",
    TransactionStatus.REVEALING: "4",
    TransactionStatus.ACCEPTED: "5",
    TransactionStatus.UNDETERMINED: "6",
    TransactionStatus.FINALIZED: "7",
    TransactionStatus.CANCELED: "8",
    TransactionStatus.APPEAL_REVEALING: "9",
    TransactionStatus.APPEAL_COMMITTING: "10",
    TransactionStatus.VALIDATORS_TIMEOUT: "11",
    TransactionStatus.LEADER_TIMEOUT: "12",
    TransactionStatus.LEADER_REVEALING: "13",
}

DECIDED_STATES = [
    TransactionStatus.ACCEPTED,
    TransactionStatus.UNDETERMINED,
    TransactionStatus.LEADER_TIMEOUT,
    TransactionStatus.VALIDATORS_TIMEOUT,
    TransactionStatus.CANCELED,
    TransactionStatus.FINALIZED,
]


def is_decided_state(status: str) -> bool:
    return status in [
        TRANSACTION_STATUS_NAME_TO_NUMBER[state] for state in DECIDED_STATES
    ]


class TransactionResult(str, Enum):
    """Consensus voting result across validators."""

    IDLE = "IDLE"
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    TIMEOUT = "TIMEOUT"
    DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"
    NO_MAJORITY = "NO_MAJORITY"
    MAJORITY_AGREE = "MAJORITY_AGREE"
    MAJORITY_DISAGREE = "MAJORITY_DISAGREE"
    MAJORITY_TIMEOUT = "MAJORITY_TIMEOUT"


TRANSACTION_RESULT_NUMBER_TO_NAME = {
    "0": TransactionResult.IDLE,
    "1": TransactionResult.MAJORITY_AGREE,
    "2": TransactionResult.MAJORITY_DISAGREE,
    "3": TransactionResult.MAJORITY_TIMEOUT,
    "4": TransactionResult.DETERMINISTIC_VIOLATION,
    "5": TransactionResult.NO_MAJORITY,
}


TRANSACTION_RESULT_NAME_TO_NUMBER = {
    TransactionResult.IDLE: "0",
    TransactionResult.MAJORITY_AGREE: "1",
    TransactionResult.MAJORITY_DISAGREE: "2",
    TransactionResult.MAJORITY_TIMEOUT: "3",
    TransactionResult.DETERMINISTIC_VIOLATION: "4",
    TransactionResult.NO_MAJORITY: "5",
}


class ExecutionResult(str, Enum):
    """Result of contract execution by the GenVM."""

    NOT_VOTED = "NOT_VOTED"
    FINISHED_WITH_RETURN = "FINISHED_WITH_RETURN"
    FINISHED_WITH_ERROR = "FINISHED_WITH_ERROR"
    TIMEOUT = "TIMEOUT"
    NONDET_DISAGREE = "NONDET_DISAGREE"
    DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"


EXECUTION_RESULT_NUMBER_TO_NAME = {
    "0": ExecutionResult.NOT_VOTED,
    "1": ExecutionResult.FINISHED_WITH_RETURN,
    "2": ExecutionResult.FINISHED_WITH_ERROR,
    "3": ExecutionResult.TIMEOUT,
    "4": ExecutionResult.NONDET_DISAGREE,
    "5": ExecutionResult.DETERMINISTIC_VIOLATION,
}


class VoteType(str, Enum):
    """Validator execution vote recorded for a consensus round."""

    NOT_VOTED = "NOT_VOTED"
    FINISHED_WITH_RETURN = "FINISHED_WITH_RETURN"
    FINISHED_WITH_ERROR = "FINISHED_WITH_ERROR"
    TIMEOUT = "TIMEOUT"
    NONDET_DISAGREE = "NONDET_DISAGREE"
    DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"


VOTE_TYPE_NUMBER_TO_NAME = {
    "0": VoteType.NOT_VOTED,
    "1": VoteType.FINISHED_WITH_RETURN,
    "2": VoteType.FINISHED_WITH_ERROR,
    "3": VoteType.TIMEOUT,
    "4": VoteType.NONDET_DISAGREE,
    "5": VoteType.DETERMINISTIC_VIOLATION,
}

VOTE_TYPE_NAME_TO_NUMBER = {
    VoteType.NOT_VOTED: "0",
    VoteType.FINISHED_WITH_RETURN: "1",
    VoteType.FINISHED_WITH_ERROR: "2",
    VoteType.TIMEOUT: "3",
    VoteType.NONDET_DISAGREE: "4",
    VoteType.DETERMINISTIC_VIOLATION: "5",
}


class TransactionHashVariant(str, Enum):
    LATEST_FINAL = "latest-final"
    LATEST_NONFINAL = "latest-nonfinal"


TransactionType = Literal["deploy", "call"]


class DecodedDeployData(TypedDict, total=False):
    code: Optional[HexStr]
    constructor_args: Optional[Any]
    leader_only: Optional[bool]
    type: Optional[TransactionType]
    contract_address: Optional[Address]


class DecodedCallData(TypedDict, total=False):
    call_data: Optional[Any]
    leader_only: Optional[bool]
    type: Optional[TransactionType]


class GenLayerTransaction(TypedDict, total=False):
    """Decoded transaction data returned by get_transaction and wait_for_transaction_receipt."""

    # currentTimestamp: testnet
    current_timestamp: Optional[str]

    # from_address: localnet // sender: testnet
    from_address: Optional[Address]
    sender: Optional[Address]

    # to_address: localnet // recipient: testnet
    to_address: Optional[Address]
    recipient: Optional[Address]

    # numOfInitialValidators: testnet
    num_of_initial_validators: Optional[str]
    initial_rotations: Optional[str]

    # txSlot: testnet
    tx_slot: Optional[str]

    # createdTimestamp: testnet
    created_timestamp: Optional[str]

    # lastVoteTimestamp: testnet
    last_vote_timestamp: Optional[str]

    # randomSeed: testnet
    random_seed: Optional[HexStr]

    # result: testnet
    result: Optional[int]
    result_name: Optional[TransactionResult]

    # tx_execution_result: testnet (from getTransactionAllData)
    tx_execution_result: Optional[int]
    tx_execution_result_name: Optional[str]

    # data: localnet // txData: testnet
    data: Optional[Dict[str, Any]]
    tx_data: Optional[HexStr]
    tx_data_decoded: Optional[Dict[str, Any]]

    # The train stores only the execution hash. `tx_receipt` remains present so
    # callers can distinguish unavailable legacy bytes (`None`) explicitly.
    tx_execution_hash: Optional[HexStr]
    tx_receipt: Optional[HexStr]

    # messages: testnet
    messages: Optional[List[Any]]

    # consumedValidators: testnet
    consumed_validators: Optional[List[Address]]

    # queueType: testnet
    queue_type: Optional[int]

    # queuePosition: testnet
    queue_position: Optional[str]

    # activator: testnet
    activator: Optional[Address]

    # lastLeader: testnet
    last_leader: Optional[Address]

    # status: localnet: TransactionStatus // status: testnet: number
    status: Optional[TransactionStatus]
    status_name: Optional[TransactionStatus]
    stored_status: Optional[str]
    stored_status_name: Optional[TransactionStatus]
    resolution_action: Optional[ResolutionAction]
    can_finalize: Optional[bool]

    # hash: localnet // txId: testnet// hash: localnet // txId: testnet
    hash: Optional[HexStr]
    tx_id: Optional[HexStr]

    # readStateBlockRange: testnet
    read_state_block_range: Optional[Dict[str, Any]]

    # numOfRounds: testnet
    num_of_rounds: Optional[str]

    # lastRound: testnet
    last_round: Optional[Dict[str, Any]]

    consensus_data: Optional[Dict[str, Any]]
    nonce: Optional[int]
    value: Optional[int]
    type: Optional[int]
    gaslimit: Optional[int]
    created_at: Optional[str]
    r: Optional[int]
    s: Optional[int]
    v: Optional[int]


@dataclass
class GenLayerRawTransaction:

    @dataclass
    class ReadStateBlockRange:
        activation_block: int
        processing_block: int
        proposal_block: int

        @classmethod
        def from_transaction_data(
            cls, tx_data: Tuple
        ) -> "GenLayerRawTransaction.ReadStateBlockRange":
            return cls(
                activation_block=tx_data[0],
                processing_block=tx_data[1],
                proposal_block=tx_data[2],
            )

        def decode(self) -> Dict[str, Any]:
            return {
                "activation_block": str(self.activation_block),
                "processing_block": str(self.processing_block),
                "proposal_block": str(self.proposal_block),
            }

    @dataclass
    class LastRound:
        round: int
        leader_index: int
        votes_committed: int
        votes_revealed: int
        appeal_bond: int
        rotations_left: int
        result: int
        round_validators: List[Address]
        validator_votes_hash: List[HexStr]
        validator_result_hash: List[HexStr]
        validator_votes: List[int]

        @classmethod
        def from_light_data(
            cls,
            tx_data: Tuple,
            round_validators: List[Address],
            validator_votes: List[int],
            validator_votes_hash: List[HexStr],
            validator_result_hash: List[HexStr],
        ) -> "GenLayerRawTransaction.LastRound":
            return cls(
                round=tx_data[0],
                leader_index=tx_data[1],
                votes_committed=tx_data[2],
                votes_revealed=tx_data[3],
                appeal_bond=tx_data[4],
                rotations_left=tx_data[5],
                result=tx_data[6],
                round_validators=round_validators,
                validator_votes=validator_votes,
                validator_votes_hash=[
                    Web3.to_hex(vote_hash) for vote_hash in validator_votes_hash
                ],
                validator_result_hash=[
                    Web3.to_hex(result_hash) for result_hash in validator_result_hash
                ],
            )

        def decode(self) -> Dict[str, Any]:
            return {
                "round": str(self.round),
                "leader_index": str(self.leader_index),
                "votes_committed": str(self.votes_committed),
                "votes_revealed": str(self.votes_revealed),
                "appeal_bond": str(self.appeal_bond),
                "rotations_left": str(self.rotations_left),
                "result": str(self.result),
                "round_validators": self.round_validators,
                "validator_votes_hash": self.validator_votes_hash,
                "validator_result_hash": self.validator_result_hash,
                "validator_votes": self.validator_votes,
                "validator_votes_name": [
                    VOTE_TYPE_NUMBER_TO_NAME[str(vote)].value
                    for vote in self.validator_votes
                ],
            }

    current_timestamp: int
    sender: Address
    recipient: Address
    num_of_initial_validators: int
    initial_rotations: int
    tx_slot: int
    created_timestamp: int
    last_vote_timestamp: int
    random_seed: HexStr
    result: int
    tx_execution_result: int
    tx_data: HexStr
    tx_execution_hash: HexStr
    tx_receipt: Optional[HexStr]
    messages: List[Any]
    consumed_validators: List[Address]
    queue_type: int
    queue_position: int
    activator: Address
    last_leader: Address
    status: int
    tx_id: HexStr
    read_state_block_range: ReadStateBlockRange
    num_of_rounds: int
    last_round: LastRound

    @classmethod
    def from_transaction_data_light(
        cls,
        tx_data: Tuple,
        round_validators: List[Address],
        validator_votes: List[int],
        validator_votes_hash: List[HexStr],
        validator_result_hash: List[HexStr],
        consumed_validators: List[Address],
        tx_execution_result: int,
        num_of_initial_validators: int,
    ) -> "GenLayerRawTransaction":
        """Parse the bounded train transaction view and separately read arrays."""
        return cls(
            current_timestamp=tx_data[0],
            sender=tx_data[1],
            recipient=tx_data[2],
            num_of_initial_validators=num_of_initial_validators,
            initial_rotations=tx_data[3],
            tx_slot=tx_data[4],
            created_timestamp=tx_data[5],
            last_vote_timestamp=tx_data[6],
            random_seed=Web3.to_hex(tx_data[7]),
            result=tx_data[8],
            tx_execution_result=tx_execution_result,
            tx_data=Web3.to_hex(tx_data[10]),
            tx_execution_hash=Web3.to_hex(tx_data[9]),
            tx_receipt=None,
            messages=tx_data[12],
            consumed_validators=consumed_validators,
            queue_type=tx_data[13],
            queue_position=tx_data[14],
            activator=tx_data[15],
            last_leader=tx_data[16],
            status=tx_data[17],
            tx_id=Web3.to_hex(tx_data[18]),
            read_state_block_range=cls.ReadStateBlockRange.from_transaction_data(
                tx_data[19]
            ),
            num_of_rounds=tx_data[20],
            last_round=cls.LastRound.from_light_data(
                tx_data[21],
                round_validators,
                validator_votes,
                validator_votes_hash,
                validator_result_hash,
            ),
        )

    def decode(self) -> GenLayerTransaction:
        return {
            "current_timestamp": str(self.current_timestamp),
            "sender": self.sender,
            "recipient": self.recipient,
            "num_of_initial_validators": str(self.num_of_initial_validators),
            "initial_rotations": str(self.initial_rotations),
            "tx_slot": str(self.tx_slot),
            "created_timestamp": str(self.created_timestamp),
            "last_vote_timestamp": str(self.last_vote_timestamp),
            "random_seed": self.random_seed,
            "result": str(self.result),
            "tx_data": self.tx_data,
            "tx_execution_hash": self.tx_execution_hash,
            "tx_receipt": self.tx_receipt,
            "consensus_data": {
                "leader_receipt": self._decode_leader_receipt(),
            },
            "messages": self.messages,
            "consumed_validators": self.consumed_validators,
            "queue_type": str(self.queue_type),
            "queue_position": str(self.queue_position),
            "activator": self.activator,
            "last_leader": self.last_leader,
            "status": str(self.status),
            "tx_id": self.tx_id,
            "read_state_block_range": self.read_state_block_range.decode(),
            "num_of_rounds": str(self.num_of_rounds),
            "last_round": self.last_round.decode(),
            "tx_data_decoded": self._decode_input_data(),
            "status_name": TRANSACTION_STATUS_NUMBER_TO_NAME[str(self.status)].value,
            "result_name": TRANSACTION_RESULT_NUMBER_TO_NAME[str(self.result)].value,
            "tx_execution_result": self.tx_execution_result,
            "tx_execution_result_name": EXECUTION_RESULT_NUMBER_TO_NAME.get(
                str(self.tx_execution_result), ExecutionResult.NOT_VOTED
            ).value,
            "triggered_transactions": [],
        }

    def _decode_leader_receipt(self) -> Dict[str, Any]:
        if not self.tx_receipt or self.tx_receipt == "0x" or len(self.tx_receipt) <= 2:
            return None
        try:
            rlp_bytes = Web3.to_bytes(hexstr=self.tx_receipt)
            rlp_decoded_array = rlp.decode(rlp_bytes, strict=False)
            if len(rlp_decoded_array) != 2:
                raise Exception(
                    f"[decode_leader_receipt] Unexpected number of elements in RLP data: Got {len(rlp_decoded_array)}, expected 2"
                )
            execution_result = rlp_decoded_array[0]
            if len(execution_result) != 4:
                raise Exception(
                    f"[decode_leader_receipt] Unexpected number of elements in Execution Result data: Got {len(execution_result)}, expected 4"
                )
            if len(execution_result[0]) != 2:
                raise Exception(
                    f"[decode_leader_receipt] Unexpected number of elements in Execution Result [0] data: Got {len(execution_result[0])}, expected 2"
                )
            result_kind = int.from_bytes(execution_result[0][0], byteorder="big")
            return [
                {
                    "execution_result": "SUCCESS" if result_kind == 0 else "ERROR",
                    "result": {
                        "status": RESULT_CODES.get(result_kind, "<unknown>"),
                    },
                    "eq_outputs": self._decode_eq_outputs(rlp_decoded_array[1]),
                    "pending_transactions": self._decode_pending_transactions(
                        execution_result[1]
                    ),
                    "pending_eth_transactions": execution_result[2],
                    "storage_proof": Web3.to_hex(execution_result[3]),
                }
            ]

        except Exception as e:
            logger.warning(
                "[decode_leader_result] Error decoding RLP: %s Raw RLP App Data: %s",
                str(e),
                self.tx_receipt,
            )
            return None

    def _decode_pending_transactions(
        self, pending_transactions: List[bytes]
    ) -> List[Dict[str, Any]]:
        decoded_pending_transactions = []
        for pending_transaction in pending_transactions:
            decoded_pending_transactions.append(
                {
                    "account": pending_transaction[0],
                    "calldata": calldata.to_str(
                        calldata.decode(pending_transaction[1])
                    ),
                    "value": int.from_bytes(pending_transaction[2], byteorder="big"),
                    "on": (
                        "decided"
                        if int.from_bytes(pending_transaction[3], byteorder="big") == 0
                        else "finalized"
                    ),
                    "code": Web3.to_hex(pending_transaction[4]),
                    "salt_nonce": int.from_bytes(
                        pending_transaction[5], byteorder="big"
                    ),
                }
            )
        return decoded_pending_transactions

    def _decode_eq_outputs(self, eq_outputs: List[bytes]) -> Dict[int, str]:
        decoded_eq_outputs = {}
        for eq_output in eq_outputs:
            key = int.from_bytes(eq_output[0], byteorder="big")
            decoded_eq_outputs[key] = base64.b64encode(eq_output[1][1]).decode("utf-8")
        return decoded_eq_outputs

    def _decode_input_data(self) -> Union[DecodedDeployData, DecodedCallData, None]:
        if not self.tx_data or self.tx_data == "0x" or len(self.tx_data) <= 2:
            return None

        try:
            decoded_data = decode_tx_data(self.tx_data)
            if decoded_data is None:
                return None
            if decoded_data["type"] == "deploy":
                return {
                    "code": decoded_data["code"],
                    "constructor_args": decoded_data["constructor_args"],
                    "leader_only": decoded_data["leader_only"],
                    "type": "deploy",
                    "contract_address": self.recipient,
                }
            if decoded_data["type"] == "call":
                return {
                    "call_data": decoded_data["call_data"],
                    "leader_only": decoded_data["leader_only"],
                    "type": "call",
                }
        except Exception as e:
            logger.warning(
                "[decode_input_data] Error decoding RLP: %s Raw RLP App Data: %s",
                e,
                self.tx_data,
            )
            return None
