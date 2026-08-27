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

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | yes |  |
| amount | `int` | yes |  |

**Returns:** `HexBytes`

---

### get_current_nonce

Returns the current nonce (transaction count) for an account.

```python
client.get_current_nonce(address: Union = None, block_identifier: Union = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | no | None |
| block_identifier | `Union` | no | None |

**Returns:** `Nonce`

---

### initialize_consensus_smart_contract

Initializes the consensus contract configuration from the network.

```python
client.initialize_consensus_smart_contract(force_reset: bool = False)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| force_reset | `bool` | no | False |

**Returns:** `None`

---

### read_contract

Executes a read-only contract call without modifying state.

```python
client.read_contract(address: Union, function_name: str, args: Optional = None, kwargs: Optional = None, account: Optional = None, raw_return: bool = False, transaction_hash_variant: TransactionHashVariant = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>, sim_config: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | yes |  |
| function_name | `str` | yes |  |
| args | `Optional` | no | None |
| kwargs | `Optional` | no | None |
| account | `Optional` | no | None |
| raw_return | `bool` | no | False |
| transaction_hash_variant | `TransactionHashVariant` | no | <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'> |
| sim_config | `Optional` | no | None |

---

### write_contract

Executes a state-modifying function on a contract through consensus. Returns the transaction hash.

```python
client.write_contract(address: Union, function_name: str, account: Optional = None, consensus_max_rotations: Optional = None, value: int = 0, leader_only: bool = False, args: Optional = None, kwargs: Optional = None, sim_config: Optional = None, valid_until: Optional = None, fees: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | yes |  |
| function_name | `str` | yes |  |
| account | `Optional` | no | None |
| consensus_max_rotations | `Optional` | no | None |
| value | `int` | no | 0 |
| leader_only | `bool` | no | False |
| args | `Optional` | no | None |
| kwargs | `Optional` | no | None |
| sim_config | `Optional` | no | None |
| valid_until | `Optional` | no | None |
| fees | `Optional` | no | None |

---

### simulate_write_contract

Simulates a state-modifying contract call without executing on-chain. Localnet only.

```python
client.simulate_write_contract(address: Union, function_name: str, account: Optional = None, args: Optional = None, kwargs: Optional = None, value: int = 0, leader_only: bool = False, fees: Optional = None, sim_config: Optional = None, transaction_hash_variant: TransactionHashVariant = <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'>)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | yes |  |
| function_name | `str` | yes |  |
| account | `Optional` | no | None |
| args | `Optional` | no | None |
| kwargs | `Optional` | no | None |
| value | `int` | no | 0 |
| leader_only | `bool` | no | False |
| fees | `Optional` | no | None |
| sim_config | `Optional` | no | None |
| transaction_hash_variant | `TransactionHashVariant` | no | <TransactionHashVariant.LATEST_NONFINAL: 'latest-nonfinal'> |

---

### deploy_contract

Deploys a new intelligent contract to GenLayer. Returns the transaction hash.

```python
client.deploy_contract(code: Union, account: Optional = None, args: Optional = None, kwargs: Optional = None, consensus_max_rotations: Optional = None, leader_only: bool = False, sim_config: Optional = None, valid_until: Optional = None, fees: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| code | `Union` | yes |  |
| account | `Optional` | no | None |
| args | `Optional` | no | None |
| kwargs | `Optional` | no | None |
| consensus_max_rotations | `Optional` | no | None |
| leader_only | `bool` | no | False |
| sim_config | `Optional` | no | None |
| valid_until | `Optional` | no | None |
| fees | `Optional` | no | None |

---

### get_contract_schema

Gets the schema (methods and constructor) of a deployed contract. Localnet only.

```python
client.get_contract_schema(address: Union)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| address | `Union` | yes |  |

**Returns:** `ContractSchema`

---

### get_contract_schema_for_code

Generates a schema for contract code without deploying it. Localnet only.

```python
client.get_contract_schema_for_code(contract_code: AnyStr)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| contract_code | `AnyStr` | yes |  |

**Returns:** `ContractSchema`

---

### appeal_transaction

Appeals a consensus transaction to trigger a new round of validation.
Returns the original transaction_id (appeals operate on the same tx).
Missing decision/value inputs are filled from the latest appeal quote.
Studio chains predate that quote: they take the pre-train call shape,
reject ``expected_decision_id``, and require an explicit ``value``.

```python
client.appeal_transaction(transaction_id: HexStr, account: Optional = None, value: Optional = None, expected_decision_id: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |
| account | `Optional` | no | None |
| value | `Optional` | no | None |
| expected_decision_id | `Optional` | no | None |

---

### top_up_fees

Deposits additional fee budget for an existing consensus transaction.

```python
client.top_up_fees(transaction_id: HexStr, distribution: FeesDistributionInput, value: int, account: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |
| distribution | `FeesDistributionInput` | yes |  |
| value | `int` | yes |  |
| account | `Optional` | no | None |

**Returns:** `HexStr`

---

### top_up_and_submit_appeal

Deposits appeal funding and submits the exact active decision.

When ``expected_decision_id`` or ``value`` is omitted, the SDK obtains
both from the lightweight consensus appeal quote. Studio chains predate
that quote: they take the pre-train call shape, reject
``expected_decision_id``, and require an explicit ``value``.

```python
client.top_up_and_submit_appeal(transaction_id: HexStr, distribution: FeesDistributionInput, account: Optional = None, value: Optional = None, expected_decision_id: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |
| distribution | `FeesDistributionInput` | yes |  |
| account | `Optional` | no | None |
| value | `Optional` | no | None |
| expected_decision_id | `Optional` | no | None |

**Returns:** `HexStr`

---

### can_appeal

Checks whether the exact active decision can be appealed.

```python
client.can_appeal(transaction_id: HexStr, expected_decision_id: Optional = None)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |
| expected_decision_id | `Optional` | no | None |

**Returns:** `bool`

---

### get_appeal_quote

Returns the latest decision id, appeal charges, and deadline.
Not available on studio chains, whose consensus predates the quote.

```python
client.get_appeal_quote(transaction_id: HexStr)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |

**Returns:** `Dict`

---

### get_appeal_charge

Returns the full appeal payment (bond plus induced-work funding).
Not available on studio chains, whose consensus predates the quote.

```python
client.get_appeal_charge(transaction_id: HexStr)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |

**Returns:** `int`

---

### get_min_appeal_bond

Deprecated alias for :meth:`get_appeal_charge`.

```python
client.get_min_appeal_bond(transaction_id: HexStr)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_id | `HexStr` | yes |  |

**Returns:** `int`

---

### wait_for_transaction_receipt

Polls until a transaction reaches the specified status. Returns the transaction receipt.

```python
client.wait_for_transaction_receipt(transaction_hash: Union, status: Optional = None, wait_until: Optional = None, interval: int = 3000, retries: int = 10, full_transaction: bool = False)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_hash | `Union` | yes |  |
| status | `Optional` | no | None |
| wait_until | `Optional` | no | None |
| interval | `int` | no | 3000 |
| retries | `int` | no | 10 |
| full_transaction | `bool` | no | False |

**Returns:** `GenLayerTransaction`

---

### get_transaction

Fetches projected/stored status, resolution/finalization readiness,
execution result, and consensus details.

``status`` is projected while ``stored_status`` is the exact chain
record. Finalization readiness is ``resolution_action == "FINALIZE"``
together with ``can_finalize``. The train exposes
``tx_execution_hash``; legacy receipt bytes are unavailable, so
``tx_receipt`` is ``None``.

```python
client.get_transaction(transaction_hash: Union)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_hash | `Union` | yes |  |

**Returns:** `GenLayerTransaction`

---

### get_triggered_transaction_ids

Returns transaction IDs of child transactions created from emitted messages.

```python
client.get_triggered_transaction_ids(transaction_hash: Union)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_hash | `Union` | yes |  |

**Returns:** `list`

---

### debug_trace_transaction

Fetches the full execution trace including return data, stdout, stderr, and GenVM logs.

```python
client.debug_trace_transaction(transaction_hash: Union, round: int = 0)
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| transaction_hash | `Union` | yes |  |
| round | `int` | no | 0 |

**Returns:** `dict`

---

## Types and Enums

### TransactionStatus

Status of a GenLayer transaction in the consensus lifecycle.

```python
TransactionStatus.UNINITIALIZED = "UNINITIALIZED"
TransactionStatus.PENDING = "PENDING"
TransactionStatus.PROPOSING = "PROPOSING"
TransactionStatus.COMMITTING = "COMMITTING"
TransactionStatus.REVEALING = "REVEALING"
TransactionStatus.ACCEPTED = "ACCEPTED"
TransactionStatus.UNDETERMINED = "UNDETERMINED"
TransactionStatus.FINALIZED = "FINALIZED"
TransactionStatus.CANCELED = "CANCELED"
TransactionStatus.APPEAL_REVEALING = "APPEAL_REVEALING"
TransactionStatus.APPEAL_COMMITTING = "APPEAL_COMMITTING"
TransactionStatus.VALIDATORS_TIMEOUT = "VALIDATORS_TIMEOUT"
TransactionStatus.LEADER_TIMEOUT = "LEADER_TIMEOUT"
TransactionStatus.LEADER_REVEALING = "LEADER_REVEALING"
```

---

### ResolutionAction

Action projected by the transaction lifecycle resolution kernel.

```python
ResolutionAction.NO_OP = "NO_OP"
ResolutionAction.CANCEL = "CANCEL"
ResolutionAction.REPLACE_ACTOR = "REPLACE_ACTOR"
ResolutionAction.ROTATE_LEADER = "ROTATE_LEADER"
ResolutionAction.RESOLVE_APPEAL = "RESOLVE_APPEAL"
ResolutionAction.MATERIALIZE_DECISION = "MATERIALIZE_DECISION"
ResolutionAction.FINALIZE = "FINALIZE"
```

---

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
TransactionResult.MAJORITY_TIMEOUT = "MAJORITY_TIMEOUT"
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
