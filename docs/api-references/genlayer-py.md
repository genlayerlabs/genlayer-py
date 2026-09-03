# GenLayerPY SDK API Reference

Auto-generated from source docstrings.

## Client Methods

Client for interacting with the GenLayer network.

Provides methods for deploying and calling intelligent contracts,
managing transactions, and staking operations.

### fund_account

Funds an account with test tokens. Localnet only.

```python
client.fund_account(address: Union, amount: int)
```

**Parameters:**

- **address** (`Union`) — required
- **amount** (`int`) — required

**Returns:** `HexBytes`

---

### get_current_nonce

Returns the current nonce (transaction count) for an account.

```python
client.get_current_nonce(address: Union = None, block_identifier: Union = None)
```

**Parameters:**

- **address** (`Union`) — optional = None
- **block_identifier** (`Union`) — optional = None

**Returns:** `Nonce`

---

### initialize_consensus_smart_contract

Initializes the consensus contract configuration from the network.

```python
client.initialize_consensus_smart_contract(force_reset: bool = False)
```

**Parameters:**

- **force_reset** (`bool`) — optional = False

**Returns:** `None`

---

### read_contract

Executes a read-only contract call without modifying state.

```python
client.read_contract(address: Union, function_name: str, args: Union = None, kwargs: Union = None, account: Union = None, raw_return: bool = False, transaction_hash_variant: TransactionHashVariant = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>, sim_config: Union = None)
```

**Parameters:**

- **address** (`Union`) — required
- **function_name** (`str`) — required
- **args** (`Union`) — optional = None
- **kwargs** (`Union`) — optional = None
- **account** (`Union`) — optional = None
- **raw_return** (`bool`) — optional = False
- **transaction_hash_variant** (`TransactionHashVariant`) — optional = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>
- **sim_config** (`Union`) — optional = None

---

### write_contract

Executes a state-modifying function on a contract through consensus. Returns the transaction hash.

```python
client.write_contract(address: Union, function_name: str, account: Union = None, consensus_max_rotations: Union = None, value: int = 0, leader_only: bool = False, args: Union = None, kwargs: Union = None, sim_config: Union = None)
```

**Parameters:**

- **address** (`Union`) — required
- **function_name** (`str`) — required
- **account** (`Union`) — optional = None
- **consensus_max_rotations** (`Union`) — optional = None
- **value** (`int`) — optional = 0
- **leader_only** (`bool`) — optional = False
- **args** (`Union`) — optional = None
- **kwargs** (`Union`) — optional = None
- **sim_config** (`Union`) — optional = None

---

### simulate_write_contract

Simulates a state-modifying contract call without executing on-chain. Localnet only.

```python
client.simulate_write_contract(address: Union, function_name: str, account: Union = None, args: Union = None, kwargs: Union = None, sim_config: Union = None, transaction_hash_variant: TransactionHashVariant = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>)
```

**Parameters:**

- **address** (`Union`) — required
- **function_name** (`str`) — required
- **account** (`Union`) — optional = None
- **args** (`Union`) — optional = None
- **kwargs** (`Union`) — optional = None
- **sim_config** (`Union`) — optional = None
- **transaction_hash_variant** (`TransactionHashVariant`) — optional = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>

---

### deploy_contract

Deploys a new intelligent contract to GenLayer. Returns the transaction hash.

```python
client.deploy_contract(code: Union, account: Union = None, args: Union = None, kwargs: Union = None, consensus_max_rotations: Union = None, leader_only: bool = False, sim_config: Union = None)
```

**Parameters:**

- **code** (`Union`) — required
- **account** (`Union`) — optional = None
- **args** (`Union`) — optional = None
- **kwargs** (`Union`) — optional = None
- **consensus_max_rotations** (`Union`) — optional = None
- **leader_only** (`bool`) — optional = False
- **sim_config** (`Union`) — optional = None

---

### get_contract_schema

Gets the schema (methods and constructor) of a deployed contract. Localnet only.

```python
client.get_contract_schema(address: Union)
```

**Parameters:**

- **address** (`Union`) — required

**Returns:** `ContractSchema`

---

### get_contract_schema_for_code

Generates a schema for contract code without deploying it. Localnet only.

```python
client.get_contract_schema_for_code(contract_code: AnyStr)
```

**Parameters:**

- **contract_code** (`AnyStr`) — required

**Returns:** `ContractSchema`

---

### appeal_transaction

Appeals a consensus transaction to trigger a new round of validation.

```python
client.appeal_transaction(transaction_id: HexStr, account: Union = None, value: int = 0)
```

**Parameters:**

- **transaction_id** (`HexStr`) — required
- **account** (`Union`) — optional = None
- **value** (`int`) — optional = 0

---

### wait_for_transaction_receipt

Polls for a stored decision by default, or for stored finalization.

```python
client.wait_for_transaction_receipt(transaction_hash: Union, wait_until: Literal = "decided", interval: int = 3000, retries: int = 10, full_transaction: bool = False)
```

**Parameters:**

- **transaction_hash** (`Union`) — required
- **wait_until** (`Literal["decided", "finalized"]`) — optional = "decided"
- **interval** (`int`) — optional = 3000
- **retries** (`int`) — optional = 10
- **full_transaction** (`bool`) — optional = False

**Returns:** `GenLayerTransaction`

---

### wait_for_decision

Polls until the stored transaction state is decided, finalized, or canceled.

```python
client.wait_for_decision(transaction_hash: Union, interval: int = 3000, retries: int = 10, full_transaction: bool = False)
```

---

### wait_for_finalization

Polls until the stored transaction state is finalized.

```python
client.wait_for_finalization(transaction_hash: Union, interval: int = 3000, retries: int = 10, full_transaction: bool = False)
```

---

### get_transaction

Fetches transaction data with a stable lifecycle derived from stored chain
state, plus execution result and consensus details.

```python
client.get_transaction(transaction_hash: Union)
```

**Parameters:**

- **transaction_hash** (`Union`) — required

**Returns:** `GenLayerTransaction`

`lifecycle` is discriminated by its `state` field: processing carries `phase`,
decided carries `outcome`, finalized may carry an outcome when it is actually
known, and canceled has no extra branch data.

The train exposes the authoritative `tx_execution_hash`. It does not retain the
old receipt bytes, so the legacy `tx_receipt` field is `None`.

---

### get_transaction_lifecycle

Returns the advanced raw protocol view: stored status, projected status,
resolution action/source, decision identity, and evaluation time. A `FINALIZE`
action is the authoritative finalization-readiness verdict.

```python
client.get_transaction_lifecycle(transaction_hash: Union)
```

---

### get_triggered_transaction_ids

Returns transaction IDs of child transactions created from emitted messages.

```python
client.get_triggered_transaction_ids(transaction_hash: Union)
```

**Parameters:**

- **transaction_hash** (`Union`) — required

**Returns:** `list`

---

### debug_trace_transaction

Fetches the full execution trace including return data, stdout, stderr, and GenVM logs.

```python
client.debug_trace_transaction(transaction_hash: Union, round: int = 0)
```

**Parameters:**

- **transaction_hash** (`Union`) — required
- **round** (`int`) — optional = 0

**Returns:** `dict`

---

## Types and Enums

### TransactionResult

Consensus voting result across validators.

```python
TransactionResult.IDLE = "IDLE"
TransactionResult.AGREE = "AGREE"
TransactionResult.DISAGREE = "DISAGREE"
TransactionResult.TIMEOUT = "TIMEOUT"
TransactionResult.DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"
TransactionResult.NO_MAJORITY = "NO_MAJORITY"
TransactionResult.MAJORITY_AGREE = "MAJORITY_AGREE"
TransactionResult.MAJORITY_DISAGREE = "MAJORITY_DISAGREE"
```

---

### ExecutionResult

Result of contract execution by the GenVM.

```python
ExecutionResult.NOT_VOTED = "NOT_VOTED"
ExecutionResult.FINISHED_WITH_RETURN = "FINISHED_WITH_RETURN"
ExecutionResult.FINISHED_WITH_ERROR = "FINISHED_WITH_ERROR"
ExecutionResult.TIMEOUT = "TIMEOUT"
ExecutionResult.NONDET_DISAGREE = "NONDET_DISAGREE"
ExecutionResult.DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"
```

---

### VoteType

Validator execution vote recorded for a consensus round.

```python
VoteType.NOT_VOTED = "NOT_VOTED"
VoteType.FINISHED_WITH_RETURN = "FINISHED_WITH_RETURN"
VoteType.FINISHED_WITH_ERROR = "FINISHED_WITH_ERROR"
VoteType.TIMEOUT = "TIMEOUT"
VoteType.NONDET_DISAGREE = "NONDET_DISAGREE"
VoteType.DETERMINISTIC_VIOLATION = "DETERMINISTIC_VIOLATION"
```

---
