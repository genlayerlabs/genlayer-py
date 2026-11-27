# Pull Requests

## Target Branch

| Change | Base |
|---|---|
| Fix or feature for the current line | `vX.Y-dev` named in `support/ci/ACTIVE_DEV_BRANCH` |
| Breaking change, or work for the next line | the next `vX.Y-dev`, if it exists |
| Fix for an older line | that line's `vX.Y-dev`; port it forward in a separate PR |

1. A PR opened against `main` is retargeted to the active dev branch by `Retarget main PRs`
2. Only the promotion PR targets a stable branch, see [release.md](releasing/release.md). `Branch Policy` enforces it
   for the active line: it fails a PR into `vX.Y` whose head is not `vX.Y-dev`

## Checks

| Check | Gate | Trigger |
|---|---|---|
| `Tests` | required | every push to the PR |
| `Branch Policy` | required | every push to the PR |
| `Smoke Tests` | advisory, may fail on testnet capacity | every push, unless the base skips it, see [testing.md](testing.md#smoke) |
| `E2E Tests` | advisory on a dev branch, required to promote | a `/run-e2e` comment by a member or collaborator |

`E2E Tests` runs the PR against the full stack from [genlayer-e2e](https://github.com/genlayerlabs/genlayer-e2e). Only
branches listed in its `release-trains.yaml` are enrolled; a PR into another branch gets *Request needs attention*.
Comment a plain `/run-e2e`; `/run-e2e all` is not needed and costs the shared runner budget

## Description

1. Title is a conventional commit, see [committing.md](committing.md)
2. Body says why, what changed for SDK users, and how it was tested
3. Name a genlayer-js counterpart PR when the change has one, or say why there is none
4. Link the issue, if any

## Landing

A maintainer lands a PR once it is [review-ready](review-ready.md), approved and green. The base is fast-forwarded to
the PR head, which GitHub marks as merged:

```bash
git push origin <head-sha>:refs/heads/vX.Y-dev
```

Never land with a merge commit: neither the merge button, GitHub auto-merge, nor the E2E App's `/merge` or
`/merge-train`. A merge commit is a commit no check ran on. Rebase the PR on its base first if it is behind
