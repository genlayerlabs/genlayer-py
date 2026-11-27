# GenLayerPY

Python SDK for the GenLayer protocol, built on web3.py

Before changing this repository, read the matching page in `docs/contributing/`:
a task has a how-to, a design question has an explanation

## Invariants

1. Every change targets the `vX.Y-dev` branch of its line; `main` and `vX.Y` only move by automation and
   `scripts/release.sh --promote`
2. Never edit the version in `pyproject.toml`, `uv.lock` or `CHANGELOG.md` by hand: `scripts/release.sh` owns them
3. Keep behavior in parity with genlayer-js; a divergence is a bug in 1 of them unless the PR says why
4. A test touching a network carries the `localnet`, `studionet` or `testnet` marker of every network it needs

## Layout

| Path | Holds |
|---|---|
| `genlayer_py/client/` | `GenLayerClient` and `create_client()`, the entry point wrapping web3.py |
| `genlayer_py/chains/` | Chain presets: RPC URLs, consensus contract addresses and ABIs |
| `genlayer_py/transactions/`, `contracts/` | Transaction building, submission, receipts, contract read/write |
| `genlayer_py/abi/` | Calldata encoding and decoding |
| `genlayer_py/consensus/`, `staking/`, `vesting/` | Protocol contract actions and their ABI JSON |
| `genlayer_py/accounts/` | Account creation and private key generation, on eth_account |
| `genlayer_py/provider/`, `config/`, `utils/` | RPC provider, SDK configuration, shared helpers |
| `genlayer_py/types/` | Public type definitions |
| `tests/unit/` | Offline tests, plus networked smoke tests under `tests/unit/smoke/` |
| `tests/e2e/` | Contract tests against a live network |
| `scripts/` | Release tooling and API reference generation |
| `support/ci/` | Data read by CI, such as `ACTIVE_DEV_BRANCH` |

## Tutorial
- [first-contribution.md](docs/contributing/tutorial/first-contribution.md) — clone, change, test, commit, open the PR

## How-To
- [setup.md](docs/contributing/howto/setup.md) — uv dev environment, editable install into another project
- [testing.md](docs/contributing/howto/testing.md) — unit, smoke and e2e suites, markers, environment variables
- [committing.md](docs/contributing/howto/committing.md) — conventional commits and how each type moves the version
- [pr.md](docs/contributing/howto/pr.md) — target branch, required checks, cross-repo E2E, landing
- [review-ready.md](docs/contributing/howto/review-ready.md) — the checks a change must pass before it is put up for review
- [logging.md](docs/contributing/howto/logging.md) — the `genlayer_py` logger and enabling it while developing

## How-To/Releasing
- [release.md](docs/contributing/howto/releasing/release.md) — release candidates, finals, promotion and recovery
- [new-line.md](docs/contributing/howto/releasing/new-line.md) — opening `vX.Y-dev` / `vX.Y` and switching the active line

## How-To/Extending
- [add-a-skill.md](docs/contributing/howto/extending/add-a-skill.md) — agent skills in `.agents/`, the symlink, skill vs how-to

## How-To/Docs
- [style.md](docs/contributing/howto/docs/style.md) — prose conventions for docs, comments and commit bodies

## Explanation
- [docs-layout.md](docs/contributing/explanation/docs-layout.md) — the 4 kinds of page and where each belongs
- [release-trains.md](docs/contributing/explanation/release-trains.md) — why dev and stable branches, fast-forwards only
