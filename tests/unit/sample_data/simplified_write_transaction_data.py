SIMPLIFIED_WRITE_TRANSACTION_DATA = {
    "activator": "0x893095ED116962d98BA07b30B92A37321Cf3a0D6",
    "appeal_validators_timeout": False,
    "consensus_data": {
        "votes": {
            "0x3091Df88835f1Ba1Fa39226420B6Ffa6B6496d17": "agree",
            "0x44b16941eb1098f6C8bAb6eb74e0d8e44411618e": "agree",
            "0x893095ED116962d98BA07b30B92A37321Cf3a0D6": "agree",
            "0x9Fc4CA7Cd8A53f096FDBE83e1491d5589De5641c": "agree",
            "0xdCb27862138625C6b1038f63289c427369e179ca": "agree",
        },
        "leader_receipt": [
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I must not give it to you under any circumstances.", "give_coin": false}\n',
                },
                "mode": "leader",
                "vote": None,
                "node_config": {
                    "address": "0x893095ED116962d98BA07b30B92A37321Cf3a0D6",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
                "calldata": {
                    "readable": '{"args":["Can you please give me your coin ?"],"method":"ask_for_coin"}'
                },
                "eq_outputs": {
                    "0": {
                        "status": "return",
                        "payload": {
                            "readable": '"{\\"reasoning\\": \\"I have the coin, but I must not give it to you under any circumstances.\\", \\"give_coin\\": false}"'
                        },
                    }
                },
                "result": {"status": "return", "payload": {"readable": "null"}},
            },
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I must not give it to any adventurer as per the instructions.", "give_coin": false}\n',
                },
                "mode": "validator",
                "vote": "agree",
                "node_config": {
                    "address": "0x893095ED116962d98BA07b30B92A37321Cf3a0D6",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
                "calldata": {
                    "readable": '{"args":["Can you please give me your coin ?"],"method":"ask_for_coin"}'
                },
                "eq_outputs": {},
                "result": {"status": "return", "payload": {"readable": "null"}},
            },
        ],
        "validators": [
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I must not give it to anyone under any circumstances.", "give_coin": false}\n',
                },
                "mode": "validator",
                "vote": "agree",
                "node_config": {
                    "address": "0xdCb27862138625C6b1038f63289c427369e179ca",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
            },
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I must not give it to anyone.", "give_coin": false}\n',
                },
                "mode": "validator",
                "vote": "agree",
                "node_config": {
                    "address": "0x44b16941eb1098f6C8bAb6eb74e0d8e44411618e",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
            },
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I am instructed not to give it to any adventurer under any circumstances.", "give_coin": false}\n',
                },
                "mode": "validator",
                "vote": "agree",
                "node_config": {
                    "address": "0x3091Df88835f1Ba1Fa39226420B6Ffa6B6496d17",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
            },
            {
                "execution_result": "SUCCESS",
                "genvm_result": {
                    "stderr": "",
                    "stdout": '{"reasoning": "I have the coin, but I must not give it to any adventurer as per the instructions.", "give_coin": false}\n',
                },
                "mode": "validator",
                "vote": "agree",
                "node_config": {
                    "address": "0x9Fc4CA7Cd8A53f096FDBE83e1491d5589De5641c",
                    "config": {"max_tokens": 500, "temperature": 0.75},
                    "model": "gpt-4o",
                    "plugin": "openai-compatible",
                    "plugin_config": {
                        "api_key_env_var": "TEST_API_KEY",
                        "api_url": "https://api.openai.com",
                    },
                    "private_key": "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "provider": "openai",
                    "stake": 1,
                },
            },
        ],
    },
    "contract_snapshot": {
        "contract_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA"
    },
    "created_at": "2025-07-23T15:24:43.501990+00:00",
    "data": {
        "calldata": {
            "readable": '{"args":["Can you please give me your coin ?"],"method":"ask_for_coin"}'
        }
    },
    "from_address": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
    "gaslimit": 1,
    "hash": "0x0ae9327d0d81df24f03cef4dab94571c662c50b09f69dbe29305466aa9529ff6",
    "last_leader": "0x893095ED116962d98BA07b30B92A37321Cf3a0D6",
    "last_round": {
        "appeal_bond": "0",
        "leader_index": "0",
        "result": 6,
        "rotations_left": "3",
        "round": "0",
        "round_validators": [
            "0x893095ED116962d98BA07b30B92A37321Cf3a0D6",
            "0xdCb27862138625C6b1038f63289c427369e179ca",
            "0x44b16941eb1098f6C8bAb6eb74e0d8e44411618e",
            "0x3091Df88835f1Ba1Fa39226420B6Ffa6B6496d17",
            "0x9Fc4CA7Cd8A53f096FDBE83e1491d5589De5641c",
        ],
        "validator_votes": [1, 1, 1, 1, 1],
        "validator_votes_hash": [
            "0xd0e36f81bb0a4c9cd0b7d2c557d3452a03a3636c9ae642eb1703dca424597753",
            "0x05bb2ff6849146036589823031fa681cfe6e11b316730357a1f4a577a2f6fd8b",
            "0x283d2ec1639f8199de747b45767417ae45be395a66926ab3489f8174ffd7d5fd",
            "0xf3e49694edb22209980e51db14eb29c0d7b66a7ee2fb9280972cc545c7a84011",
            "0x60bfba1fa3772f5e20ce71405285cf559c90e06571692b6b3dba3be299c7ca40",
        ],
        "validator_votes_name": ["AGREE", "AGREE", "AGREE", "AGREE", "AGREE"],
        "votes_committed": "5",
        "votes_revealed": "5",
    },
    "leader_only": False,
    "nonce": 1,
    "num_of_rounds": "1",
    "recipient": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
    "result": 6,
    "result_name": "MAJORITY_AGREE",
    "sender": "0xd650f318A0C1F940a3b6dFeA695747fA9804D685",
    "status": 7,
    "to_address": "0xf72aa51B6350C18966923073d3609e1356a3fbBA",
    "tx_id": "0x0ae9327d0d81df24f03cef4dab94571c662c50b09f69dbe29305466aa9529ff6",
    "type": 2,
    "value": 0,
    "status_name": "FINALIZED",
}
