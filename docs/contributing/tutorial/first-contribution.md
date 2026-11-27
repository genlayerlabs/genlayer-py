# First Contribution

From a fresh clone to an open PR. Each step links the how-to with the details

## 1. Set Up

```bash
git clone https://github.com/genlayerlabs/genlayer-py.git
cd genlayer-py
uv sync --group dev
uv run pytest tests/unit -m "not testnet"
```

The suite passes on a clean checkout. See [setup.md](../howto/setup.md)

## 2. Branch

Branch from the active dev branch, named in `support/ci/ACTIVE_DEV_BRANCH`:

```bash
git switch -c fix/<short-name> "origin/$(cat support/ci/ACTIVE_DEV_BRANCH)"
```

A breaking change goes on the next line instead, see [pr.md](../howto/pr.md#target-branch)

## 3. Change and Test

Make the change with its test next to the code it covers under `tests/unit/`, then run the suite again. Update
`README.md` if users see the change. See [testing.md](../howto/testing.md)

## 4. Commit

```bash
git commit -m "fix(chains): correct the studionet RPC URL 🐛"
```

See [committing.md](../howto/committing.md). Do not touch the version: releases set it

## 5. Open the PR

```bash
gh pr create --base "$(cat support/ci/ACTIVE_DEV_BRANCH)"
```

`gh` pushes the branch, to a fork if you cannot push to the repository

Walk [review-ready.md](../howto/review-ready.md) before asking for review. A maintainer runs `/run-e2e` and lands it,
see [pr.md](../howto/pr.md)
