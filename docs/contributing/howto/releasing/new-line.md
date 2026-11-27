# Starting a New Line

A line is a pair of branches: `vX.Y-dev` for integration and `vX.Y` for finals. On 0.x a minor bump is breaking, so
`0.19 → 0.20` opens a new pair instead of tagging on top of the current one

## 1. Branches

1. Cut `vX.Y-dev` from the dev branch of the line before it
2. Create `vX.Y` at a commit already in `vX.Y-dev`, for example the one it was cut from. The promotion PR needs it as
   its base, and the `E2E Tests` ruleset does not apply to creating a branch

## 2. Enroll in E2E

Add the dev branch to the matching track in genlayer-e2e `release-trains.yaml`. Until then, `/run-e2e` on its PRs
answers *Request needs attention* and the promotion PR cannot get `E2E Tests`

## 3. First Release Candidate

```bash
scripts/release.sh minor --allow-major
```

gives `X.Y.0-rc.1`. From then on ask for the version itself, `X.Y.0-rc.2`, then `X.Y.0`: a keyword counts from the last
RC and would skip a version, which the script refuses

## 4. Before the First Final

The line needs at least 1 `feat` or breaking commit since the previous final; with only fixes, history keeps deriving
a version of the previous line and `X.Y.0` is refused

Merge the previous line's stable branch, which carries its newest final tag, into `vX.Y-dev`. The release tool derives
the next version from the newest final it can reach, so without it `scripts/release.sh X.Y.0` is refused. Merge again
if the previous line ships a patch before this line's first final; `--promote` rechecks against origin and, if it
fails, revert the release commit, merge, and cut it again

## 5. Switch the Active Line

When the new line becomes the default target, in 1 change set:

1. Set `support/ci/ACTIVE_DEV_BRANCH` to `vX.Y-dev`
2. Update the genlayer-e2e release-train matrix
3. Check workflows that name a branch, such as the `if:` in `.github/workflows/smoke.yml`

`Fast-forward main` then follows the new branch. `main` must be an ancestor of it, which holds when the new line was cut
from the old one
