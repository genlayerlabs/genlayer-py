#!/usr/bin/env bash
# Cut a release of the line owned by a vX.Y-dev branch.
#
# Nothing is published from here: publish.yml ships to PyPI and creates
# the GitHub Release when the tag arrives. Only this script is supposed
# to create release commits and tags.
#
# Release candidate, one step on vX.Y-dev:
#   scripts/release.sh <X.Y.Z-rc.N>
#     Release commit and tag, both pushed to vX.Y-dev.
#
# Final, two steps:
#   scripts/release.sh <X.Y.Z>              (on vX.Y-dev)
#     Release commit pushed to vX.Y-dev, no tag. It becomes the head of
#     the promotion PR vX.Y-dev -> vX.Y, so E2E Tests runs on it.
#   scripts/release.sh --promote <X.Y.Z>    (any checkout)
#     Fast-forwards vX.Y to that commit with a plain push, then tags it.
#
# The stable branch only accepts commits with a green E2E Tests check,
# so the release commit has to exist (and pass) on dev before it can
# reach vX.Y. That is why finals are no longer bumped on the stable branch.
#
# Keywords instead of a version:
#   scripts/release.sh patch|minor|major           release candidate of that bump
#   scripts/release.sh --final patch|minor|major   final of that bump (step 1)
#
# Options:
#   --dry-run       Run every check and print the plan; change nothing.
#   --allow-major   Allow a 0.x minor bump or a major bump (see below).
#   --final         With a keyword, prepare a final instead of an RC.
#   --promote       Second step of a final.
#
# Semver-zero rule: while the major is 0, the MINOR is the breaking-
# change boundary. 0.18 -> 0.19 IS a major bump and needs --allow-major.
#
# Checks before a release commit (each one refuses on failure):
#   - On vX.Y-dev, working tree clean, HEAD equal to origin/vX.Y-dev
#   - A green Tests workflow run exists for that exact commit
#   - The requested version matches what the commit history produces
#
# Checks before --promote:
#   - origin/vX.Y-dev head is the release commit of X.Y.Z
#   - origin/vX.Y is an ancestor of it (the push is a fast-forward)
#   - Tests and E2E Tests are green on that exact commit
#   - Tag vX.Y.Z does not exist yet

set -euo pipefail

E2E_CHECK="E2E Tests"
E2E_APP="ci-core-e2e-runner"
PSR=(uvx --from 'python-semantic-release==10.0.2' semantic-release -c releaserc.toml)

ALLOW_MAJOR=0
DRY_RUN=0
PROMOTE=0
FINAL=0
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --allow-major) ALLOW_MAJOR=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --promote) PROMOTE=1 ;;
    --final) FINAL=1 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

VERSION_ARG="${1:-}"
if [ -z "$VERSION_ARG" ]; then
  cat >&2 <<EOF
Usage: $0 [--dry-run] [--allow-major] <X.Y.Z-rc.N>      release candidate
       $0 [--dry-run] [--allow-major] <X.Y.Z>           final, step 1
       $0 [--dry-run] --promote <X.Y.Z>                 final, step 2
       $0 [--dry-run] [--allow-major] [--final] patch|minor|major
EOF
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required to verify the checks on the release commit." >&2
  exit 1
fi

helper() {
  python3 scripts/release_version.py "$@"
}

package_version_at() {
  git show "$1:pyproject.toml" | grep -E '^version = ' | head -1 | sed -E 's/version = "([^"]+)"/\1/'
}

require_green_tests() {
  local sha="$1" conclusions verdict
  conclusions="$(gh run list --workflow tests.yml --commit "$sha" --json conclusion --jq '.[].conclusion' 2>/dev/null || true)"
  # shellcheck disable=SC2086
  verdict="$(helper runs-verdict $conclusions)"
  case "$verdict" in
    green) ;;
    red)
      echo "A Tests workflow run on $sha is not green. Refusing to release a red commit." >&2
      exit 1
      ;;
    *)
      echo "No green Tests workflow run found for $sha. Refusing to release an unverified commit." >&2
      exit 1
      ;;
  esac
}

require_green_e2e() {
  local sha="$1" dev="$2" stable="$3" state
  state="$(
    gh api -X GET "repos/{owner}/{repo}/commits/$sha/check-runs" \
      -f check_name="$E2E_CHECK" -f filter=latest -f per_page=100 \
      --jq "[.check_runs[] | select(.app.slug == \"$E2E_APP\")] | sort_by(.id) | last
            | if . == null then \"missing\" else (.conclusion // .status) end" 2>/dev/null || echo "unknown"
  )"
  if [ "$state" != "success" ]; then
    cat >&2 <<EOF
$E2E_CHECK on $sha is '$state' (not success).

Open the promotion PR $dev -> $stable if there is none, run E2E on it
(comment /run-e2e all) and wait for the check to pass on this commit.
EOF
    exit 1
  fi
}

promote() {
  local version dev stable tag sha stable_sha subject
  version="$(helper normalize "$VERSION_ARG")" || exit 2
  if [ "$(helper is-prerelease "$version")" = "true" ]; then
    echo "$version is a release candidate: RCs are tagged on the dev branch and never promoted." >&2
    exit 2
  fi
  dev="$(helper dev-branch "$version")"
  stable="$(helper stable-branch "$version")"
  tag="v$version"

  if ! git fetch --quiet --tags origin \
    "+refs/heads/$dev:refs/remotes/origin/$dev" \
    "+refs/heads/$stable:refs/remotes/origin/$stable"; then
    echo "Could not fetch $dev and $stable from origin. Both branches must exist before promoting." >&2
    exit 1
  fi
  sha="$(git rev-parse "origin/$dev")"
  stable_sha="$(git rev-parse "origin/$stable")"

  if [ -n "$(git ls-remote --tags origin "refs/tags/$tag")" ]; then
    echo "Tag $tag already exists on origin; $version is already released." >&2
    exit 1
  fi
  if git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
    echo "A local tag $tag exists but is not on origin. Delete it (git tag -d $tag) and retry." >&2
    exit 1
  fi

  subject="$(git log -1 --format=%s "$sha")"
  if [ "$subject" != "chore(release): $version" ]; then
    cat >&2 <<EOF
The head of $dev is not the release commit of $version:
  $sha $subject

Run 'scripts/release.sh $version' on $dev first. If commits landed after
the release commit, revert it, then cut it again so the changelog and the
tested commit include them.
EOF
    exit 1
  fi
  helper verify-tag "$tag" "$(package_version_at "$sha")" >/dev/null

  if [ "$stable_sha" != "$sha" ] && ! git merge-base --is-ancestor "$stable_sha" "$sha"; then
    cat >&2 <<EOF
$stable ($stable_sha) is not an ancestor of $dev ($sha), so $stable can't
be fast-forwarded. Merge $stable into $dev, cut the release commit again
and let the checks run on the new head.
EOF
    exit 1
  fi

  require_green_tests "$sha"
  require_green_e2e "$sha" "$dev" "$stable"

  echo "Promoting v$version: $stable -> $sha, then tag $tag."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [ "$stable_sha" = "$sha" ]; then
      echo "  $stable is already at $sha; no branch push needed."
    else
      echo "  would run: git push origin $sha:refs/heads/$stable"
    fi
    echo "  would run: git tag -a $tag -m $tag $sha && git push origin refs/tags/$tag"
    echo "Dry run complete; no branch, tag, push, or publication was performed."
    exit 0
  fi

  # Plain fast-forward: keeps ancestry, and the promotion PR closes as merged.
  if [ "$stable_sha" != "$sha" ]; then
    git push origin "$sha:refs/heads/$stable"
  fi
  git tag -a "$tag" -m "$tag" "$sha"
  git push origin "refs/tags/$tag"

  echo
  echo "Pushed $tag on $stable. publish.yml will fire on the tag and ship to PyPI."
  echo "Track it at: https://github.com/genlayerlabs/genlayer-py/actions"
}

if [[ "$PROMOTE" -eq 1 ]]; then
  if [[ "$FINAL" -eq 1 || "$ALLOW_MAJOR" -eq 1 ]]; then
    echo "--promote takes only --dry-run and the final version." >&2
    exit 2
  fi
  promote
  exit 0
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if ! [[ "$branch" =~ ^v[0-9]+\.[0-9]+-dev$ ]]; then
  cat >&2 <<EOF
Refusing to release from '$branch'.

Release commits are made on the dev branch of the line (v0.19-dev for
v0.19.x): release candidates are tagged there, and finals are promoted
to the stable branch with 'scripts/release.sh --promote <X.Y.Z>'.
A line without a dev branch needs one first (create vX.Y-dev from vX.Y).
See docs/BRANCHING.md.
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
Pull (or push) before releasing so the release commit sits on the
branch's public history.
EOF
  exit 1
fi

require_green_tests "$local_sha"

release_flags=()
case "$VERSION_ARG" in
  major|minor|patch)
    release_flags+=("--$VERSION_ARG")
    kind="rc"
    [[ "$FINAL" -eq 1 ]] && kind="final"
    ;;
  *)
    requested_version="$(helper normalize "$VERSION_ARG")" || exit 2
    kind="final"
    if [ "$(helper is-prerelease "$requested_version")" = "true" ]; then
      kind="rc"
      if [[ "$FINAL" -eq 1 ]]; then
        echo "--final does not apply to release candidate $requested_version." >&2
        exit 2
      fi
    fi
    ;;
esac

if [ "$kind" = "rc" ]; then
  release_flags+=(--as-prerelease --prerelease-token rc)
fi

computed_raw="$("${PSR[@]}" version --print "${release_flags[@]}")"
next_version="$(helper normalize "$computed_raw")" || exit 2

if [[ -n "${requested_version:-}" && "$requested_version" != "$next_version" ]]; then
  cat >&2 <<EOF
Requested $requested_version, but the release history and conventional commits
produce $next_version. Refusing to publish an unexpected version.
EOF
  if [ "$kind" = "final" ]; then
    echo "If only chore/ci/docs commits landed, force the level: $0 --final patch" >&2
  fi
  exit 1
fi

helper validate "$branch" "$next_version" >/dev/null
stable="$(helper stable-branch "$next_version")"

last_tag="$(git describe --tags --abbrev=0 --match 'v*.*.*' 2>/dev/null || true)"
if [[ -z "$last_tag" ]]; then
  echo "No previous release tag is reachable from $branch; refusing to infer release boundaries." >&2
  exit 1
fi
last_version="$(helper normalize "$last_tag")" || exit 2
if [ "$last_version" = "$next_version" ]; then
  echo "v$next_version is already tagged and nothing releasable landed since. Nothing to release." >&2
  exit 1
fi
current_version="$(helper normalize "$(package_version_at HEAD)")" || exit 2
if [ "$current_version" = "$next_version" ]; then
  cat >&2 <<EOF
pyproject.toml is already at $next_version, so $branch carries an untagged
release commit for it. Promote it (scripts/release.sh --promote $next_version)
or, if commits landed after it, revert that release commit and run this again.
EOF
  exit 1
fi
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

if [ "$kind" = "rc" ]; then
  echo "Releasing v$next_version on $branch (previous release: v$last_version)."
else
  echo "Preparing final v$next_version on $branch (previous release: v$last_version); no tag until --promote."
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete; no release commit, tag, push, or publication was performed."
  exit 0
fi

if git rev-parse --verify --quiet "refs/tags/v$next_version" >/dev/null; then
  echo "Tag v$next_version already exists locally; refusing to reuse it." >&2
  exit 1
fi

# The tool writes the version and changelog, commits and tags locally.
"${PSR[@]}" version "${release_flags[@]}" --no-push --no-vcs-release

if [ "$(git rev-parse HEAD)" = "$local_sha" ]; then
  echo "Release tool did not create a release commit for v$next_version; nothing to push." >&2
  exit 1
fi
if [ "$kind" = "final" ]; then
  # --no-tag is ignored when the tool commits; --promote tags a final instead.
  git tag -d "v$next_version" >/dev/null
fi
helper verify-tag "v$next_version" "$(package_version_at HEAD)" >/dev/null

if [ "$kind" = "rc" ]; then
  if ! git rev-parse --verify --quiet "refs/tags/v$next_version" >/dev/null; then
    echo "Release tool did not create the expected tag v$next_version; refusing to push." >&2
    exit 1
  fi
  git push origin "$branch"
  git push origin "v$next_version"

  echo
  echo "Pushed v$next_version. publish.yml will fire on the tag and ship to PyPI."
  echo "Track it at: https://github.com/genlayerlabs/genlayer-py/actions"
  exit 0
fi

git push origin "$branch"
release_sha="$(git rev-parse HEAD)"

cat <<EOF

Pushed the release commit of v$next_version to $branch ($release_sha). No tag yet.

Next:
  1. Open the promotion PR $branch -> $stable (or reuse the open one) and
     run E2E on it: comment /run-e2e all.
  2. When Tests and $E2E_CHECK are green on $release_sha:
       scripts/release.sh --promote $next_version

Do not press the merge button on that PR: --promote fast-forwards $stable
to this commit and GitHub then closes the PR as merged.
EOF
