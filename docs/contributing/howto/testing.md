# Testing

| Suite | Path | Needs | Runs in CI |
|---|---|---|---|
| Unit | `tests/unit/` | nothing | `Tests`, on every PR and push to a `vX.Y-dev` branch |
| Smoke | `tests/unit/smoke/`, marker `testnet` | public testnets | `Smoke Tests`, daily and on PRs; advisory |
| Contract e2e | `tests/e2e/` | a running network and funded accounts | no |
| Cross-repo E2E | [genlayer-e2e](https://github.com/genlayerlabs/genlayer-e2e) | the full GenLayer stack | `E2E Tests`, on `/run-e2e`, see [pr.md](pr.md) |

## Unit

What `Tests` runs:

```bash
uv run pytest tests/unit --disable-warnings -m "not testnet"
```

A single file or test: `uv run pytest tests/unit/client/test_client.py -k name -v`

## Smoke

```bash
uv run pytest tests/unit/smoke -v -m testnet
```

Read-only calls against the deployed testnets. A failure may be testnet capacity, not the SDK; rerun before debugging.
Lines that target a protocol train the public testnets do not run yet skip smoke on their PRs, see the `if:` in
`.github/workflows/smoke.yml`

## Contract E2E

Each test deploys a contract from `tests/e2e/contracts/` and is parametrized over networks, 1 marker per network:
`localnet`, `studionet`, `testnet`. Select one with `-m`:

```bash
uv run pytest tests/e2e -m localnet -v
```

`testnet` cases sign with `ACCOUNT_PRIVATE_KEY_1` .. `ACCOUNT_PRIVATE_KEY_3`, read from the environment
or a `.env` file at the repository root. `.env` is git-ignored; never commit keys

## Writing Tests

1. Put offline tests in `tests/unit/<component>/`, mirroring `genlayer_py/`
2. Put networked tests in `tests/unit/smoke/` with the `testnet` marker, which `Tests` excludes, or in `tests/e2e/`
   with 1 marker per network
3. A bug fix lands with the test that fails without it
