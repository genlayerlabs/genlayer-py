# Release Trains

Why releases move through 2 branches per line, and why only fast-forwards. The steps are in
[release.md](../howto/releasing/release.md)

## Branches

| Branch | Role | Moves by |
|---|---|---|
| `vX.Y-dev` | Integration: every PR of the line, every release commit | landed PRs, `scripts/release.sh` |
| `vX.Y` | Finals only; tags `vX.Y.Z` | `scripts/release.sh --promote` |
| `main` | Default branch for GitHub UX and tools that need one; not a target | `Fast-forward main`, from `ACTIVE_DEV_BRANCH` |

Older lines stay open for back-ports: a line without a dev branch gets one cut from its stable branch

## Why the Bump Happens on Dev

The `vX.Y` ruleset rejects any commit without a green cross-repo `E2E Tests` check. A release commit made on `vX.Y`
after promotion would be a new, untested commit, so the version bump is made on dev, tested there as the head of the
promotion PR, and `vX.Y` is fast-forwarded to that exact commit

## Why Never a Merge Commit

A merge or squash commit is a commit `E2E Tests` did not run on. A squash also breaks ancestry between dev and stable,
so the next promotion conflicts on the version lines. The same holds for PRs into dev: a fast-forward keeps the tested
commit and the landed commit identical

## Why the Merge Hold

`--promote` only accepts a dev head that is the release commit. A PR that lands between the release commit and the
promotion means the tested commit is no longer what would ship, and the changelog misses that change, so the release
commit is reverted and cut again

## Why PRs Never Target a Stable Branch

A commit that lands on `vX.Y` first is missing from `vX.Y-dev`, so the next release commit can no longer be
fast-forwarded onto `vX.Y`. A 1-line fix goes through dev and ships with the next release

## Why No Auto-Bump

Releases used to be cut by python-semantic-release on every push to `main`. That conflated 2 decisions, *merge this
PR* and *ship to PyPI*, and let a `BREAKING CHANGE` footer bump 0.x to the next line unnoticed. The script keeps the
derived versions and changelog but puts a human between landing and shipping, and refuses a line change without
`--allow-major`
