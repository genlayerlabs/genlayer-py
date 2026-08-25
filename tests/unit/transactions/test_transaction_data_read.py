"""The SDK picks the transaction read the chain's own ABI offers.

getTransactionData(txId, timestamp) was withdrawn by the resolution-kernel
train in favour of getStoredTransactionData(txId). Chains upgrade
independently, so the SDK detects rather than assumes.
"""

from types import SimpleNamespace

from genlayer_py.transactions.actions import _read_transaction_data


STORED_ABI = [{"type": "function", "name": "getStoredTransactionData"}]
LEGACY_ABI = [{"type": "function", "name": "getTransactionData"}]
TX_HASH = "0x" + "ab" * 32


class _ContractStub:
    def __init__(self, record):
        self._record = record
        self.calls = []
        self.functions = self

    def getStoredTransactionData(self, tx_id):
        self.calls.append(("getStoredTransactionData", (tx_id,)))
        return SimpleNamespace(call=lambda: self._record)

    def getTransactionData(self, tx_id, timestamp):
        self.calls.append(("getTransactionData", (tx_id, timestamp)))
        return SimpleNamespace(call=lambda: self._record)


def test_prefers_the_stored_read_when_the_chain_offers_it():
    contract = _ContractStub(("record",))

    result = _read_transaction_data(contract, STORED_ABI, TX_HASH)

    assert result == ("record",)
    assert contract.calls == [("getStoredTransactionData", (TX_HASH,))]


def test_falls_back_to_the_legacy_read_on_a_chain_without_it():
    contract = _ContractStub(("record",))

    result = _read_transaction_data(contract, LEGACY_ABI, TX_HASH)

    assert result == ("record",)
    name, args = contract.calls[0]
    assert name == "getTransactionData"
    # The legacy read takes a caller-supplied clock as its second argument.
    assert args[0] == TX_HASH
    assert isinstance(args[1], int)


def test_tolerates_non_dict_abi_entries():
    contract = _ContractStub(("record",))

    result = _read_transaction_data(contract, ["not-a-dict"] + STORED_ABI, TX_HASH)

    assert result == ("record",)
    assert contract.calls[0][0] == "getStoredTransactionData"
