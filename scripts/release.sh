#!/usr/bin/env bash
# Cut a release on the current stable branch.
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
#   scripts/release.sh <X.Y.Z>     # explicit semver — recommended
#   scripts/release.sh patch       # 0.18.0 → 0.18.1
#   scripts/release.sh minor       # 0.18.0 → 0.19.0 — refused unless --allow-major (see below)
#   scripts/release.sh major       # 0.18.0 → 1.0.0  — refused unless --allow-major
#   scripts/release.sh --allow-major <X.Y.Z>
#
# Semver-zero rule: while the major is 0, the MINOR is the breaking-
# change boundary (per semver). 0.18 → 0.19 IS a major bump. The script
# refuses both `minor` and `major` keywords without --allow-major while
# the current major is 0. Patches stay automatic-friendly.
#
# Pre-flight (each check refuses to proceed on failure):
#   - On a v<MAJOR>[.<MINOR>] branch (refuses on main / feature branches)
#   - Working tree clean
#   - Local HEAD matches origin/<branch>
#   - Latest CI run on HEAD is green

set -euo pipefail

ALLOW_MAJOR=0
if [ "${1:-}" = "--allow-major" ]; then
  ALLOW_MAJOR=1
  shift
fi

VERSION_ARG="${1:-}"
if [ -z "$VERSION_ARG" ]; then
  echo "Usage: $0 [--allow-major] <X.Y.Z>|patch|minor|major" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

branch="$(git rev-parse --abbrev-ref HEAD)"
if ! [[ "$branch" =~ ^v[0-9]+(\.[0-9]+)?(-dev)?$ ]]; then
  cat >&2 <<EOF
Refusing to release from '$branch'.

Release branches in this repo are named after the major they ship
(v0.18, v0.19, ...) or the next-major dev line (v0.19-dev). main has
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

if command -v gh >/dev/null 2>&1; then
  status="$(gh run list --branch "$branch" --commit "$local_sha" --limit 1 --json conclusion --jq '.[0].conclusion' 2>/dev/null || echo "")"
  case "$status" in
    success) ;;
    "" )
      echo "Warning: no CI run found for $local_sha on $branch. Continuing anyway." >&2
      ;;
    *)
      echo "Latest CI on $branch@$local_sha is '$status' (not success). Refusing to release a red commit." >&2
      exit 1
      ;;
  esac
fi

current_version="$(grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/version = "([^"]+)"/\1/')"

# Resolve to a concrete X.Y.Z so the major-bump guard can compare.
case "$VERSION_ARG" in
  major|minor|patch)
    next_version="$(python3 - "$current_version" "$VERSION_ARG" <<'PY'
import sys
cur = sys.argv[1].split(".")
kind = sys.argv[2]
major, minor, patch = int(cur[0]), int(cur[1]), int(cur[2])
if kind == "major":
    print(f"{major+1}.0.0")
elif kind == "minor":
    print(f"{major}.{minor+1}.0")
elif kind == "patch":
    print(f"{major}.{minor}.{patch+1}")
PY
)"
    ;;
  *)
    next_version="$VERSION_ARG"
    ;;
esac

if ! [[ "$next_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo "Not a valid semver: $next_version" >&2
  exit 2
fi

cur_major="${current_version%%.*}"
next_major="${next_version%%.*}"
cur_minor="$(echo "$current_version" | cut -d. -f2)"
next_minor="$(echo "$next_version" | cut -d. -f2)"

# Semver-zero: while major == 0, MINOR bumps are major bumps.
if [ "$cur_major" = "0" ]; then
  if [ "$next_major" != "0" ] || [ "$next_minor" != "$cur_minor" ]; then
    if [ "$ALLOW_MAJOR" -ne 1 ]; then
      cat >&2 <<EOF
Refusing $current_version → $next_version without --allow-major.

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
Refusing major bump $current_version → $next_version without --allow-major.

In this repo's release model, a major bump means cutting a new branch
(v$next_major) and switching the default. Don't tag a major on top of
the v$cur_major branch — see CONTRIBUTING.md.
EOF
  exit 1
fi

echo "Releasing v$next_version on $branch (was v$current_version)."

# Use python-semantic-release with an explicit version. --no-push and
# --no-vcs-release keep npm-equivalent (PyPI) and GitHub Release out of
# the dev machine — publish.yml does both on the tag arrival.
uvx --from 'python-semantic-release==10.0.2' \
  semantic-release -c releaserc.toml version "$next_version" \
    --no-push \
    --no-vcs-release

# semantic-release commits and tags locally; we push explicitly so the
# behaviour matches the JS-side script and the order of operations is
# obvious from this file.
git push origin "$branch"
git push origin "v$next_version"

echo
echo "Pushed v$next_version. publish.yml will fire on the tag and ship to PyPI."
echo "Track it at: https://github.com/genlayerlabs/genlayer-py/actions"
