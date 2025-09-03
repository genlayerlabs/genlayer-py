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
    get_contract_schema,
    get_contract_schema_for_code,
    simulate_write_contract,
)
from genlayer_py.chains.actions import initialize_consensus_smart_contract
from genlayer_py.transactions.actions import (
    wait_for_transaction_receipt,
    get_transaction,
)
from genlayer_py.config import transaction_config


class GenLayerClient(Eth):
    """
    The client to interact with GenLayer Network
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
        return fund_account(self, address, amount)

    def get_current_nonce(
        self,
        address: Optional[Union[Address, ChecksumAddress, ENS]] = None,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> Nonce:
        return get_current_nonce(self, address, block_identifier)

    # Chain actions
    def initialize_consensus_smart_contract(
        self,
        force_reset: bool = False,
    ) -> None:
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
        return get_contract_schema(
            self=self,
            address=address,
        )

    def get_contract_schema_for_code(
        self,
        contract_code: AnyStr,
    ) -> ContractSchema:
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
        return get_transaction(self=self, transaction_hash=transaction_hash)

    def appeal_transaction(
        self,
        transaction_id: HexStr,
        account: Optional[LocalAccount] = None,
        value: int = 0,
    ):
        return appeal_transaction(
            self=self,
            transaction_id=transaction_id,
            account=account,
            value=value,
        )
