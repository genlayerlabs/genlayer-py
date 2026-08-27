from web3.eth import Eth
from web3 import Web3
from web3.types import Nonce, BlockIdentifier, ENS, _Hash32
from eth_typing import Address, ChecksumAddress, HexStr
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from typing import AnyStr, Literal
from genlayer_py.types import (
    GenLayerChain,
    CalldataEncodable,
    GenLayerTransaction,
    ContractSchema,
    TransactionHashVariant,
    SimConfig,
)
from genlayer_py.provider import GenLayerProvider
from typing import Optional, Union, List, Dict
from genlayer_py.accounts.actions import get_current_nonce, fund_account
from genlayer_py.contracts.actions import (
    read_contract,
    write_contract,
    deploy_contract,
    appeal_transaction,
    top_up_fees,
    top_up_and_submit_appeal,
    get_round_number,
    get_round_data,
    get_last_round_data,
    can_appeal,
    get_appeal_quote,
    get_appeal_charge,
    get_min_appeal_bond,
    get_contract_schema,
    get_contract_schema_for_code,
    simulate_write_contract,
    get_current_fee_policy,
    estimate_fees_distribution,
    estimate_transaction_fees,
    estimate_transaction_fees_from_simulation,
    estimate_transaction_fees_for_write,
)
from genlayer_py.chains.actions import initialize_consensus_smart_contract
from genlayer_py.transactions.actions import (
    wait_for_decision,
    wait_for_finalization,
    wait_for_transaction_receipt,
    get_transaction,
    get_transaction_lifecycle,
    get_triggered_transaction_ids,
    debug_trace_transaction,
)
from genlayer_py.types.transactions import ProtocolTransactionLifecycle
from genlayer_py.staking.actions import (
    validator_join,
    validator_deposit,
    validator_exit,
    validator_claim,
    validator_prime,
    set_operator,
    get_operator_transfer_context,
    get_validator_join_context,
    initiate_operator_transfer,
    complete_operator_transfer,
    cancel_operator_transfer,
    get_pending_operator,
    set_identity,
    delegator_join,
    delegator_exit,
    delegator_claim,
    epoch as staking_epoch,
    active_validators,
    active_validators_count,
    joined_validators,
    joined_validators_count,
    is_validator,
    get_validator_info,
    get_stake_info,
    banned_validators,
    validator_min_stake,
    delegator_min_stake,
)
from genlayer_py.staking.operator_registration import (
    OperatorRegistrationContext,
    OperatorRegistrationProof,
)
from genlayer_py.config import transaction_config
from genlayer_py.transactions.fees import (
    FeeEstimateOptions,
    FeesDistributionInput,
    TransactionFeeOptions,
    SimulationFeeEstimateOptions,
)


class GenLayerClient(Eth):
    """Client for interacting with the GenLayer network.

    Provides methods for deploying and calling intelligent contracts,
    managing transactions, and staking operations.
    """

    def __init__(
        self, chain_config: GenLayerChain, account: Optional[LocalAccount] = None
    ):
        self.chain = chain_config
        self.local_account = account
        url = chain_config.rpc_urls["default"]["http"][0]
        self.provider = GenLayerProvider(url)
        web3 = Web3(provider=self.provider)

        super().__init__(web3)

    ## Account actions
    def fund_account(
        self, address: Union[Address, ChecksumAddress, ENS], amount: int
    ) -> HexBytes:
        """Funds an account with test tokens. Localnet only."""
        return fund_account(self, address, amount)

    def get_current_nonce(
        self,
        address: Optional[Union[Address, ChecksumAddress, ENS]] = None,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> Nonce:
        """Returns the current nonce (transaction count) for an account."""
        return get_current_nonce(self, address, block_identifier)

    # Chain actions
    def initialize_consensus_smart_contract(
        self,
        force_reset: bool = False,
    ) -> None:
        """Initializes the consensus contract configuration from the network."""
        return initialize_consensus_smart_contract(self=self, force_reset=force_reset)

    # Contract actions
    def read_contract(
        self,
        address: Union[Address, ChecksumAddress],
        function_name: str,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
        account: Optional[LocalAccount] = None,
        raw_return: bool = False,
        transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
        sim_config: Optional[SimConfig] = None,
    ):
        """Executes a read-only contract call without modifying state."""
        return read_contract(
            self=self,
            address=address,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            account=account,
            raw_return=raw_return,
            transaction_hash_variant=transaction_hash_variant,
            sim_config=sim_config,
        )

    def write_contract(
        self,
        address: Union[Address, ChecksumAddress],
        function_name: str,
        account: Optional[LocalAccount] = None,
        consensus_max_rotations: Optional[int] = None,
        value: int = 0,
        leader_only: bool = False,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
        sim_config: Optional[SimConfig] = None,
        valid_until: Optional[int] = None,
        fees: Optional[TransactionFeeOptions] = None,
    ):
        """Executes a state-modifying function on a contract through consensus. Returns the transaction hash."""
        return write_contract(
            self=self,
            address=address,
            function_name=function_name,
            account=account,
            consensus_max_rotations=consensus_max_rotations,
            value=value,
            leader_only=leader_only,
            args=args,
            kwargs=kwargs,
            sim_config=sim_config,
            valid_until=valid_until,
            fees=fees,
        )

    def simulate_write_contract(
        self,
        address: Union[Address, ChecksumAddress],
        function_name: str,
        account: Optional[LocalAccount] = None,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
        value: int = 0,
        leader_only: bool = False,
        fees: Optional[TransactionFeeOptions] = None,
        sim_config: Optional[SimConfig] = None,
        transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
    ):
        """Simulates a state-modifying contract call without executing on-chain. Localnet only."""
        return simulate_write_contract(
            self=self,
            address=address,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            account=account,
            value=value,
            leader_only=leader_only,
            fees=fees,
            sim_config=sim_config,
            transaction_hash_variant=transaction_hash_variant,
        )

    def deploy_contract(
        self,
        code: Union[str, bytes],
        account: Optional[LocalAccount] = None,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
        consensus_max_rotations: Optional[int] = None,
        leader_only: bool = False,
        sim_config: Optional[SimConfig] = None,
        valid_until: Optional[int] = None,
        fees: Optional[TransactionFeeOptions] = None,
    ):
        """Deploys a new intelligent contract to GenLayer. Returns the transaction hash."""
        return deploy_contract(
            self=self,
            code=code,
            account=account,
            args=args,
            kwargs=kwargs,
            consensus_max_rotations=consensus_max_rotations,
            leader_only=leader_only,
            sim_config=sim_config,
            valid_until=valid_until,
            fees=fees,
        )

    def get_contract_schema(
        self,
        address: Union[Address, ChecksumAddress],
    ) -> ContractSchema:
        """Gets the schema (methods and constructor) of a deployed contract. Localnet only."""
        return get_contract_schema(
            self=self,
            address=address,
        )

    def get_contract_schema_for_code(
        self,
        contract_code: AnyStr,
    ) -> ContractSchema:
        """Generates a schema for contract code without deploying it. Localnet only."""
        return get_contract_schema_for_code(
            self=self,
            contract_code=contract_code,
        )

    def get_current_fee_policy(self):
        """Returns the active fee price policy used to build user-side caps."""
        return get_current_fee_policy(self=self)

    def estimate_fees_distribution(
        self,
        options: Optional[FeeEstimateOptions] = None,
    ):
        """Builds a fee distribution with caps derived from the active fee policy."""
        return estimate_fees_distribution(self=self, options=options)

    def estimate_transaction_fees(
        self,
        options: Optional[FeeEstimateOptions] = None,
    ):
        """Builds a complete transaction fees object, including feeValue."""
        return estimate_transaction_fees(self=self, options=options)

    def estimate_transaction_fees_from_simulation(
        self,
        options: SimulationFeeEstimateOptions,
    ):
        """Builds a complete transaction fees object from a representative simulation."""
        return estimate_transaction_fees_from_simulation(self=self, options=options)

    def estimate_transaction_fees_for_write(
        self,
        address: Union[Address, ChecksumAddress],
        function_name: str,
        account: Optional[LocalAccount] = None,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
        value: int = 0,
        leader_only: bool = False,
        options: Optional[FeeEstimateOptions] = None,
        sim_config: Optional[SimConfig] = None,
        transaction_hash_variant: TransactionHashVariant = TransactionHashVariant.LATEST_NONFINAL,
    ):
        """Builds a complete transaction fees object for a concrete write call."""
        return estimate_transaction_fees_for_write(
            self=self,
            address=address,
            function_name=function_name,
            account=account,
            args=args,
            kwargs=kwargs,
            value=value,
            leader_only=leader_only,
            options=options,
            sim_config=sim_config,
            transaction_hash_variant=transaction_hash_variant,
        )

    def top_up_fees(
        self,
        transaction_id: HexStr,
        distribution: FeesDistributionInput,
        value: int,
        account: Optional[LocalAccount] = None,
    ) -> HexStr:
        """Deposits additional fee budget for an existing consensus transaction."""
        return top_up_fees(
            self=self,
            transaction_id=transaction_id,
            distribution=distribution,
            account=account,
            value=value,
        )

    def top_up_and_submit_appeal(
        self,
        transaction_id: HexStr,
        distribution: FeesDistributionInput,
        account: Optional[LocalAccount] = None,
        value: Optional[int] = None,
        expected_decision_id: Optional[int] = None,
    ) -> HexStr:
        """Deposits appeal funding and submits the exact active decision.

        When ``expected_decision_id`` or ``value`` is omitted, the SDK obtains
        both from the lightweight consensus appeal quote. Studio chains predate
        that quote: they take the pre-train call shape, reject
        ``expected_decision_id``, and require an explicit ``value``.
        """
        return top_up_and_submit_appeal(
            self=self,
            transaction_id=transaction_id,
            distribution=distribution,
            account=account,
            value=value,
            expected_decision_id=expected_decision_id,
        )

    # Transaction actions
    def wait_for_transaction_receipt(
        self,
        transaction_hash: _Hash32,
        wait_until: Literal["decided", "finalized"] = "decided",
        interval: int = transaction_config.wait_interval,
        retries: int = transaction_config.retries,
        full_transaction: bool = False,
    ) -> GenLayerTransaction:
        """Poll for a stored decision (default) or stored finalization."""
        return wait_for_transaction_receipt(
            self=self,
            transaction_hash=transaction_hash,
            wait_until=wait_until,
            interval=interval,
            retries=retries,
            full_transaction=full_transaction,
        )

    def wait_for_decision(
        self,
        transaction_hash: _Hash32,
        interval: int = transaction_config.wait_interval,
        retries: int = transaction_config.retries,
        full_transaction: bool = False,
    ) -> GenLayerTransaction:
        """Poll until the stored transaction state is decided or terminal."""
        return wait_for_decision(
            self=self,
            transaction_hash=transaction_hash,
            interval=interval,
            retries=retries,
            full_transaction=full_transaction,
        )

    def wait_for_finalization(
        self,
        transaction_hash: _Hash32,
        interval: int = transaction_config.wait_interval,
        retries: int = transaction_config.retries,
        full_transaction: bool = False,
    ) -> GenLayerTransaction:
        """Poll until the stored transaction state is finalized."""
        return wait_for_finalization(
            self=self,
            transaction_hash=transaction_hash,
            interval=interval,
            retries=retries,
            full_transaction=full_transaction,
        )

    def get_transaction(
        self,
        transaction_hash: _Hash32,
    ) -> GenLayerTransaction:
        """Fetch transaction data with a stable stored-state ``lifecycle``.

        The lifecycle's ``state`` is one of processing, decided, finalized, or
        canceled. Processing carries ``phase`` and decided carries ``outcome``.
        The train exposes ``tx_execution_hash``; legacy receipt bytes are
        unavailable, so ``tx_receipt`` is ``None``.
        """
        return get_transaction(self=self, transaction_hash=transaction_hash)

    def get_transaction_lifecycle(
        self,
        transaction_hash: _Hash32,
        timestamp: Optional[int] = None,
    ) -> ProtocolTransactionLifecycle:
        """Return advanced stored/projected/action protocol lifecycle data."""
        return get_transaction_lifecycle(
            self=self,
            transaction_hash=transaction_hash,
            timestamp=timestamp,
        )

    def get_triggered_transaction_ids(
        self,
        transaction_hash: _Hash32,
    ) -> list:
        """Returns transaction IDs of child transactions created from emitted messages."""
        return get_triggered_transaction_ids(
            self=self, transaction_hash=transaction_hash
        )

    def debug_trace_transaction(
        self,
        transaction_hash: _Hash32,
        round: int = 0,
    ) -> dict:
        """Fetches the full execution trace including return data, stdout, stderr, and GenVM logs."""
        return debug_trace_transaction(
            self=self, transaction_hash=transaction_hash, round=round
        )

    def appeal_transaction(
        self,
        transaction_id: HexStr,
        account: Optional[LocalAccount] = None,
        value: Optional[int] = None,
        expected_decision_id: Optional[int] = None,
    ):
        """Appeals a consensus transaction to trigger a new round of validation.
        Returns the original transaction_id (appeals operate on the same tx).
        Missing decision/value inputs are filled from the latest appeal quote.
        Studio chains predate that quote: they take the pre-train call shape,
        reject ``expected_decision_id``, and require an explicit ``value``.
        """
        return appeal_transaction(
            self=self,
            transaction_id=transaction_id,
            account=account,
            value=value,
            expected_decision_id=expected_decision_id,
        )

    def get_round_number(self, transaction_id: HexStr) -> int:
        """Returns the current consensus round number for a transaction."""
        return get_round_number(self=self, transaction_id=transaction_id)

    def get_round_data(self, transaction_id: HexStr, round: int) -> dict:
        """Returns detailed data for a specific consensus round."""
        return get_round_data(self=self, transaction_id=transaction_id, round=round)

    def get_last_round_data(self, transaction_id: HexStr) -> tuple:
        """Returns the current round number and its data."""
        return get_last_round_data(self=self, transaction_id=transaction_id)

    def can_appeal(
        self,
        transaction_id: HexStr,
        expected_decision_id: Optional[int] = None,
    ) -> bool:
        """Checks whether the exact active decision can be appealed."""
        return can_appeal(
            self=self,
            transaction_id=transaction_id,
            expected_decision_id=expected_decision_id,
        )

    def get_appeal_quote(self, transaction_id: HexStr) -> Dict[str, int]:
        """Returns the latest decision id, appeal charges, and deadline.
        Not available on studio chains, whose consensus predates the quote.
        """
        return get_appeal_quote(self=self, transaction_id=transaction_id)

    def get_appeal_charge(self, transaction_id: HexStr) -> int:
        """Returns the full appeal payment (bond plus induced-work funding).
        Not available on studio chains, whose consensus predates the quote.
        """
        return get_appeal_charge(self=self, transaction_id=transaction_id)

    def get_min_appeal_bond(self, transaction_id: HexStr) -> int:
        """Deprecated alias for :meth:`get_appeal_charge`."""
        return get_min_appeal_bond(self=self, transaction_id=transaction_id)

    # ── Staking actions (EVM, not consensus-layer) ────────────────────
    # Mirrors genlayer-js StakingActions. Requires chain.staking_contract
    # to be set — see examples/staking.py or the bradbury chain preset.

    def staking_epoch(self) -> int:
        """Returns the current staking epoch."""
        return staking_epoch(self=self)

    def active_validators(self) -> List:
        """Returns ValidatorWallet addresses currently eligible for duties."""
        return active_validators(self=self)

    def active_validators_count(self) -> int:
        """Returns the number of validators currently eligible for duties."""
        return active_validators_count(self=self)

    def joined_validators(self) -> List:
        """Returns every ValidatorWallet in the append-only joined registry."""
        return joined_validators(self=self)

    def joined_validators_count(self) -> int:
        """Returns the size of the append-only joined validator registry."""
        return joined_validators_count(self=self)

    def is_validator(self, address) -> bool:
        return is_validator(self=self, address=address)

    def get_validator_info(self, validator) -> dict:
        """Returns the raw validatorView struct for a validator wallet."""
        return get_validator_info(self=self, validator=validator)

    def get_stake_info(self, delegator, validator) -> dict:
        """Returns a delegator's stake position on a validator."""
        return get_stake_info(self=self, delegator=delegator, validator=validator)

    def banned_validators(self, start_index: int = 0, size: int = 100) -> List:
        return banned_validators(self=self, start_index=start_index, size=size)

    def validator_min_stake(self) -> int:
        return validator_min_stake(self=self)

    def delegator_min_stake(self) -> int:
        return delegator_min_stake(self=self)

    def validator_join(
        self,
        amount: int,
        registration: Optional[OperatorRegistrationProof] = None,
        account: Optional[LocalAccount] = None,
        operator=None,
    ) -> HexBytes:
        """Joins with a proof-bound operator key and deploys a ValidatorWallet."""
        return validator_join(
            self=self,
            amount=amount,
            registration=registration,
            account=account,
            operator=operator,
        )

    def get_validator_join_context(
        self, account: Optional[LocalAccount] = None
    ) -> OperatorRegistrationContext:
        """Factory-bound context for building a validator join proof."""
        return get_validator_join_context(self=self, account=account)

    def validator_deposit(
        self, validator, amount: int, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Adds stake to an active validator. Routed via the wallet so
        Staking sees msg.sender == wallet (required by the contract)."""
        return validator_deposit(
            self=self, validator=validator, amount=amount, account=account
        )

    def validator_exit(
        self, validator, shares: int, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Burns validator shares. Routed via the wallet."""
        return validator_exit(
            self=self, validator=validator, shares=shares, account=account
        )

    def validator_claim(
        self, validator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return validator_claim(self=self, validator=validator, account=account)

    def validator_prime(
        self, validator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return validator_prime(self=self, validator=validator, account=account)

    def set_operator(
        self, validator, operator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Raises with migration guidance for proof-based operator rotation."""
        return set_operator(
            self=self, validator=validator, operator=operator, account=account
        )

    def get_operator_transfer_context(self, validator):
        """Wallet-bound context for building a rotation proof."""
        return get_operator_transfer_context(self=self, validator=validator)

    def initiate_operator_transfer(
        self, validator, registration, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Starts the two-step operator rotation (CON-715)."""
        return initiate_operator_transfer(
            self=self, validator=validator, registration=registration, account=account
        )

    def complete_operator_transfer(
        self, validator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Finalises a pending operator rotation."""
        return complete_operator_transfer(
            self=self, validator=validator, account=account
        )

    def cancel_operator_transfer(
        self, validator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        """Abandons a pending operator rotation."""
        return cancel_operator_transfer(self=self, validator=validator, account=account)

    def get_pending_operator(self, validator) -> dict:
        """Pending operator and when its transfer was initiated."""
        return get_pending_operator(self=self, validator=validator)

    def set_identity(
        self, validator, moniker: str, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return set_identity(
            self=self, validator=validator, moniker=moniker, account=account
        )

    def delegator_join(
        self, validator, amount: int, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return delegator_join(
            self=self, validator=validator, amount=amount, account=account
        )

    def delegator_exit(
        self, validator, shares: int, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return delegator_exit(
            self=self, validator=validator, shares=shares, account=account
        )

    def delegator_claim(
        self, validator, account: Optional[LocalAccount] = None
    ) -> HexBytes:
        return delegator_claim(self=self, validator=validator, account=account)
