---
name: release
description: Cut a release or release candidate of genlayer-py. Bumps version, updates CHANGELOG on the dev branch, promotes finals to the stable branch by fast-forward, tags — CI then publishes to PyPI and creates the GitHub Release.
---

# Release skill — genlayer-py

This repo follows a branch-per-release-line model. There is no auto-bump on push. Every release commit is made on the `*-dev` branch of its line with `scripts/release.sh`. An RC is tagged there; a final is promoted to the stable branch by fast-forward and tagged on the stable head.

## When to use this skill

User asks anything like:
- "release v0.19.1"
- "ship a patch"
- "cut an RC"
- "tag the latest fix as a release"

If they ask "publish to PyPI directly" — refuse and point at this flow. The repo doesn't have an unprotected PyPI push path; the tag is the only release entry point.

## What this repo's release model expects

- Branches are named after the release line they ship: `v0.19` (stable) and `v0.19-dev` (integration). When the next line becomes stable, the previous one stays available for back-ports.
- Tags live within those branches: `v0.19.1`, `v0.19.2`, ... on the stable branch; `v0.19.1-rc.1` on the dev branch.
- The stable branch has a ruleset that rejects any commit without a green `E2E Tests` check. A release commit therefore can't be created on the stable branch: it is created on dev, tested there, and the stable branch is fast-forwarded to it.
- The promotion PR `vX.Y-dev` → `vX.Y` is where `E2E Tests` runs. Only `--promote` lands it: it pushes the fast-forward and GitHub closes the PR as merged. It is never merged with the merge button, GitHub auto-merge, the E2E app's merge train (`/merge`, `/merge-train` or its merge action) or the Legatus self-merge loop: a merge or squash commit is a commit `E2E Tests` did not run on, and a squash also breaks ancestry between the two branches.
- **Semver-zero rule**: this package is still on a 0.x line, so the MINOR component is the breaking-change boundary. `0.18 → 0.19` IS a major bump. `scripts/release.sh` refuses minor and major bumps without `--allow-major` while we're on 0.x.
- A major (= minor on 0.x) bump means cutting a new branch pair (`v0.20-dev` / `v0.20`) — not tagging on top of the current one.
- `CHANGELOG.md` is updated in the release commit by python-semantic-release; an explicit requested version must match the version computed from release history and conventional commits.
- `publish.yml` verifies that the tag is the current head of its owning branch (dev for RCs, stable for finals), publishes to PyPI, and marks RC GitHub Releases as prereleases.

## Steps: release candidate

1. **Confirm the version** with the user (`X.Y.Z-rc.N`).
2. **Sync the dev branch.**
   ```bash
   git checkout v0.19-dev
   git pull --ff-only origin v0.19-dev
   ```
   If the working tree isn't clean, stop and surface what's there.
3. **Dry run, then release.**
   ```bash
   scripts/release.sh --dry-run 0.19.1-rc.1
   scripts/release.sh 0.19.1-rc.1
   scripts/release.sh --allow-major 0.20.0-rc.1   # first RC of a new 0.x line
   ```
   The real command commits `chore(release): X.Y.Z-rc.N`, tags it, and pushes both to the dev branch.
4. **Watch the publish workflow** (see below).

## Steps: final

1. **Confirm intent with the user.**
   - Which version? If unspecified, ask whether it's patch or explicit.
   - If they say "minor" or "major" while we're on 0.x, surface that this means cutting a new branch pair — confirm before proceeding.

2. **Sync the dev branch and look at what ships.**
   ```bash
   git checkout v0.19-dev
   git pull --ff-only origin v0.19-dev
   git log "$(git describe --tags --abbrev=0)..HEAD" --oneline
   ```

3. **Create the release commit on dev (no tag).**
   ```bash
   scripts/release.sh --dry-run 0.19.1
   scripts/release.sh 0.19.1
   ```
   This bumps `pyproject.toml` and `uv.lock`, updates `CHANGELOG.md`, commits `chore(release): 0.19.1` and pushes it to `v0.19-dev`. The script needs a green `Tests` run on the commit it starts from and refuses if `v0.19` is not an ancestor of `v0.19-dev`.

   If only `chore:`/`ci:`/`docs:` commits landed, history produces no bump and an explicit version is refused. Force the level instead: `scripts/release.sh --final patch`.

4. **Hold merges into `v0.19-dev`.** From the push in step 3 until step 6 is done, nothing else merges into `v0.19-dev`. A commit that lands after the release commit means the head of dev is no longer the tested release commit: `--promote` refuses, and the release commit has to be reverted and cut again with a new full E2E run. Tell the team, and check that no open PR into `v0.19-dev` has auto-merge enabled or is about to be merged by the Legatus loop.

5. **Promotion PR and E2E.** Open `v0.19-dev` → `v0.19` if it isn't open yet (the Branch Policy check only accepts the dev branch as head). Its head is now the release commit. Ask for E2E on it with a PR comment:
   ```text
   /run-e2e all
   ```
   Wait for `Tests` and `E2E Tests` to be green on the release commit. Do not merge the PR, and do not let anything else merge it (auto-merge, `/merge`, `/merge-train`, Legatus).

6. **Promote.**
   ```bash
   scripts/release.sh --promote --dry-run 0.19.1
   scripts/release.sh --promote 0.19.1
   ```
   Run it from a checkout that has this version of the script: the dev branch, or the stable branch once it has been promoted with it. It verifies that the head of `v0.19-dev` is the release commit of that version, that `v0.19` is an ancestor of it, and that `Tests` and `E2E Tests` are green on it. Then it runs `git push origin <sha>:refs/heads/v0.19` (a plain fast-forward) and pushes the annotated tag `v0.19.1` on the same commit. Options are accepted before or after the version.

7. **Watch the publish workflow.**
   ```bash
   gh run watch
   ```
   If `publish.yml` fails (typical: tag/pyproject mismatch, expired `PYPI_API_TOKEN`, build failure), report verbatim and stop. Don't retry blindly.

8. **Confirm on PyPI.**
   ```bash
   pip index versions genlayer-py
   ```
   The latest version should match. Report back with the version and the GitHub Release URL.

## When something goes wrong between the steps

- **E2E is red on the release commit, or a commit landed on dev after it, and the stable branch has not moved.** The head of dev is no longer a tested release commit and `--promote` refuses. Revert the release commit (`git revert <sha>`, pushed to dev), land the fix if there is one, and run step 3 again. The new release commit lists the change in the changelog, and E2E runs again on it.
- **The stable branch moved** (it is not an ancestor of dev any more). Merge the stable branch into dev, cut the release commit again, and let the checks run on the new head.
- **`--promote` stopped after the branch push and before the tag.** Run it again. It finds the release commit at the head of the stable branch, checks it again and pushes only the tag; this works even when dev has moved on since, and it reuses the local tag a failed tag push left behind. Do not revert anything in this case: the stable branch already holds the release.
- **The fast-forward push is rejected by the ruleset.** The commit does not have a green `E2E Tests` check from the E2E app. Do not ask for a bypass; get the check green on that commit.

## Things to refuse

- **Minor or major bump on 0.x without `--allow-major`**. Those are major bumps in semver-zero and belong on a new stable/dev branch pair.
- **Releasing from `main` or from the stable branch** — the script only makes release commits on `vX.Y-dev`.
- **Merging the promotion PR** with the merge button, GitHub auto-merge, `/merge` or `/merge-train` (the E2E app's merge commands) or the Legatus self-merge loop, or pushing anything to the stable branch other than the `--promote` fast-forward.
- **Tagging by hand** — a final tag that isn't the stable head, or an RC tag that isn't the dev head, is rejected by `publish.yml`.
- **Hand-editing `pyproject.toml` to bump the version** — the script keeps pyproject, the lockfile, the CHANGELOG entry, the commit message, and the tag in lockstep.
- **Publishing a tag where `publish.yml` failed** — fix the underlying issue, re-cut the release (delete the bad tag locally and on origin, re-run the script).

## Roll-back

If a release shipped but is broken:

1. **Don't yank from PyPI** unless someone with elevated permissions has assessed the impact — PyPI yank is reversible but signals "skip this" to installers and you'll want a follow-up patch up first.
2. **Ship a follow-up patch** via the same flow (fix on `vX.Y-dev`, then the final steps above).
3. After the fixed version is live, optionally yank the bad version:
   ```bash
   pip install pkginfo twine
   # use pypi.org web UI to yank — there's no CLI in current PyPI flow
   ```

## Why no auto-bump?

Previously `push: main` triggered `python-semantic-release`, which would auto-bump and tag whenever a `feat:`/`fix:` commit landed. Two failure modes that fix-on-merge can't address:
- Conflated decisions — "merge this PR" silently meant "ship to PyPI".
- Major bumps that slip through (`BREAKING CHANGE` in a PR body produces a 0.X → 0.X+1 bump while on 0.x, which is a major).

Manual + scripted puts a checkpoint between the two without losing the bump-tag automation.
