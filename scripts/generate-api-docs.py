#!/usr/bin/env python3
"""Generate Markdown API reference from GenLayerClient docstrings and type hints."""

import inspect
import importlib
import os
import sys
from typing import get_type_hints

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def format_type(annotation):
    if annotation is inspect.Parameter.empty:
        return ""
    name = getattr(annotation, "__name__", None)
    if name:
        return name
    return str(annotation).replace("typing.", "").replace("ForwardRef('", "").replace("')", "")


def generate_method_doc(name, method):
    sig = inspect.signature(method)
    docstring = inspect.getdoc(method) or ""
    params = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        type_str = format_type(param.annotation)
        default = ""
        if param.default is not inspect.Parameter.empty:
            default = f" = {param.default!r}"
        required = param.default is inspect.Parameter.empty
        params.append((pname, type_str, required, default))

    ret = format_type(sig.return_annotation)

    lines = [f"### {name}\n"]
    lines.append(f"{docstring}\n")

    param_parts = []
    for pname, type_str, required, default in params:
        display = f"{pname}: {type_str}" if type_str else pname
        display += default
        param_parts.append(display)

    lines.append(f"```python\nclient.{name}({', '.join(param_parts)})\n```\n")

    if params:
        lines.append("| Parameter | Type | Required | Default |")
        lines.append("|-----------|------|----------|---------|")
        for pname, type_str, required, default in params:
            req_str = "yes" if required else "no"
            type_display = f"`{type_str}`" if type_str else ""
            default_display = default.lstrip(" = ") if default else ""
            lines.append(f"| {pname} | {type_display} | {req_str} | {default_display} |")
        lines.append("")

    if ret:
        lines.append(f"**Returns:** `{ret}`\n")

    lines.append("---\n")
    return "\n".join(lines)


def generate_enum_doc(name, enum_class):
    docstring = inspect.getdoc(enum_class) or ""
    lines = [f"### {name}\n", f"{docstring}\n", "```python"]
    for member in enum_class:
        lines.append(f'{name}.{member.name} = "{member.value}"')
    lines.append("```\n")
    lines.append("---\n")
    return "\n".join(lines)


def main():
    from genlayer_py.client.genlayer_client import GenLayerClient
    from genlayer_py.types.transactions import (
        TransactionStatus, TransactionResult, ExecutionResult, VoteType,
    )

    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "api-references")
    os.makedirs(output_dir, exist_ok=True)

    lines = [
        "# GenLayerPY SDK API Reference\n",
        "Auto-generated from source docstrings.\n",
    ]

    # Client methods
    lines.append("## Client Methods\n")
    client_doc = inspect.getdoc(GenLayerClient) or ""
    lines.append(f"{client_doc}\n")

    public_methods = [
        "fund_account", "get_current_nonce", "initialize_consensus_smart_contract",
        "read_contract", "write_contract", "simulate_write_contract", "deploy_contract",
        "get_contract_schema", "get_contract_schema_for_code", "appeal_transaction",
        "wait_for_transaction_receipt", "get_transaction",
        "get_triggered_transaction_ids", "debug_trace_transaction",
    ]
    for name in public_methods:
        method = getattr(GenLayerClient, name, None)
        if method and callable(method):
            lines.append(generate_method_doc(name, method))

    # Enums
    lines.append("## Types and Enums\n")
    for name, enum_class in [
        ("TransactionStatus", TransactionStatus),
        ("TransactionResult", TransactionResult),
        ("ExecutionResult", ExecutionResult),
        ("VoteType", VoteType),
    ]:
        lines.append(generate_enum_doc(name, enum_class))

    api_path = os.path.join(output_dir, "api.md")
    with open(api_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated: {api_path}")

    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    index_path = os.path.join(output_dir, "index.md")
    with open(readme_path, "r") as src, open(index_path, "w") as dst:
        dst.write(src.read())
    print(f"Generated: {index_path}")


if __name__ == "__main__":
    main()
