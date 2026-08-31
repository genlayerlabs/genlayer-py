# GenLayerPY



## About

GenLayerPY SDK is a python library designed for developers building decentralized applications (Dapps) on the GenLayer protocol. This SDK provides a comprehensive set of tools to interact with the GenLayer network, including client creation, transaction handling, event subscriptions, and more, all while leveraging the power of web3.py as the underlying blockchain client.

## Prerequisites

Before installing GenLayerPY SDK, ensure you have the following prerequisites installed:

- Python (>=3.12)


## ️ Installation and Usage

To install the GenLayerPY SDK, use the following command:
```bash
$ pip install genlayer-py
```

SDK releases follow their corresponding GenLayer protocol release. This
release targets the current resolution-kernel train; use the matching older SDK
release when connecting to an older deployment.

Here’s how to initialize the client and connect to the GenLayer Simulator:

### Reading a Transaction
```python
from genlayer_py import create_client
from genlayer_py.chains import localnet

client = create_client(
    chain=localnet,
)

transaction_hash = "0x..."

transaction = client.get_transaction(hash=transaction_hash)

```

### Waiting for Transaction Receipt
```python
from genlayer_py import create_client
from genlayer_py.chains import localnet

client = create_client(chain=localnet)

# Get simplified receipt (default - removes binary data, keeps execution results)
receipt = client.wait_for_transaction_receipt(
    transaction_hash="0x...",
    wait_until="finalized",
    full_transaction=False  # Default - simplified for readability
)

# Get complete receipt with all fields
full_receipt = client.wait_for_transaction_receipt(
    transaction_hash="0x...",
    wait_until="finalized",
    full_transaction=True  # Complete receipt with all internal data
)
```

### Reading a contract
```python
from genlayer_py import create_client
from genlayer_py.chains import localnet

client = create_client(
    chain=localnet,
)

result = client.read_contract(
    address=contract_address,
    function_name='get_complete_storage',
    args=[],
    state_status='accepted'
)
```

### Writing a transaction
```python
from genlayer_py.chains import localnet
from genlayer_py import create_client, create_account

client = create_client(
    chain=localnet,
)

account = create_account()

transaction_hash = client.write_contract(
    account=account,
    transaction=transaction,
    address=contract_address,
    function_name='account',
    args=['new_storage'],
    value=0, // value is optional, if you want to send some native token to the contract
)
receipt = client.wait_for_transaction_receipt(
    hash=transaction_hash,
    wait_until="finalized",
    full_transaction=False  // False by default - returns simplified receipt for better readability
)
```

### Fee presets for transactions

Apps can build a trusted fee preset once they know the transaction shape, then
submit the same preset with the transaction. The user may still override these
values in wallet or app UI before signing.

```python
estimate = client.estimate_transaction_fees(
    {
        "leaderTimeunitsAllocation": 100,
        "validatorTimeunitsAllocation": 200,
    }
)

tx_hash = client.write_contract(
    account=account,
    address=contract_address,
    function_name="update_storage",
    args=["new_storage"],
    fees={
        "distribution": estimate["distribution"],
        "feeValue": estimate["feeValue"],
    },
)
```

When `rotations` is omitted, estimates fund
`chain.default_consensus_max_rotations` for the initial round and every enabled
appeal round. Pass an explicit list, including `[0]`, when the application wants
to fund a different number of rotations.

If `fees["distribution"]` is provided without `feeValue`, the SDK derives the
fee deposit from FeeManager on network backends, or from `sim_getFeeConfig` on
Studio. Use `messageAllocations` with `estimate_transaction_fees` for
transactions that can emit funded messages. For method-specific message
budgets, derive the same call key GenVM reports in fee accounting:

```python
from genlayer_py.transactions import (
    MessageType,
    derive_external_message_call_key,
    derive_internal_message_call_key,
    encode_external_message_fee_params,
    encode_internal_message_fee_params,
)

estimate = client.estimate_transaction_fees(
    {
        "messageAllocations": [
            {
                "messageType": MessageType.Internal,
                "onAcceptance": True,
                "recipient": contract_address,
                "callKey": derive_internal_message_call_key("update_storage"),
                "budget": 55,
                "feeParams": encode_internal_message_fee_params(),
            },
            {
                "messageType": MessageType.External,
                "onAcceptance": False,
                "recipient": "0x3333333333333333333333333333333333333333",
                "callKey": derive_external_message_call_key("0xaabbccdd"),
                "budget": 210_000,
                "feeParams": encode_external_message_fee_params(
                    {"gasLimit": 21_000, "maxGasPrice": 10}
                ),
            },
        ],
    }
)
```

For a concrete Studio/localnet write, use the one-call helper. The SDK sends an
initial fee budget to `sim_estimateTransactionFees`; Studio simulates the write
without committing state and returns the authoritative recommended preset.

```python
recommended = client.estimate_transaction_fees_for_write(
    account=account,
    address=contract_address,
    function_name="update_storage",
    args=["new_storage"],
)

tx_hash = client.write_contract(
    account=account,
    address=contract_address,
    function_name="update_storage",
    args=["new_storage"],
    fees={
        "distribution": recommended["distribution"],
        "messageAllocations": recommended.get("messageAllocations"),
        "feeValue": recommended["feeValue"],
    },
)
```

For tests or tools that need to inspect the raw simulation, use the explicit
two-step flow. `simulate_write_contract` uses `sim_call`; the returned receipt
includes the fee accounting report produced by GenVM and Studio:

```python
simulation = client.simulate_write_contract(
    account=account,
    address=contract_address,
    function_name="update_storage",
    args=["new_storage"],
    fees={
        "distribution": estimate["distribution"],
        "feeValue": estimate["feeValue"],
    },
)

print(simulation["genvm_result"]["fee_accounting"])
```

To reuse a representative Studio simulation as the trusted preset source, pass
the simulation result into `estimate_transaction_fees_from_simulation`:

```python
estimate = client.estimate_transaction_fees_from_simulation(
    {
        "simulation": simulation,
    }
)

tx_hash = client.write_contract(
    account=account,
    address=contract_address,
    function_name="update_storage",
    args=["new_storage"],
    fees={
        "distribution": estimate["distribution"],
        "messageAllocations": estimate.get("messageAllocations"),
        "feeValue": estimate["feeValue"],
    },
)
```

For transactions that are already submitted, use the fee-management helpers:

```python
client.top_up_fees(
    transaction_id=tx_hash,
    value=1_100,
    distribution={
        "leaderTimeunitsAllocation": 100,
        "validatorTimeunitsAllocation": 200,
        "rotations": [0],
    },
)

quote = client.get_appeal_quote(tx_hash)
if client.can_appeal(tx_hash, expected_decision_id=quote["decision_id"]):
    client.top_up_and_submit_appeal(
        transaction_id=tx_hash,
        expected_decision_id=quote["decision_id"],
        value=quote["total"],
        distribution={
            "appealRounds": 1,
            "rotations": [0, 0],
        },
    )
```

`top_up_fees` returns the backend RPC hash. On network backends this is the EVM
transaction hash; on Studio/localnet it is the target GenLayer transaction id.
Appeal commands are guarded by the quoted decision id so a stale request cannot
bind to a newer decision. If the id and value are omitted, the SDK refreshes
this lightweight quote automatically. This applies to deployed Consensus.
Current Studio uses its native decision-free appeal methods: pass ``value``
explicitly and omit ``expected_decision_id``.

### Checking execution results

A transaction can be finalized by consensus but still have a failed execution. Always check `tx_execution_result` before reading contract state:

```python
from genlayer_py import create_client, create_account
from genlayer_py.chains import testnet_bradbury
from genlayer_py.types import ExecutionResult

client = create_client(chain=testnet_bradbury, account=create_account())

receipt = client.wait_for_transaction_receipt(
    transaction_hash=tx_hash,
    wait_until="finalized",
)

if receipt.get("tx_execution_result_name") == ExecutionResult.FINISHED_WITH_RETURN.value:
    # Execution succeeded — safe to read state
    result = client.read_contract(
        address=contract_address,
        function_name="get_storage",
        args=[],
    )
elif receipt.get("tx_execution_result_name") == ExecutionResult.FINISHED_WITH_ERROR.value:
    # Execution failed — contract state was not modified
    raise RuntimeError("Contract execution failed")
else:
    # NOT_VOTED — execution hasn't completed
    print("Execution result not yet available")
```

### Fetching emitted messages and triggered transactions

Transactions can emit messages to other contracts. These messages create new child transactions when processed:

```python
tx = client.get_transaction(transaction_hash=tx_hash)

# The default lifecycle is derived only from stored chain state.
print(tx["lifecycle"])
# {"state": "processing", "phase": "revealing"}
# {"state": "decided", "outcome": "accepted"}

# Protocol projection/action details are available only through the explicit
# advanced API.
raw_lifecycle = client.get_transaction_lifecycle(transaction_hash=tx_hash)
print(raw_lifecycle["stored_status_name"])
print(raw_lifecycle["projected_status_name"])
print(raw_lifecycle["resolution_action_name"])
print(raw_lifecycle["resolution_source_name"])
# `resolution_action_name == "Finalize"` is the authoritative readiness verdict.
# On current Studio without the advanced lifecycle RPC, only stored status is
# provable; projection repeats it and resolution/decision fields stay inactive.

# The train stores the execution hash, not the old receipt bytes.
print(tx["tx_execution_hash"])
# `tx_receipt` remains present but is `None` when the
# protocol cannot supply the old bytes.

# Messages emitted by the contract during execution
print(tx["messages"])
# [{"messageType": 1, "recipient": "0x...", "value": 0, "data": "0x...", "onAcceptance": True, "saltNonce": 0}, ...]

# Child transaction IDs created from those messages (separate call)
child_tx_ids = client.get_triggered_transaction_ids(transaction_hash=tx_hash)
print(child_tx_ids)
# ["0xabc...", "0xdef..."]
```

### Active and joined validators

The active set contains only validators currently eligible for protocol
duties. The joined registry is broader and can include validators that are not
yet selectable, are under-staked, or are otherwise unavailable.

```python
active = client.active_validators()
active_count = client.active_validators_count()

joined = client.joined_validators()
joined_count = client.joined_validators_count()
```

### Debugging transaction execution

Use `debug_trace_transaction` to inspect the full execution trace of a transaction, including return data, errors, and GenVM logs:

```python
trace = client.debug_trace_transaction(
    transaction_hash=tx_hash,
    round=0,  # optional, defaults to 0
)

print(trace["result_code"])   # 0=success, 1=user error, 2=VM error
print(trace["return_data"])   # hex-encoded contract return data
print(trace["stderr"])        # standard error output
print(trace["genvm_log"])     # detailed GenVM execution logs
```

## Key Features

* **Client Creation**: Easily create and configure a client to connect to GenLayer’s network.
* **Transaction Handling**: Send and manage transactions on the GenLayer network.
* **Gas Estimation**: Estimate gas fees for executing transactions on GenLayer.

_* under development_


## Documentation

For detailed information on how to use GenLayerPY SDK, please refer to our [documentation](https://docs.genlayer.com/api-references/genlayer-py).


## Contributing

We welcome contributions to GenLayerPY SDK! Whether it's new features, improved infrastructure, or better documentation, your input is valuable. Please read our [CONTRIBUTING](https://github.com/genlayerlabs/genlayer-py/blob/main/CONTRIBUTING.md) guide for guidelines on how to submit your contributions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
