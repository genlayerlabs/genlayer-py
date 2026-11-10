---
name: release
description: Cut a release or release candidate of genlayer-py. Bumps version, updates CHANGELOG, tags, pushes — CI then publishes to PyPI and creates the GitHub Release.
---

# Release skill — genlayer-py

This repo follows a branch-per-release-line model. There is no auto-bump on push. A final release is cut from its stable branch; an RC is cut from the matching `*-dev` integration branch.

## When to use this skill

User asks anything like:
- "release v0.18.1"
- "ship a patch"
- "tag the latest fix as a release"

If they ask "publish to PyPI directly" — refuse and point at this flow. The repo doesn't have an unprotected PyPI push path; the tag is the only release entry point.

## What this repo's release model expects

- Branches are named after the release line they ship: `v0.18` (stable) and `v0.19-dev` (integration). When `v0.19` becomes stable, the previous `v0.18` stays available for back-ports.
- Tags live within those branches: `v0.18.1`, `v0.18.2`, ...
- **Semver-zero rule**: this package is still on a 0.x line, so the MINOR component is the breaking-change boundary. `0.18 → 0.19` IS a major bump. `scripts/release.sh` refuses both `minor` and `major` keywords without `--allow-major` while we're on 0.x.
- A major (= minor on 0.x) bump means cutting a new branch (`v0.19`) — not tagging on top of the current one.
- `CHANGELOG.md` is updated in the release commit by python-semantic-release; an explicit requested version must match the version computed from release history and conventional commits.
- Final tags are cut from `vX.Y`; RC tags such as `v0.19.0-rc.1` are cut from `vX.Y-dev`.
- `publish.yml` verifies that the tag is the current owning branch head, publishes to PyPI, and marks RC GitHub Releases as prereleases.

## Steps

1. **Confirm intent with the user.**
   - Which version? If unspecified, ask whether it's patch or explicit.
   - If they say "minor" or "major" while we're on 0.x, surface that this means cutting a new branch — confirm before proceeding.

2. **Switch to the owning branch + sync.**
   ```bash
   git checkout v0.18
   git pull --ff-only origin v0.18
   ```
   If the working tree isn't clean, stop and surface what's there.

   For `v0.19.0-rc.1`, use `v0.19-dev` instead. The script rejects final versions on a dev branch and prereleases on a stable branch.

3. **Verify the head is shippable.**
   - Latest CI green:
     ```bash
     gh run list --branch v0.18 --commit "$(git rev-parse HEAD)" --limit 1
     ```
   - Inspect commits since the previous tag for surprises:
     ```bash
     git log "$(git describe --tags --abbrev=0)..HEAD" --oneline
     ```

4. **Run the release script.**
   ```bash
   scripts/release.sh <X.Y.Z>                    # final on vX.Y
   scripts/release.sh --allow-major <X.Y.Z-rc.N> # first RC of a new 0.x line
   ```
   First run the same command with `--dry-run`; it exercises all read-only preflight and version-policy checks. The real command bumps `pyproject.toml`, updates `CHANGELOG.md`, commits `chore(release): X.Y.Z`, tags `vX.Y.Z`, and pushes both the branch commit and the tag. It will NOT publish to PyPI — CI handles that.

5. **Watch the publish workflow.**
   ```bash
   gh run watch
   ```
   If `publish.yml` fails (typical: tag/pyproject mismatch, expired `PYPI_API_TOKEN`, build failure), report verbatim and stop. Don't retry blindly.

6. **Confirm on PyPI.**
   ```bash
   pip index versions genlayer-py
   ```
   The latest version should match. Report back with the version and the GitHub Release URL.

## Things to refuse

- **Minor or major bump on 0.x without `--allow-major`**. Those are major bumps in semver-zero and belong on a new stable/dev branch pair.
- **Releasing from `main`** — `main` is retired.
- **A final tag from `*-dev`, or an RC tag from the stable branch** — the tag must belong to the exact owning branch.
- **Hand-editing `pyproject.toml` to bump the version** — the script keeps pyproject, the CHANGELOG entry, the commit message, and the tag in lockstep.
- **Publishing a tag where `publish.yml` failed** — fix the underlying issue, re-cut the release (delete the bad tag locally and on origin, re-run the script).

## Roll-back

If a release shipped but is broken:

1. **Don't yank from PyPI** unless someone with elevated permissions has assessed the impact — PyPI yank is reversible but signals "skip this" to installers and you'll want a follow-up patch up first.
2. **Ship a follow-up patch** via the same flow (`scripts/release.sh patch`).
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
