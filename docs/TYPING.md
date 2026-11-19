# PEP 561 typing adoption: known issues

This change makes installed SDK annotations visible to downstream type checkers.
It is a prerequisite for DXP-537's generated bindings and must receive independent
review. It is **not approved for the frozen v0.19-dev / 0.19.0 release**. Hold it
until a new development train exists (then retarget) or the repository owner
explicitly approves inclusion. Enabling typing can introduce errors in consumer
CI even when runtime behavior has not changed.

## Audit baseline

Audited the v0.19-dev base `0c18daa` with the marker and ContractMethod TypedDict
correction in this PR, Python 3.12.12, mypy 2.4.1, and the repository's locked
SDK dependencies. Reproduce after `uv sync --group dev`:

```sh
uvx --python .venv/bin/python mypy --python-executable .venv/bin/python --strict --no-incremental genlayer_py
```

Result: **373 errors in 33 files (55 source files checked)**. This is a known-issues
baseline, not a passing strict-mode claim. The generated consumer module can
pass strict checking while the SDK's implementation has these unresolved issues;
checking a consumer does not check all imported implementation bodies.

| Diagnostic | Count |
| --- | ---: |
| `arg-type` | 78 |
| `assignment` | 9 |
| `attr-defined` | 69 |
| `comparison-overlap` | 1 |
| `dict-item` | 1 |
| `import-untyped` | 3 |
| `index` | 12 |
| `no-any-return` | 32 |
| `no-untyped-call` | 24 |
| `no-untyped-def` | 74 |
| `operator` | 2 |
| `override` | 2 |
| `return` | 1 |
| `return-value` | 5 |
| `str-bytes-safe` | 4 |
| `type-arg` | 44 |
| `typeddict-item` | 6 |
| `typeddict-unknown-key` | 2 |
| `union-attr` | 4 |

## Impact and examples

- Missing return/parameter annotations and unconstrained generics allow `Any` to
  escape into consumer code (for example `types/chain.py` and
  `types/calldata.py`). Public annotations are not uniformly complete.
- Implicit package re-exports are rejected by strict `no_implicit_reexport`
  checking, including `genlayer_py/__init__.py` and imports of `eth_utils`
  attributes. Consumers may need imports from defining modules.
- Client/action signatures and calldata/transaction dictionaries disagree in
  places (`arg-type`, `index`, `assignment`, and TypedDict diagnostics). These
  should be reconciled against runtime behavior individually, not suppressed
  across the SDK or treated as proof of runtime failures.
- Some return types/overrides and optional-value handling are inconsistent;
  type checking may expose formerly unchecked calls in downstream applications.
- `rlp` and other dependencies lack usable typing on some import paths
  (`import-untyped`). This PR does not add third-party stub packages.

This PR corrects `ContractMethod` to a TypedDict containing method parameters,
return descriptor and readonly flag, matching actual RPC data. The other
findings remain open; this change does not claim a fully strict-clean SDK.
Do not resolve them by setting global `ignore_errors` or silently weakening
contract address types to `Any`.
