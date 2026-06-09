from types import SimpleNamespace
from unittest.mock import Mock

import eth_utils
from eth_abi import decode as abi_decode
from web3 import Web3

import genlayer_py.contracts.actions as contract_actions
from genlayer_py.chains import localnet
from genlayer_py.transactions.fees import (
    ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES,
    ADD_TRANSACTION_WITH_FEES_SELECTOR,
    CALL_KEY_DEPLOY,
    CALL_KEY_UNNAMED,
    CALL_KEY_WILDCARD,
    FEES_DISTRIBUTION_ABI_TYPE,
    MESSAGE_ALLOCATION_ROOT_PARENT_INDEX,
    MessageType,
    build_estimated_fees_distribution,
    calculate_local_round_fees,
    create_fees_distribution,
    derive_external_message_call_key,
    derive_internal_message_call_key,
    encode_external_message_fee_params,
    encode_internal_message_fee_params,
    extract_studio_fee_policy,
    requires_fee_deposit_calculation,
)


DEFAULT_PARENT_MESSAGE_RECEIPT_HEADROOM = 10_000


ADD_TRANSACTION_ABI_V5 = [
    {
        "type": "function",
        "name": "addTransaction",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_sender", "type": "address"},
            {"name": "_recipient", "type": "address"},
            {"name": "_numOfInitialValidators", "type": "uint256"},
            {"name": "_maxRotations", "type": "uint256"},
            {"name": "_calldata", "type": "bytes"},
        ],
        "outputs": [],
    }
]

ADD_TRANSACTION_ABI_V6 = [
    {
        "type": "function",
        "name": "addTransaction",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_sender", "type": "address"},
            {"name": "_recipient", "type": "address"},
            {"name": "_numOfInitialValidators", "type": "uint256"},
            {"name": "_maxRotations", "type": "uint256"},
            {"name": "_calldata", "type": "bytes"},
            {"name": "_validUntil", "type": "uint256"},
        ],
        "outputs": [],
    }
]

ADD_TRANSACTION_ABI_WITH_FEES = [
    {
        "type": "function",
        "name": "addTransaction",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "_params",
                "type": "tuple",
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "recipient", "type": "address"},
                    {"name": "numOfInitialValidators", "type": "uint256"},
                    {"name": "maxRotations", "type": "uint256"},
                    {"name": "validUntil", "type": "uint256"},
                    {"name": "saltNonce", "type": "uint256"},
                    {"name": "userValue", "type": "uint256"},
                    {
                        "name": "feesDistribution",
                        "type": "tuple",
                        "components": [
                            {"name": "leaderTimeunitsAllocation", "type": "uint256"},
                            {"name": "validatorTimeunitsAllocation", "type": "uint256"},
                            {"name": "appealRounds", "type": "uint256"},
                            {"name": "executionBudgetPerRound", "type": "uint256"},
                            {"name": "executionConsumed", "type": "uint256"},
                            {"name": "totalMessageFees", "type": "uint256"},
                            {"name": "rotations", "type": "uint256[]"},
                            {"name": "maxPriceGenPerTimeUnit", "type": "uint256"},
                            {"name": "storageFeeMaxGasPrice", "type": "uint256"},
                            {"name": "receiptFeeMaxGasPrice", "type": "uint256"},
                        ],
                    },
                    {"name": "txCalldata", "type": "bytes"},
                    {
                        "name": "messageAllocations",
                        "type": "tuple[]",
                        "components": [
                            {"name": "messageType", "type": "uint8"},
                            {"name": "onAcceptance", "type": "bool"},
                            {"name": "parentIndex", "type": "uint256"},
                            {"name": "recipient", "type": "address"},
                            {"name": "callKey", "type": "bytes32"},
                            {"name": "budget", "type": "uint256"},
                            {"name": "feeParams", "type": "bytes"},
                        ],
                    },
                ],
            },
        ],
        "outputs": [],
    }
]

SENDER = "0x1111111111111111111111111111111111111111"
RECIPIENT = "0x2222222222222222222222222222222222222222"
TX_ID = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_encode_internal_message_fee_params_uses_consensus_tuple_shape():
    encoded = encode_internal_message_fee_params(
        {
            "leaderTimeunitsAllocation": 5,
            "validatorTimeunitsAllocation": 10,
            "appealRounds": 1,
            "executionBudgetPerRound": 20,
            "rotations": [2, 3],
        }
    )

    decoded = abi_decode(
        ("(uint256,uint256,uint256,uint256,uint256[])",),
        Web3.to_bytes(hexstr=encoded),
    )[0]
    assert decoded == (5, 10, 1, 20, (2, 3))


def test_derive_internal_message_call_key_for_short_method_name():
    assert derive_internal_message_call_key("update_storage") == (
        "0x7570646174655f73746f72616765000000000000000000000000000000000000"
    )


def test_derive_internal_message_call_key_hashes_exact_32_byte_method_name():
    method_name = "a" * 32
    expected = bytearray(eth_utils.keccak(text=method_name))
    expected[-1] |= 1
    assert derive_internal_message_call_key(method_name) == "0x" + bytes(expected).hex()


def test_derive_message_call_key_constants_for_deploy_and_unnamed():
    assert CALL_KEY_DEPLOY == "0x" + "00" * 32
    assert CALL_KEY_UNNAMED == "0x" + "00" * 32
    assert derive_internal_message_call_key("") == CALL_KEY_UNNAMED


def test_derive_external_message_call_key_uses_selector_prefix():
    assert derive_external_message_call_key("0xaabbccdd0102") == (
        "0xaabbccdd00000000000000000000000000000000000000000000000000000000"
    )


def test_derive_external_message_call_key_keeps_unnamed_for_short_calldata():
    assert derive_external_message_call_key("0xaabbcc") == CALL_KEY_UNNAMED


def test_encode_external_message_fee_params_uses_consensus_tuple_shape():
    encoded = encode_external_message_fee_params(
        {
            "gasLimit": 21_000,
            "maxGasPrice": 10,
        }
    )

    decoded = abi_decode(
        ("(uint256,uint256)",),
        Web3.to_bytes(hexstr=encoded),
    )[0]
    assert decoded == (21_000, 10)


def test_encode_top_up_fees_uses_consensus_tuple_shape():
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)

    encoded = contract_actions._encode_fee_management_data(
        self=client,
        function_name="topUpFees",
        transaction_id=TX_ID,
        distribution={
            "leaderTimeunitsAllocation": 100,
            "validatorTimeunitsAllocation": 200,
            "appealRounds": 1,
            "executionBudgetPerRound": 500_000,
            "totalMessageFees": 30,
            "rotations": [0, 2],
            "maxPriceGenPerTimeUnit": 12,
            "storageFeeMaxGasPrice": 24,
            "receiptFeeMaxGasPrice": 36,
        },
    )

    selector = eth_utils.keccak(
        text=f"topUpFees(bytes32,{FEES_DISTRIBUTION_ABI_TYPE})"
    )[:4].hex()
    assert encoded.startswith(f"0x{selector}")
    decoded_tx_id, distribution = abi_decode(
        ("bytes32", FEES_DISTRIBUTION_ABI_TYPE),
        Web3.to_bytes(hexstr=encoded[10:]),
    )
    assert decoded_tx_id == Web3.to_bytes(hexstr=TX_ID)
    assert distribution == (100, 200, 1, 500_000, 0, 30, (0, 2), 12, 24, 36)


def test_top_up_fees_sends_consensus_call(monkeypatch):
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)
    captured = {}

    def fake_send_consensus_call(**kwargs):
        captured.update(kwargs)
        return "0xevmtx"

    monkeypatch.setattr(
        contract_actions,
        "_send_consensus_call",
        fake_send_consensus_call,
    )

    result = contract_actions.top_up_fees(
        self=client,
        transaction_id=TX_ID,
        value=999,
        distribution={"totalMessageFees": 30},
    )

    assert result == "0xevmtx"
    assert captured["sender_account"] is client.local_account
    assert captured["value"] == 999
    assert captured["operation_name"] == "Top up fees"
    assert captured["encoded_data"].startswith("0x")


def test_top_up_and_submit_appeal_sends_consensus_call_and_returns_tx_id(monkeypatch):
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)
    captured = {}

    def fake_send_consensus_call(**kwargs):
        captured.update(kwargs)
        return "0xevmtx"

    monkeypatch.setattr(
        contract_actions,
        "_send_consensus_call",
        fake_send_consensus_call,
    )

    result = contract_actions.top_up_and_submit_appeal(
        self=client,
        transaction_id=TX_ID,
        value=1234,
        distribution={"appealRounds": 1, "rotations": [0, 1]},
    )

    selector = eth_utils.keccak(
        text=f"topUpAndSubmitAppeal(bytes32,{FEES_DISTRIBUTION_ABI_TYPE})"
    )[:4].hex()
    assert result == TX_ID
    assert captured["value"] == 1234
    assert captured["operation_name"] == "Top up and submit appeal"
    assert captured["encoded_data"].startswith(f"0x{selector}")


def test_send_consensus_call_returns_localnet_rpc_hash_without_waiting(monkeypatch):
    wait_for_transaction_receipt = Mock()
    sign_transaction = Mock(
        return_value=SimpleNamespace(raw_transaction=b"\x12\x34")
    )
    client = SimpleNamespace(
        chain=SimpleNamespace(
            id=localnet.id,
            consensus_main_contract={
                "address": "0x3333333333333333333333333333333333333333",
            },
        ),
        provider=SimpleNamespace(
            make_request=Mock(return_value={"result": TX_ID})
        ),
        w3=SimpleNamespace(
            to_hex=Mock(return_value="0xsigned"),
            eth=SimpleNamespace(wait_for_transaction_receipt=wait_for_transaction_receipt),
        ),
    )
    account = SimpleNamespace(address=SENDER, sign_transaction=sign_transaction)

    monkeypatch.setattr(
        contract_actions,
        "_prepare_transaction",
        Mock(return_value={"from": SENDER}),
    )

    result = contract_actions._send_consensus_call(
        self=client,
        encoded_data="0x1234",
        sender_account=account,
        value=1,
        operation_name="Top up fees",
    )

    assert result == TX_ID
    wait_for_transaction_receipt.assert_not_called()


def _make_client(add_transaction_abi):
    chain = SimpleNamespace(
        id=61999,
        consensus_main_contract={
            "address": "0x3333333333333333333333333333333333333333",
            "abi": add_transaction_abi,
        },
        default_number_of_initial_validators=5,
        default_consensus_max_rotations=3,
    )
    local_account = SimpleNamespace(address=SENDER)
    return SimpleNamespace(
        chain=chain,
        local_account=local_account,
        w3=Web3(),
    )


def test_simulate_write_contract_passes_fee_policy_and_value_to_sim_call():
    make_request = Mock(
        return_value={
            "result": {
                "data": "0x",
                "genvm_result": {"fee_accounting": {"status": "active"}},
            }
        }
    )
    client = SimpleNamespace(
        chain=SimpleNamespace(id=localnet.id),
        local_account=SimpleNamespace(address=SENDER),
        provider=SimpleNamespace(make_request=make_request),
    )

    result = contract_actions.simulate_write_contract(
        self=client,
        address=RECIPIENT,
        function_name="update_storage",
        args=["simulated"],
        value=12,
        leader_only=True,
        fees={
            "feeValue": 123,
            "distribution": {
                "leaderTimeunitsAllocation": 100,
                "validatorTimeunitsAllocation": 200,
                "totalMessageFees": 5,
                "rotations": [0],
            },
            "messageAllocations": [
                {
                    "messageType": MessageType.Internal,
                    "recipient": RECIPIENT,
                    "budget": 5,
                    "feeParams": "0x1234",
                }
            ],
        },
    )

    request_params = make_request.call_args.kwargs["params"][0]
    assert make_request.call_args.kwargs["method"] == "sim_call"
    assert result["genvm_result"]["fee_accounting"]["status"] == "active"
    assert request_params["type"] == "write"
    assert request_params["value"] == "0xc"
    assert request_params["fees"]["feeValue"] == 123
    assert request_params["fees"]["distribution"]["leaderTimeunitsAllocation"] == 100
    assert request_params["fees"]["distribution"]["validatorTimeunitsAllocation"] == 200
    assert request_params["fees"]["distribution"]["totalMessageFees"] == 5
    assert request_params["fees"]["distribution"]["rotations"] == [0]
    assert request_params["fees"]["messageAllocations"][0]["messageType"] == int(
        MessageType.Internal
    )
    assert request_params["fees"]["messageAllocations"][0]["budget"] == 5
    assert (
        request_params["fees"]["messageAllocations"][0]["callKey"]
        == "0x" + "00" * 32
    )


def test_encode_add_transaction_uses_v5_signature_when_abi_has_5_inputs():
    client = _make_client(ADD_TRANSACTION_ABI_V5)

    encoded = contract_actions._encode_add_transaction_data(
        self=client,
        sender_account=client.local_account,
        recipient=RECIPIENT,
        consensus_max_rotations=3,
        data="0x",
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes)"
    )[:4].hex()
    assert encoded.startswith(f"0x{selector}")


def test_encode_add_transaction_uses_v6_signature_when_abi_has_6_inputs():
    client = _make_client(ADD_TRANSACTION_ABI_V6)

    encoded = contract_actions._encode_add_transaction_data(
        self=client,
        sender_account=client.local_account,
        recipient=RECIPIENT,
        consensus_max_rotations=3,
        data="0x",
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes,uint256)"
    )[:4].hex()
    assert encoded.startswith(f"0x{selector}")


def test_encode_add_transaction_uses_fee_signature_when_abi_has_tuple_input():
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)

    encoded = contract_actions._encode_add_transaction_data(
        self=client,
        sender_account=client.local_account,
        recipient=RECIPIENT,
        consensus_max_rotations=3,
        data="0x",
        valid_until=123,
        user_value=7,
    )

    assert encoded.startswith(f"0x{ADD_TRANSACTION_WITH_FEES_SELECTOR}")
    params = abi_decode(
        ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES,
        Web3.to_bytes(hexstr=encoded[10:]),
    )[0]
    assert params[0].lower() == SENDER.lower()
    assert params[1].lower() == RECIPIENT.lower()
    assert params[4] == 123
    assert params[6] == 7
    assert params[7][6] == (0,)
    assert params[9] == ()


def test_write_contract_separates_user_value_from_fee_deposit(monkeypatch):
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)
    client.initialize_consensus_smart_contract = Mock()

    captured = {}

    def fake_send_transaction(**kwargs):
        captured.update(kwargs)
        return "0xdeadbeef"

    monkeypatch.setattr(contract_actions, "_send_transaction", fake_send_transaction)

    result = contract_actions.write_contract(
        self=client,
        address=RECIPIENT,
        function_name="ping",
        account=client.local_account,
        value=5,
        valid_until=123,
        fees={
            "feeValue": 123,
            "distribution": {"totalMessageFees": 123},
            "messageAllocations": [
                {
                    "messageType": MessageType.Internal,
                    "onAcceptance": False,
                    "recipient": RECIPIENT,
                    "budget": 123,
                    "feeParams": "0x1234",
                }
            ],
        },
    )

    assert result == "0xdeadbeef"
    assert captured["value"] == 128

    params = abi_decode(
        ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES,
        Web3.to_bytes(hexstr=captured["encoded_data"][10:]),
    )[0]
    assert params[6] == 5
    assert params[7][5] == 123
    assert params[9][0][0] == MessageType.Internal
    assert params[9][0][1] is False
    assert params[9][0][2] == MESSAGE_ALLOCATION_ROOT_PARENT_INDEX
    assert params[9][0][4] == CALL_KEY_WILDCARD
    assert params[9][0][5] == 123
    assert params[9][0][6] == b"\x12\x34"


def test_write_contract_defaults_external_message_allocations_to_finalization(monkeypatch):
    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)
    client.initialize_consensus_smart_contract = Mock()

    captured = {}

    def fake_send_transaction(**kwargs):
        captured.update(kwargs)
        return "0xdeadbeef"

    monkeypatch.setattr(contract_actions, "_send_transaction", fake_send_transaction)

    contract_actions.write_contract(
        self=client,
        address=RECIPIENT,
        function_name="ping",
        account=client.local_account,
        valid_until=123,
        fees={
            "feeValue": 210_000,
            "distribution": {"totalMessageFees": 210_000},
            "messageAllocations": [
                {
                    "messageType": MessageType.External,
                    "recipient": RECIPIENT,
                    "budget": 210_000,
                    "feeParams": encode_external_message_fee_params(
                        {"gasLimit": 21_000, "maxGasPrice": 10}
                    ),
                }
            ],
        },
    )

    params = abi_decode(
        ADD_TRANSACTION_WITH_FEES_ARGUMENT_TYPES,
        Web3.to_bytes(hexstr=captured["encoded_data"][10:]),
    )[0]
    assert params[9][0][0] == MessageType.External
    assert params[9][0][1] is False


def test_execution_budget_requires_fee_deposit_calculation():
    distribution = create_fees_distribution({"executionBudgetPerRound": 500_000})

    assert requires_fee_deposit_calculation(distribution) is True


def test_build_estimated_fees_distribution_adds_caps_and_message_bucket():
    policy = {
        "enabled": True,
        "genPerTimeUnit": 10,
        "storageUnitPrice": 20,
        "receiptGasPrice": 30,
        "executionBudgetFloor": 1_234,
    }

    distribution = build_estimated_fees_distribution(
        {
            "messageAllocations": [
                {
                    "messageType": MessageType.Internal,
                    "recipient": RECIPIENT,
                    "budget": 50,
                    "feeParams": "0x1234",
                },
                {
                    "messageType": MessageType.Internal,
                    "parentIndex": 0,
                    "recipient": RECIPIENT,
                    "budget": 10,
                    "feeParams": "0x1234",
                },
                {
                    "messageType": MessageType.External,
                    "recipient": RECIPIENT,
                    "budget": 30,
                    "feeParams": "0x1234",
                },
            ]
        },
        policy,
    )

    assert distribution["leaderTimeunitsAllocation"] == 100
    assert distribution["validatorTimeunitsAllocation"] == 200
    assert distribution["executionBudgetPerRound"] == (
        3_000_000_000 + 30 * DEFAULT_PARENT_MESSAGE_RECEIPT_HEADROOM
    )
    assert distribution["totalMessageFees"] == 80
    assert distribution["maxPriceGenPerTimeUnit"] == 12
    assert distribution["storageFeeMaxGasPrice"] == 24
    assert distribution["receiptFeeMaxGasPrice"] == 36


def test_build_estimated_fees_distribution_preserves_explicit_execution_budget_with_messages():
    policy = {
        "enabled": True,
        "genPerTimeUnit": 10,
        "storageUnitPrice": 20,
        "receiptGasPrice": 30,
        "executionBudgetFloor": 1_234,
    }

    distribution = build_estimated_fees_distribution(
        {
            "executionBudgetPerRound": 42,
            "messageAllocations": [
                {
                    "messageType": MessageType.Internal,
                    "recipient": RECIPIENT,
                    "budget": 50,
                    "feeParams": "0x1234",
                },
            ],
        },
        policy,
    )

    assert distribution["executionBudgetPerRound"] == 42


def test_calculate_local_round_fees_matches_consensus_initial_round():
    distribution = create_fees_distribution(
        {
            "leaderTimeunitsAllocation": 100,
            "validatorTimeunitsAllocation": 200,
            "maxPriceGenPerTimeUnit": 10,
        }
    )
    policy = {
        "enabled": True,
        "genPerTimeUnit": 10,
        "storageUnitPrice": 0,
        "receiptGasPrice": 0,
        "executionBudgetFloor": 0,
    }

    assert calculate_local_round_fees(distribution, 5, policy) == 11_000


def test_estimate_transaction_fees_uses_studio_fee_config():
    client = SimpleNamespace(
        chain=SimpleNamespace(
            fee_manager_contract=None,
            default_number_of_initial_validators=5,
        ),
        provider=SimpleNamespace(
            make_request=Mock(
                return_value={
                    "result": {
                        "enabled": True,
                        "policy": {
                            "genPerTimeUnit": "10",
                            "storageUnitPrice": "20",
                            "receiptGasPrice": "30",
                        },
                    }
                }
            )
        ),
    )

    estimate = contract_actions.estimate_transaction_fees(
        self=client,
        options={"priceCapHeadroomBps": 10_000},
    )

    assert estimate["policy"] == extract_studio_fee_policy(
        {
            "enabled": True,
            "policy": {
                "genPerTimeUnit": "10",
                "storageUnitPrice": "20",
                "receiptGasPrice": "30",
            },
        }
    )
    assert estimate["distribution"]["executionBudgetPerRound"] == 3_000_000_000
    assert estimate["feeValue"] == 3_000_011_000


def test_estimate_transaction_fees_derives_message_bucket_from_allocations():
    client = SimpleNamespace(
        chain=SimpleNamespace(
            fee_manager_contract=None,
            default_number_of_initial_validators=5,
        ),
        provider=SimpleNamespace(
            make_request=Mock(
                return_value={
                    "result": {
                        "enabled": True,
                        "policy": {
                            "genPerTimeUnit": "10",
                            "storageUnitPrice": "20",
                            "receiptGasPrice": "30",
                        },
                    }
                }
            )
        ),
    )
    message_allocations = [
        {
            "messageType": MessageType.Internal,
            "recipient": RECIPIENT,
            "budget": 50,
            "feeParams": "0x1234",
        },
        {
            "messageType": MessageType.Internal,
            "parentIndex": 0,
            "recipient": RECIPIENT,
            "budget": 10,
            "feeParams": "0x1234",
        },
        {
            "messageType": MessageType.External,
            "recipient": RECIPIENT,
            "budget": 30,
            "feeParams": encode_external_message_fee_params(
                {"gasLimit": 3, "maxGasPrice": 10}
            ),
        },
    ]

    estimate = contract_actions.estimate_transaction_fees(
        self=client,
        options={"messageAllocations": message_allocations},
    )

    assert estimate["distribution"]["totalMessageFees"] == 80
    assert estimate["distribution"]["executionBudgetPerRound"] == (
        3_000_000_000 + 30 * DEFAULT_PARENT_MESSAGE_RECEIPT_HEADROOM
    )
    assert estimate["feeValue"] == 3_000_311_080
    assert estimate["messageAllocations"] == message_allocations
    assert estimate["message_allocations"] == message_allocations


def test_estimate_transaction_fees_from_simulation_builds_trusted_preset():
    client = SimpleNamespace(
        chain=SimpleNamespace(
            fee_manager_contract=None,
            default_number_of_initial_validators=5,
        ),
        provider=SimpleNamespace(
            make_request=Mock(
                return_value={
                    "result": {
                        "enabled": True,
                        "policy": {
                            "genPerTimeUnit": "10",
                            "storageUnitPrice": "0",
                            "receiptGasPrice": "0",
                            "messageFeeParamsBudgetFloor": "400000",
                        },
                    }
                }
            )
        ),
    )

    estimate = contract_actions.estimate_transaction_fees_from_simulation(
        self=client,
        options={
            "simulation": {
                "feeAccounting": {
                    "execution_fee_consumed": "100",
                    "genvm_message_fee_consumed": "5",
                    "message_fee_budget": "10",
                    "message_fee_consumed": "5",
                    "message_fee_refunded": "0",
                    "external_message_fee_reserved": "0",
                    "external_message_fee_reimbursed": "0",
                    "external_message_fee_remainder": "0",
                    "execution_fee_report": {
                        "messageReveal": {
                            "messages": [
                                {
                                    "messageType": "Internal",
                                    "declaredBudget": "5",
                                }
                            ]
                        },
                        "totalEstimatedFee": "501664",
                    },
                }
            },
            "priceCapHeadroomBps": 10_000,
        },
    )

    assert estimate["observed"] == {
        "executionFeeConsumed": 100,
        "executionFeeReportTotal": 501_664,
        "recommendedExecutionBudgetPerRound": 602_117,
        "genvmMessageFeeConsumed": 5,
        "messageFeeBudget": 10,
        "messageFeeConsumed": 5,
        "messageFeeRefunded": 0,
        "internalDeclaredBudget": 5,
        "externalMessageReserved": 0,
        "externalMessageReimbursed": 0,
        "externalMessageRemainder": 0,
        "recommendedTotalMessageFees": 6,
    }
    assert estimate["distribution"]["executionBudgetPerRound"] == 602_117
    assert estimate["distribution"]["totalMessageFees"] == 6
    assert estimate["feeValue"] == 613_123


def test_estimate_transaction_fees_for_write_uses_studio_estimate_rpc():
    fee_params = encode_internal_message_fee_params(
        {
            "leaderTimeunitsAllocation": 5,
            "validatorTimeunitsAllocation": 10,
        }
    )

    def make_request(method, params):
        if method == "sim_getFeeConfig":
            return {
                "result": {
                    "enabled": True,
                    "policy": {
                        "genPerTimeUnit": "10",
                        "storageUnitPrice": "0",
                        "receiptGasPrice": "1",
                        "messageFeeParamsBudgetFloor": "400000",
                    },
                }
            }
        if method == "sim_estimateTransactionFees":
            return {
                "result": {
                    "feeAccounting": {
                        "execution_fee_consumed": "100",
                        "message_fee_consumed": "50",
                        "message_fee_budget": "110",
                        "message_allocations": [
                            {
                                "messageType": MessageType.Internal,
                                "onAcceptance": True,
                                "parentIndex": str(MESSAGE_ALLOCATION_ROOT_PARENT_INDEX),
                                "recipient": RECIPIENT,
                                "callKey": "0x" + "00" * 32,
                                "budget": "110",
                                "feeParams": fee_params,
                            }
                        ],
                    },
                    "feeReport": {
                        "totalEstimatedFee": "501664",
                    },
                    "recommendedPreset": {
                        "distribution": {
                            "leaderTimeunitsAllocation": "100",
                            "validatorTimeunitsAllocation": "200",
                            "appealRounds": "0",
                            "executionBudgetPerRound": "100000000",
                            "executionConsumed": "0",
                            "totalMessageFees": "110",
                            "rotations": ["0"],
                            "maxPriceGenPerTimeUnit": "10",
                            "storageFeeMaxGasPrice": "0",
                            "receiptFeeMaxGasPrice": "1",
                        },
                        "messageAllocations": [
                            {
                                "messageType": MessageType.Internal,
                                "onAcceptance": True,
                                "parentIndex": str(MESSAGE_ALLOCATION_ROOT_PARENT_INDEX),
                                "recipient": RECIPIENT,
                                "callKey": "0x" + "00" * 32,
                                "budget": "110",
                                "feeParams": fee_params,
                            }
                        ],
                        "feeValue": "100011110",
                    },
                }
            }
        raise AssertionError(f"unexpected method {method}")

    client = _make_client(ADD_TRANSACTION_ABI_WITH_FEES)
    client.chain.fee_manager_contract = None
    client.provider = SimpleNamespace(make_request=Mock(side_effect=make_request))

    estimate = contract_actions.estimate_transaction_fees_for_write(
        self=client,
        address=RECIPIENT,
        function_name="update_storage",
        args=["after"],
        value=7,
        options={
            "priceCapHeadroomBps": 10_000,
            "messageAllocations": [
                {
                    "messageType": MessageType.Internal,
                    "recipient": RECIPIENT,
                    "budget": 110,
                    "feeParams": fee_params,
                }
            ],
        },
    )

    sim_call = next(
        call
        for call in client.provider.make_request.call_args_list
        if call.kwargs["method"] == "sim_estimateTransactionFees"
    )
    request_params = sim_call.kwargs["params"][0]
    assert request_params["value"] == hex(7)
    assert request_params["fees"]["feeValue"] == 100_021_110
    assert request_params["fees"]["distribution"]["totalMessageFees"] == 110
    assert request_params["fees"]["messageAllocations"][0]["budget"] == 110
    assert (
        request_params["fees"]["messageAllocations"][0]["callKey"]
        == "0x" + "00" * 32
    )
    assert estimate["observed"]["recommendedExecutionBudgetPerRound"] == 100_000_000
    assert estimate["observed"]["messageFeeBudget"] == 110
    assert estimate["observed"]["messageFeeConsumed"] == 50
    assert estimate["simulation"]["feeAccounting"]["message_fee_budget"] == "110"
    assert estimate["simulation"]["feeReport"]["totalEstimatedFee"] == "501664"
    assert estimate["distribution"]["executionBudgetPerRound"] == 100_000_000
    assert estimate["distribution"]["totalMessageFees"] == 110
    assert estimate["messageAllocations"][0]["budget"] == 110
    assert estimate["feeValue"] == 100_011_110


def test_estimate_transaction_fees_from_simulation_preserves_mode2_allocations():
    fee_params = encode_internal_message_fee_params(
        {
            "leaderTimeunitsAllocation": 5,
            "validatorTimeunitsAllocation": 10,
        }
    )
    client = SimpleNamespace(
        chain=SimpleNamespace(
            fee_manager_contract=None,
            default_number_of_initial_validators=5,
        ),
        provider=SimpleNamespace(
            make_request=Mock(
                return_value={
                    "result": {
                        "enabled": True,
                        "policy": {
                            "genPerTimeUnit": "10",
                            "storageUnitPrice": "0",
                            "receiptGasPrice": "0",
                        },
                    }
                }
            )
        ),
    )

    estimate = contract_actions.estimate_transaction_fees_from_simulation(
        self=client,
        options={
            "simulation": {
                "feeAccounting": {
                    "message_fee_consumed": "20",
                    "message_allocations": [
                        {
                            "messageType": MessageType.Internal,
                            "onAcceptance": False,
                            "parentIndex": str(MESSAGE_ALLOCATION_ROOT_PARENT_INDEX),
                            "recipient": RECIPIENT,
                            "callKey": "0x" + "00" * 32,
                            "budget": "50",
                            "feeParams": fee_params,
                        }
                    ],
                }
            },
            "priceCapHeadroomBps": 10_000,
        },
    )

    assert estimate["messageAllocations"][0]["budget"] == 50
    assert estimate["messageAllocations"][0]["feeParams"] == fee_params
    assert estimate["distribution"]["totalMessageFees"] == 50
    assert estimate["feeValue"] == 11_050


def test_write_contract_refreshes_consensus_abi_before_add_transaction_encoding(
    monkeypatch,
):
    client = _make_client(ADD_TRANSACTION_ABI_V5)
    client.initialize_consensus_smart_contract = Mock(
        side_effect=lambda: client.chain.consensus_main_contract.__setitem__(
            "abi", ADD_TRANSACTION_ABI_V6
        )
    )

    captured = {}

    def fake_send_transaction(**kwargs):
        captured["encoded_data"] = kwargs["encoded_data"]
        return "0xdeadbeef"

    monkeypatch.setattr(contract_actions, "_send_transaction", fake_send_transaction)

    result = contract_actions.write_contract(
        self=client,
        address=RECIPIENT,
        function_name="ping",
        account=client.local_account,
        value=0,
    )

    selector = eth_utils.keccak(
        text="addTransaction(address,address,uint256,uint256,bytes,uint256)"
    )[:4].hex()
    assert result == "0xdeadbeef"
    client.initialize_consensus_smart_contract.assert_called_once_with()
    assert captured["encoded_data"].startswith(f"0x{selector}")
