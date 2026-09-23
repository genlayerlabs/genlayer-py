#!/usr/bin/env bash
# Cut a release on the current owning version branch.
#
# Bumps pyproject.toml, updates CHANGELOG.md via python-semantic-release,
# commits, tags vX.Y.Z, and pushes both the branch commit and the tag.
# publish.yml takes over from the tag push (build → PyPI publish →
# GitHub Release).
#
# Releases are deliberate. There is no auto-bump on push; only this
# script is supposed to create release tags. Run from the major branch
# you want to ship a release on (e.g. v0.18 for v0.18.x).
#
# Usage:
#   scripts/release.sh <X.Y.Z>          # final release from vX.Y
#   scripts/release.sh <X.Y.Z-rc.N>     # release candidate from vX.Y-dev
#   scripts/release.sh patch       # 0.18.0 → 0.18.1
#   scripts/release.sh minor       # 0.18.0 → 0.19.0 — refused unless --allow-major (see below)
#   scripts/release.sh major       # 0.18.0 → 1.0.0  — refused unless --allow-major
#   scripts/release.sh --allow-major <X.Y.Z>
#   scripts/release.sh --dry-run [--allow-major] <version>
#
# Semver-zero rule: while the major is 0, the MINOR is the breaking-
# change boundary (per semver). 0.18 → 0.19 IS a major bump. The script
# refuses both `minor` and `major` keywords without --allow-major while
# the current major is 0. Patches stay automatic-friendly.
#
# Pre-flight (each check refuses to proceed on failure):
#   - On vX.Y for a final or vX.Y-dev for a release candidate
#   - Working tree clean
#   - Local HEAD matches origin/<branch>
#   - Latest CI run on HEAD is green

set -euo pipefail

ALLOW_MAJOR=0
DRY_RUN=0
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --allow-major) ALLOW_MAJOR=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

VERSION_ARG="${1:-}"
if [ -z "$VERSION_ARG" ]; then
  echo "Usage: $0 [--dry-run] [--allow-major] <X.Y.Z>|<X.Y.Z-rc.N>|patch|minor|major" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

branch="$(git rev-parse --abbrev-ref HEAD)"
if ! [[ "$branch" =~ ^v[0-9]+\.[0-9]+(-dev)?$ ]]; then
  cat >&2 <<EOF
Refusing to release from '$branch'.

Release branches in this repo are named after the line they ship
(v0.18, v0.19, ...) or its prerelease dev line (v0.19-dev). main has
been retired — see CONTRIBUTING.md for the branch model.

If you intended to ship a v0.18.x release, run:
  git checkout v0.18 && git pull --ff-only && scripts/release.sh ...
EOF
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree not clean. Stash or commit first." >&2
  exit 1
fi

git fetch --tags origin "$branch"
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"
if [ "$local_sha" != "$remote_sha" ]; then
  cat >&2 <<EOF
Local $branch ($local_sha) does not match origin/$branch ($remote_sha).
Pull (or push) before releasing so the published tag is reachable from
the branch's public history.
EOF
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required to verify the release head's native tests." >&2
  exit 1
fi
status="$(gh run list --workflow tests.yml --branch "$branch" --commit "$local_sha" --limit 1 --json conclusion --jq '.[0].conclusion' 2>/dev/null || echo "")"
case "$status" in
  success) ;;
  "" )
    echo "No Tests workflow run found for $local_sha on $branch. Refusing to release an unverified head." >&2
    exit 1
    ;;
  *)
    echo "Latest Tests workflow on $branch@$local_sha is '$status' (not success). Refusing to release a red commit." >&2
    exit 1
    ;;
esac

release_flags=()
case "$VERSION_ARG" in
  major|minor|patch)
    release_flags+=("--$VERSION_ARG")
    ;;
  *)
    requested_version="$(python3 scripts/release_version.py normalize "$VERSION_ARG")" || exit 2
    ;;
esac

if [[ "$branch" == *-dev ]]; then
  release_flags+=(--as-prerelease --prerelease-token rc)
fi

computed_raw="$(
  uvx --from 'python-semantic-release==10.0.2' \
    semantic-release -c releaserc.toml version --print "${release_flags[@]}"
)"
next_version="$(python3 scripts/release_version.py normalize "$computed_raw")" || exit 2

if [[ -n "${requested_version:-}" && "$requested_version" != "$next_version" ]]; then
  cat >&2 <<EOF
Requested $requested_version, but the release history and conventional commits
produce $next_version. Refusing to publish an unexpected version.
EOF
  exit 1
fi

python3 scripts/release_version.py validate "$branch" "$next_version" >/dev/null

last_tag="$(git describe --tags --abbrev=0 --match 'v*.*.*' 2>/dev/null || true)"
if [[ -z "$last_tag" ]]; then
  echo "No previous release tag is reachable from $branch; refusing to infer release boundaries." >&2
  exit 1
fi
last_version="$(python3 scripts/release_version.py normalize "$last_tag")" || exit 2
cur_major="${last_version%%.*}"
next_major="${next_version%%.*}"
cur_minor="$(echo "$last_version" | cut -d. -f2)"
next_minor="$(echo "$next_version" | cut -d. -f2)"

# Semver-zero: while major == 0, MINOR bumps are major bumps.
if [ "$cur_major" = "0" ]; then
  if [ "$next_major" != "0" ] || [ "$next_minor" != "$cur_minor" ]; then
    if [ "$ALLOW_MAJOR" -ne 1 ]; then
      cat >&2 <<EOF
Refusing $last_version → $next_version without --allow-major.

This package is still on a 0.x line, so the MINOR component is the
breaking-change boundary (per semver). 0.$cur_minor → 0.$next_minor
counts as a major bump and should land on a new branch (v0.$next_minor)
following the model in CONTRIBUTING.md.

If you actually want this on the current branch, pass --allow-major.
EOF
      exit 1
    fi
  fi
elif [ "$next_major" != "$cur_major" ] && [ "$ALLOW_MAJOR" -ne 1 ]; then
  cat >&2 <<EOF
Refusing major bump $last_version → $next_version without --allow-major.

In this repo's release model, a major bump means cutting a new branch
(v$next_major) and switching the default. Don't tag a major on top of
the v$cur_major branch — see CONTRIBUTING.md.
EOF
  exit 1
fi

echo "Releasing v$next_version on $branch (previous release: v$last_version)."

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete; no release commit, tag, push, or publication was performed."
  exit 0
fi

# Use python-semantic-release to update the version and changelog and create
# the local release commit and tag. Publishing remains CI-only.
uvx --from 'python-semantic-release==10.0.2' \
  semantic-release -c releaserc.toml version "${release_flags[@]}" \
    --no-push \
    --no-vcs-release

package_version="$(grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/version = "([^"]+)"/\1/')"
python3 scripts/release_version.py verify-tag "v$next_version" "$package_version" >/dev/null
if ! git rev-parse --verify --quiet "refs/tags/v$next_version" >/dev/null; then
  echo "Release tool did not create the expected tag v$next_version; refusing to push." >&2
  exit 1
fi

# semantic-release commits and tags locally; we push explicitly so the
# behaviour matches the JS-side script and the order of operations is
# obvious from this file.
git push origin "$branch"
git push origin "v$next_version"

echo
echo "Pushed v$next_version. publish.yml will fire on the tag and ship to PyPI."
echo "Track it at: https://github.com/genlayerlabs/genlayer-py/actions"
