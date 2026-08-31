from genlayer_py.logging import logger
import rlp
import base64
from genlayer_py.abi import calldata
from enum import Enum
from typing import (
    Dict,
    Optional,
    Any,
    TypedDict,
    List,
    Tuple,
    Literal,
    Union,
    NotRequired,
)
from eth_typing import Address, HexStr
from web3 import Web3
from dataclasses import dataclass
from genlayer_py.utils.jsonifier import RESULT_CODES
from genlayer_py.consensus.consensus_main import decode_tx_data


class ProtocolTransactionStatus(str, Enum):
    """Raw transaction status stored by the consensus contracts.

    This protocol enum is intentionally advanced API. Consumer-facing
    transactions expose a small ``lifecycle`` value discriminated by ``state``
    instead.
    """

    UNINITIALIZED = "Uninitialized"
    PENDING = "Pending"
    PROPOSING = "Proposing"
    COMMITTING = "Committing"
    REVEALING = "Revealing"
    ACCEPTED = "Accepted"
    UNDETERMINED = "Undetermined"
    FINALIZED = "Finalized"
    CANCELED = "Canceled"
    APPEAL_REVEALING = "AppealRevealing"
    APPEAL_COMMITTING = "AppealCommitting"
    VALIDATORS_TIMEOUT = "ValidatorsTimeout"
    LEADER_TIMEOUT = "LeaderTimeout"
    LEADER_REVEALING = "LeaderRevealing"


class ResolutionAction(str, Enum):
    """Action projected by the transaction lifecycle resolution kernel."""

    NO_OP = "NoOp"
    CANCEL = "Cancel"
    REPLACE_ACTOR = "ReplaceActor"
    ROTATE_LEADER = "RotateLeader"
    RESOLVE_APPEAL = "ResolveAppeal"
    MATERIALIZE_DECISION = "MaterializeDecision"
    FINALIZE = "Finalize"


class ResolutionSource(str, Enum):
    """Protocol trigger that produced a transaction resolution plan."""

    UNSPECIFIED = "Unspecified"
    ACTIVATION_INSUFFICIENT_VALIDATORS = "ActivationInsufficientValidators"
    PROPOSAL_HANGING = "ProposalHanging"
    LEADER_RECEIPT_TIMEOUT = "LeaderReceiptTimeout"
    COMMIT_HANGING = "CommitHanging"
    LEADER_REVEAL_HANGING = "LeaderRevealHanging"
    FULL_REVEAL = "FullReveal"
    REVEAL_DEADLINE = "RevealDeadline"
    APPEAL_COMMIT_HANGING = "AppealCommitHanging"
    APPEAL_FULL_REVEAL = "AppealFullReveal"
    APPEAL_REVEAL_DEADLINE = "AppealRevealDeadline"
    SELECTION_DEPLETED = "SelectionDepleted"


RESOLUTION_ACTION_NUMBER_TO_NAME = {
    "0": ResolutionAction.NO_OP,
    "1": ResolutionAction.CANCEL,
    "2": ResolutionAction.REPLACE_ACTOR,
    "3": ResolutionAction.ROTATE_LEADER,
    "4": ResolutionAction.RESOLVE_APPEAL,
    "5": ResolutionAction.MATERIALIZE_DECISION,
    "6": ResolutionAction.FINALIZE,
}

RESOLUTION_SOURCE_NUMBER_TO_NAME = {
    str(number): source for number, source in enumerate(ResolutionSource)
}


TransactionProcessingPhase = Literal[
    "uninitialized",
    "pending",
    "proposing",
    "committing",
    "revealing",
    "appeal_revealing",
    "appeal_committing",
    "leader_revealing",
]
TransactionDecisionOutcome = Literal[
    "accepted", "undetermined", "validators_timeout", "leader_timeout"
]


class ProcessingTransactionLifecycle(TypedDict):
    state: Literal["processing"]
    phase: TransactionProcessingPhase


class DecidedTransactionLifecycle(TypedDict):
    state: Literal["decided"]
    outcome: TransactionDecisionOutcome


class FinalizedTransactionLifecycle(TypedDict):
    state: Literal["finalized"]
    outcome: NotRequired[TransactionDecisionOutcome]


class CanceledTransactionLifecycle(TypedDict):
    state: Literal["canceled"]


TransactionLifecycle = Union[
    ProcessingTransactionLifecycle,
    DecidedTransactionLifecycle,
    FinalizedTransactionLifecycle,
    CanceledTransactionLifecycle,
]


class ProtocolTransactionLifecycle(TypedDict):
    """Advanced resolution-kernel view for one fixed block snapshot."""

    stored_status: int
    stored_status_name: ProtocolTransactionStatus
    projected_status: int
    projected_status_name: ProtocolTransactionStatus
    resolution_action: int
    resolution_action_name: ResolutionAction
    resolution_source: int
    resolution_source_name: ResolutionSource
    decision_id: Optional[str]
    decision_active: bool
    evaluated_at: int


# Current train protocol ordinals. Finalization readiness is a resolution
# verdict, not a stored or projected transaction status.
PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME = {
    "0": ProtocolTransactionStatus.UNINITIALIZED,
    "1": ProtocolTransactionStatus.PENDING,
    "2": ProtocolTransactionStatus.PROPOSING,
    "3": ProtocolTransactionStatus.COMMITTING,
    "4": ProtocolTransactionStatus.REVEALING,
    "5": ProtocolTransactionStatus.ACCEPTED,
    "6": ProtocolTransactionStatus.UNDETERMINED,
    "7": ProtocolTransactionStatus.FINALIZED,
    "8": ProtocolTransactionStatus.CANCELED,
    "9": ProtocolTransactionStatus.APPEAL_REVEALING,
    "10": ProtocolTransactionStatus.APPEAL_COMMITTING,
    "11": ProtocolTransactionStatus.VALIDATORS_TIMEOUT,
    "12": ProtocolTransactionStatus.LEADER_TIMEOUT,
    "13": ProtocolTransactionStatus.LEADER_REVEALING,
}

PROTOCOL_TRANSACTION_STATUS_NAME_TO_NUMBER = {
    status: str(number) for number, status in enumerate(ProtocolTransactionStatus)
}

_PROCESSING_PHASE_BY_PROTOCOL_STATUS: Dict[
    ProtocolTransactionStatus, TransactionProcessingPhase
] = {
    ProtocolTransactionStatus.UNINITIALIZED: "uninitialized",
    ProtocolTransactionStatus.PENDING: "pending",
    ProtocolTransactionStatus.PROPOSING: "proposing",
    ProtocolTransactionStatus.COMMITTING: "committing",
    ProtocolTransactionStatus.REVEALING: "revealing",
    ProtocolTransactionStatus.APPEAL_REVEALING: "appeal_revealing",
    ProtocolTransactionStatus.APPEAL_COMMITTING: "appeal_committing",
    ProtocolTransactionStatus.LEADER_REVEALING: "leader_revealing",
}


def transaction_lifecycle_from_protocol_status(
    status: Union[int, str, ProtocolTransactionStatus],
) -> TransactionLifecycle:
    """Map every stored protocol status to the stable consumer lifecycle."""

    if isinstance(status, ProtocolTransactionStatus):
        protocol_status = status
    elif isinstance(status, int) or (isinstance(status, str) and status.isdigit()):
        try:
            protocol_status = PROTOCOL_TRANSACTION_STATUS_NUMBER_TO_NAME[str(status)]
        except KeyError as exc:
            raise ValueError(f"Unknown protocol transaction status: {status}") from exc
    else:
        try:
            status_text = str(status)
            protocol_status = (
                ProtocolTransactionStatus[status_text]
                if status_text in ProtocolTransactionStatus.__members__
                else ProtocolTransactionStatus(status_text)
            )
        except ValueError as exc:
            raise ValueError(f"Unknown protocol transaction status: {status}") from exc

    if protocol_status in _PROCESSING_PHASE_BY_PROTOCOL_STATUS:
        return {
            "state": "processing",
            "phase": _PROCESSING_PHASE_BY_PROTOCOL_STATUS[protocol_status],
        }
    if protocol_status == ProtocolTransactionStatus.ACCEPTED:
        return {"state": "decided", "outcome": "accepted"}
    if protocol_status == ProtocolTransactionStatus.UNDETERMINED:
        return {"state": "decided", "outcome": "undetermined"}
    if protocol_status == ProtocolTransactionStatus.VALIDATORS_TIMEOUT:
        return {"state": "decided", "outcome": "validators_timeout"}
    if protocol_status == ProtocolTransactionStatus.LEADER_TIMEOUT:
        return {"state": "decided", "outcome": "leader_timeout"}
    if protocol_status == ProtocolTransactionStatus.FINALIZED:
        return {"state": "finalized"}
    if protocol_status == ProtocolTransactionStatus.CANCELED:
        return {"state": "canceled"}
    raise AssertionError(f"Unmapped protocol transaction status: {protocol_status}")


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


def transaction_outcome_from_protocol_result(
    result: Union[int, str, TransactionResult],
) -> Optional[TransactionDecisionOutcome]:
    """Return an application outcome when a finalized record preserves one."""

    if isinstance(result, TransactionResult):
        result_name = result
    elif isinstance(result, int) or (isinstance(result, str) and result.isdigit()):
        result_name = TRANSACTION_RESULT_NUMBER_TO_NAME.get(str(result))
    else:
        try:
            result_name = TransactionResult(str(result))
        except ValueError:
            result_name = None

    if result_name == TransactionResult.MAJORITY_AGREE:
        return "accepted"
    if result_name == TransactionResult.MAJORITY_TIMEOUT:
        return "validators_timeout"
    if result_name in (
        TransactionResult.MAJORITY_DISAGREE,
        TransactionResult.DETERMINISTIC_VIOLATION,
        TransactionResult.NO_MAJORITY,
    ):
        return "undetermined"
    return None


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

    # Stable consumer lifecycle. Raw protocol values are returned only by
    # GenLayerClient.get_transaction_lifecycle().
    lifecycle: TransactionLifecycle

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
        lifecycle = transaction_lifecycle_from_protocol_status(self.status)
        if lifecycle["state"] == "finalized":
            outcome = transaction_outcome_from_protocol_result(self.result)
            if outcome is not None:
                lifecycle["outcome"] = outcome
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
            "lifecycle": lifecycle,
            "tx_id": self.tx_id,
            "read_state_block_range": self.read_state_block_range.decode(),
            "num_of_rounds": str(self.num_of_rounds),
            "last_round": self.last_round.decode(),
            "tx_data_decoded": self._decode_input_data(),
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
