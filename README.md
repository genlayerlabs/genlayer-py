# GenLayerPY

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/license/mit/)
[![Discord](https://dcbadge.vercel.app/api/server/8Jm4v89VAu?compact=true&style=flat)](https://discord.gg/VpfmXEMN66)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/yeagerai.svg?style=social&label=Follow%20%40GenLayer)](https://x.com/GenLayer)


## About

GenLayerPY SDK is a python library designed for developers building decentralized applications (Dapps) on the GenLayer protocol. This SDK provides a comprehensive set of tools to interact with the GenLayer network, including client creation, transaction handling, event subscriptions, and more, all while leveraging the power of web3.py as the underlying blockchain client.

## Prerequisites

Before installing GenLayerPY SDK, ensure you have the following prerequisites installed:

- Python (>=3.8)


## 🛠️ Installation and Usage

To install the GenLayerPY SDK, use the following command:
```bash
$ pip install genlayer-py
```

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
    status=TransactionStatus.FINALIZED // or ACCEPTED
)
```


## 🚀 Key Features

* **Client Creation**: Easily create and configure a client to connect to GenLayer’s network.
* **Transaction Handling**: Send and manage transactions on the GenLayer network.
* **Gas Estimation***: Estimate gas fees for executing transactions on GenLayer.

_* under development_


## 📖 Documentation

For detailed information on how to use GenLayerPY SDK, please refer to our [documentation](https://docs.genlayer.com/api-references/genlayer-py).


## Contributing

We welcome contributions to GenLayerPY SDK! Whether it's new features, improved infrastructure, or better documentation, your input is valuable. Please read our [CONTRIBUTING](https://github.com/yeagerai/genlayer-py/blob/main/CONTRIBUTING.md) guide for guidelines on how to submit your contributions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
