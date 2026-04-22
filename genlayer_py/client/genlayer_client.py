from web3.eth import Eth
from web3 import Web3
from web3.types import Nonce, BlockIdentifier, ENS, _Hash32
from eth_typing import Address, ChecksumAddress, HexStr
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from typing import AnyStr
from genlayer_py.types import (
    GenLayerChain,
    TransactionStatus,
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
    get_round_number,
    get_round_data,
    get_last_round_data,
    can_appeal,
    get_min_appeal_bond,
    get_contract_schema,
    get_contract_schema_for_code,
    simulate_write_contract,
)
from genlayer_py.chains.actions import initialize_consensus_smart_contract
from genlayer_py.transactions.actions import (
    wait_for_transaction_receipt,
    get_transaction,
    get_triggered_transaction_ids,
    debug_trace_transaction,
)
from genlayer_py.staking.actions import (
    validator_join,
    validator_deposit,
    validator_exit,
    validator_claim,
    validator_prime,
    set_operator,
    set_identity,
    delegator_join,
    delegator_exit,
    delegator_claim,
    epoch as staking_epoch,
    active_validators,
    active_validators_count,
    is_validator,
    get_validator_info,
    get_stake_info,
    banned_validators,
    validator_min_stake,
    delegator_min_stake,
)
from genlayer_py.config import transaction_config


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
        )

    def simulate_write_contract(
        self,
        address: Union[Address, ChecksumAddress],
        function_name: str,
        account: Optional[LocalAccount] = None,
        args: Optional[List[CalldataEncodable]] = None,
        kwargs: Optional[Dict[str, CalldataEncodable]] = None,
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

    # Transaction actions
    def wait_for_transaction_receipt(
        self,
        transaction_hash: _Hash32,
        status: TransactionStatus = TransactionStatus.ACCEPTED,
        interval: int = transaction_config.wait_interval,
        retries: int = transaction_config.retries,
        full_transaction: bool = False,
    ) -> GenLayerTransaction:
        """Polls until a transaction reaches the specified status. Returns the transaction receipt."""
        return wait_for_transaction_receipt(
            self=self,
            transaction_hash=transaction_hash,
            status=status,
            interval=interval,
            retries=retries,
            full_transaction=full_transaction,
        )

    def get_transaction(
        self,
        transaction_hash: _Hash32,
    ) -> GenLayerTransaction:
        """Fetches transaction data including status, execution result, and consensus details."""
        return get_transaction(self=self, transaction_hash=transaction_hash)

    def get_triggered_transaction_ids(
        self,
        transaction_hash: _Hash32,
    ) -> list:
        """Returns transaction IDs of child transactions created from emitted messages."""
        return get_triggered_transaction_ids(self=self, transaction_hash=transaction_hash)

    def debug_trace_transaction(
        self,
        transaction_hash: _Hash32,
        round: int = 0,
    ) -> dict:
        """Fetches the full execution trace including return data, stdout, stderr, and GenVM logs."""
        return debug_trace_transaction(self=self, transaction_hash=transaction_hash, round=round)

    def appeal_transaction(
        self,
        transaction_id: HexStr,
        account: Optional[LocalAccount] = None,
        value: int = 0,
    ):
        """Appeals a consensus transaction to trigger a new round of validation.
        Returns the original transaction_id (appeals operate on the same tx)."""
        return appeal_transaction(
            self=self,
            transaction_id=transaction_id,
            account=account,
            value=value,
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

    def can_appeal(self, transaction_id: HexStr) -> bool:
        """Checks if a transaction can be appealed."""
        return can_appeal(self=self, transaction_id=transaction_id)

    def get_min_appeal_bond(self, transaction_id: HexStr) -> int:
        """Calculates the minimum bond required to appeal a transaction."""
        return get_min_appeal_bond(self=self, transaction_id=transaction_id)

    # ── Staking actions (EVM, not consensus-layer) ────────────────────
    # Mirrors genlayer-js StakingActions. Requires chain.staking_contract
    # to be set — see examples/staking.py or the bradbury chain preset.

    def staking_epoch(self) -> int:
        """Returns the current staking epoch."""
        return staking_epoch(self=self)

    def active_validators(self) -> List:
        """Returns ValidatorWallet addresses active in the current epoch."""
        return active_validators(self=self)

    def active_validators_count(self) -> int:
        return active_validators_count(self=self)

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
        operator=None,
        account: Optional[LocalAccount] = None,
    ) -> HexBytes:
        """Joins as a validator. Deploys a ValidatorWallet with msg.sender
        as owner and `operator` (defaults to owner) as operator."""
        return validator_join(
            self=self, amount=amount, operator=operator, account=account
        )

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
        """Rotates the operator for an existing ValidatorWallet."""
        return set_operator(
            self=self, validator=validator, operator=operator, account=account
        )

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
