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
#   scripts/release.sh --promote <X.Y.Z>    (any checkout with this script)
#     Fast-forwards vX.Y to that commit with a plain push, then tags it.
#     If an earlier run moved vX.Y but did not push the tag, it only tags.
#
# The stable branch only accepts commits with a green E2E Tests check,
# so the release commit has to exist (and pass) on dev before it can
# reach vX.Y. That is why finals are no longer bumped on the stable branch.
#
# Keywords instead of a version:
#   scripts/release.sh patch|minor|major           release candidate of that bump
#   scripts/release.sh --final patch|minor|major   final of that bump (step 1)
#
# Options (accepted before or after the version):
#   --dry-run       Run every check and print the plan; change nothing.
#   --allow-major   Allow a 0.x minor bump or a major bump (see below).
#   --final         With a keyword, prepare a final instead of an RC.
#   --promote       Second step of a final.
#
# Semver-zero rule: while the major is 0, the MINOR is the breaking-
# change boundary. 0.18 -> 0.19 IS a major bump and needs --allow-major.
#
# Checks before a release commit (each one refuses on failure):
#   - origin is this repository; on vX.Y-dev, clean, HEAD equal to origin
#   - A green Tests workflow run exists for that exact commit
#   - The requested version matches what the commit history produces and
#     is newer than the version already in pyproject.toml
#   - For a final: origin/vX.Y exists and is an ancestor of HEAD
#
# Checks before --promote:
#   - Tag vX.Y.Z does not exist on origin
#   - origin/vX.Y-dev head is the release commit of X.Y.Z and origin/vX.Y
#     is an ancestor of it, or origin/vX.Y already is that release commit
#   - For X.Y.0: the newest final of an earlier line on origin is in the
#     history of that commit
#   - Tests and E2E Tests are green on that exact commit

set -euo pipefail

# Checks are read from this repository, so origin has to be it too.
REPO="genlayerlabs/genlayer-py"
TESTS_WORKFLOW="tests.yml"
E2E_CHECK="E2E Tests"
# GitHub App the stable-branch ruleset requires the check from.
E2E_APP_ID=2929262
PSR=(uvx --from 'python-semantic-release==10.0.2' semantic-release -c releaserc.toml)

usage() {
  cat >&2 <<EOF
Usage: $0 [--dry-run] [--allow-major] <X.Y.Z-rc.N>      release candidate
       $0 [--dry-run] [--allow-major] <X.Y.Z>           final, step 1
       $0 [--dry-run] --promote <X.Y.Z>                 final, step 2
       $0 [--dry-run] [--allow-major] [--final] patch|minor|major
EOF
}

ALLOW_MAJOR=0
DRY_RUN=0
PROMOTE=0
FINAL=0
VERSION_ARG=""
for arg in "$@"; do
  case "$arg" in
    --allow-major) ALLOW_MAJOR=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --promote) PROMOTE=1 ;;
    --final) FINAL=1 ;;
    -*)
      echo "Unknown option: $arg" >&2
      usage
      exit 2
      ;;
    *)
      if [ -n "$VERSION_ARG" ]; then
        echo "Unexpected extra argument: $arg" >&2
        usage
        exit 2
      fi
      VERSION_ARG="$arg"
      ;;
  esac
done

if [ -z "$VERSION_ARG" ]; then
  usage
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

require_canonical_origin() {
  local url
  url="$(git config --get remote.origin.url | tr '[:upper:]' '[:lower:]' || true)"
  if ! [[ "$url" =~ github\.com[:/]+$REPO(\.git)?/?$ ]]; then
    cat >&2 <<EOF
origin is '${url:-unset}', not github.com/$REPO.
The checks are read from $REPO, so the branches and the tag have to be
pushed there as well. Run this from a clone whose origin is that repository.
EOF
    exit 1
  fi
}

# True when the commit is the release commit of the version.
is_release_commit() {
  [ "$(git log -1 --format=%s "$1")" = "chore(release): $2" ] &&
    [ "$(helper normalize "$(package_version_at "$1")" 2>/dev/null)" = "$2" ]
}

require_green_tests() {
  local sha="$1" conclusions verdict
  conclusions="$(gh run list -R "$REPO" --workflow "$TESTS_WORKFLOW" --commit "$sha" --limit 100 \
    --json status,conclusion \
    --jq '.[] | if .status == "completed" then .conclusion else "pending" end' 2>/dev/null || true)"
  # shellcheck disable=SC2086
  verdict="$(helper runs-verdict $conclusions)"
  case "$verdict" in
    green) ;;
    red)
      echo "A Tests workflow run on $sha is not green. Refusing to release a red commit." >&2
      exit 1
      ;;
    pending)
      echo "A Tests workflow run on $sha is still running. Wait for it and retry." >&2
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
  # filter=all: the newest check run decides, so a rerun in progress is not hidden.
  state="$(
    gh api -X GET "repos/$REPO/commits/$sha/check-runs" \
      -f check_name="$E2E_CHECK" -f filter=all -f per_page=100 \
      --jq "[.check_runs[] | select(.app.id == $E2E_APP_ID)] | sort_by(.id) | last
            | if . == null then \"missing\" else (.conclusion // .status) end" 2>/dev/null || echo "unknown"
  )"
  if [ "$state" != "success" ]; then
    cat >&2 <<EOF
$E2E_CHECK on $sha is '$state' (not success).

Open the promotion PR $dev -> $stable if there is none, run E2E on it
(comment /run-e2e) and wait for the check to pass on this commit.
EOF
    exit 1
  fi
}

promote() {
  local version dev stable tag sha dev_sha stable_sha tag_sha remote_tag have_tag=0
  local remote_tags previous_final previous_stable
  version="$(helper normalize "$VERSION_ARG")" || exit 2
  if [ "$(helper is-prerelease "$version")" = "true" ]; then
    echo "$version is a release candidate: RCs are tagged on the dev branch and never promoted." >&2
    exit 2
  fi
  require_canonical_origin
  dev="$(helper dev-branch "$version")"
  stable="$(helper stable-branch "$version")"
  tag="v$version"

  if ! git fetch --quiet --no-tags origin \
    "+refs/heads/$dev:refs/remotes/origin/$dev" \
    "+refs/heads/$stable:refs/remotes/origin/$stable"; then
    echo "Could not fetch $dev and $stable from origin (git's error is above). Promoting needs both branches there." >&2
    exit 1
  fi
  dev_sha="$(git rev-parse "origin/$dev")"
  stable_sha="$(git rev-parse "origin/$stable")"

  if ! remote_tag="$(git ls-remote --tags origin "refs/tags/$tag")"; then
    echo "Could not ask origin whether tag $tag exists; refusing to promote." >&2
    exit 1
  fi
  if [ -n "$remote_tag" ]; then
    echo "Tag $tag already exists on origin; $version is already released." >&2
    exit 1
  fi

  if is_release_commit "$stable_sha" "$version"; then
    # An earlier run moved the stable branch but did not push the tag.
    sha="$stable_sha"
  elif is_release_commit "$dev_sha" "$version"; then
    sha="$dev_sha"
    if ! git merge-base --is-ancestor "$stable_sha" "$sha"; then
      cat >&2 <<EOF
$stable ($stable_sha) is not an ancestor of $dev ($sha), so $stable can't
be fast-forwarded. Merge $stable into $dev, cut the release commit again
and let the checks run on the new head.
EOF
      exit 1
    fi
  else
    cat >&2 <<EOF
The head of $dev is not the release commit of $version:
  $dev_sha $(git log -1 --format=%s "$dev_sha")

Run 'scripts/release.sh $version' on $dev first. If commits landed after
the release commit, revert it, then cut it again so the changelog and the
tested commit include them.
EOF
    exit 1
  fi

  # An earlier line may have shipped a final since step 1 checked this.
  if [ -z "$(helper predecessor "$version")" ]; then
    if ! remote_tags="$(git ls-remote --tags --refs origin 'refs/tags/v[0-9]*')"; then
      echo "Could not list the tags on origin; refusing to promote." >&2
      exit 1
    fi
    # shellcheck disable=SC2046
    previous_final="$(helper previous-line-final "$dev" $(printf '%s\n' "$remote_tags" | sed 's|.*refs/tags/||'))"
    if [ -n "$previous_final" ]; then
      previous_stable="$(helper stable-branch "$previous_final")"
      if ! git fetch --quiet --no-tags origin "refs/tags/v$previous_final"; then
        echo "Could not fetch tag v$previous_final from origin (git's error is above); refusing to promote." >&2
        exit 1
      fi
      if ! git merge-base --is-ancestor "FETCH_HEAD^{commit}" "$sha"; then
        if [ "$sha" = "$stable_sha" ]; then
          # Too late to refuse: the release commit is already on the stable branch.
          cat >&2 <<EOF
Warning: v$previous_final, the newest final of an earlier line, is not in the
history of $stable, which already carries the release commit of $version.
Tagging it anyway; merge $previous_stable into $dev before the next release.
EOF
        else
          cat >&2 <<EOF
v$previous_final, the newest final of an earlier line, is not in the history
of the release commit of $version ($sha).
Revert that commit on $dev, merge $previous_stable into $dev, run
'scripts/release.sh $version' again and let the checks run on the new head
(see docs/contributing/howto/releasing/new-line.md).
EOF
          exit 1
        fi
      fi
    fi
  fi

  if tag_sha="$(git rev-parse --verify --quiet "refs/tags/$tag^{commit}")"; then
    if [ "$tag_sha" != "$sha" ] || [ "$(git cat-file -t "refs/tags/$tag")" != "tag" ]; then
      echo "A local tag $tag exists that is not an annotated tag on $sha. Delete it (git tag -d $tag) and retry." >&2
      exit 1
    fi
    # Left by a run whose tag push failed.
    have_tag=1
  fi

  require_green_tests "$sha"
  require_green_e2e "$sha" "$dev" "$stable"

  echo "Promoting v$version: $stable -> $sha, then tag $tag."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [ "$stable_sha" = "$sha" ]; then
      echo "  $stable is already at $sha; no branch push needed."
    else
      echo "  would run: git push --no-follow-tags origin $sha:refs/heads/$stable"
    fi
    if [[ "$have_tag" -eq 1 ]]; then
      echo "  would run: git push origin refs/tags/$tag (local tag already on $sha)"
    else
      echo "  would run: git tag -a $tag -m $tag $sha && git push origin refs/tags/$tag"
    fi
    echo "Dry run complete; no branch, tag, push, or publication was performed."
    exit 0
  fi

  # Plain fast-forward: keeps ancestry, and the promotion PR closes as merged.
  if [ "$stable_sha" != "$sha" ]; then
    git push --no-follow-tags origin "$sha:refs/heads/$stable"
  fi
  if [[ "$have_tag" -eq 0 ]]; then
    git tag -a "$tag" -m "$tag" "$sha"
  fi
  git push origin "refs/tags/$tag"

  echo
  echo "Pushed $tag on $stable. publish.yml will fire on the tag and ship to PyPI."
  echo "Track it at: https://github.com/$REPO/actions"
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
See docs/contributing/explanation/release-trains.md.
EOF
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree not clean. Stash or commit first." >&2
  exit 1
fi

require_canonical_origin
git fetch --tags origin "+refs/heads/$branch:refs/remotes/origin/$branch"
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

last_tag="$(git describe --tags --abbrev=0 --match 'v*.*.*' 2>/dev/null || true)"
if [[ -z "$last_tag" ]]; then
  echo "No previous release tag is reachable from $branch; refusing to infer release boundaries." >&2
  exit 1
fi
last_version="$(helper normalize "$last_tag")" || exit 2
current_version="$(helper normalize "$(package_version_at HEAD)")" || exit 2

# Asked from origin: a local tag may be left over from a failed tag push.
if [ "$(helper is-prerelease "$current_version")" = "false" ]; then
  if ! remote_tag="$(git ls-remote --tags origin "refs/tags/v$current_version")"; then
    echo "Could not ask origin whether tag v$current_version exists; refusing to release." >&2
    exit 1
  fi
  if [ -z "$remote_tag" ]; then
    cat >&2 <<EOF
pyproject.toml is at $current_version, which has no tag on origin: $branch
carries an unpublished final release commit. Finish it with
'scripts/release.sh --promote $current_version'. If it must not ship and the
stable branch has not moved to it, revert that commit and run this again.
EOF
    exit 1
  fi
fi

# Until this line has a final, versions derive from the previous line's final.
# shellcheck disable=SC2046
previous_final="$(helper previous-line-final "$branch" $(git tag -l 'v[0-9]*'))"
line_base="${branch#v}"
line_base="${line_base%-dev}.0"
if [ -n "$previous_final" ] &&
  ! git rev-parse --verify --quiet "refs/tags/v$line_base" >/dev/null &&
  ! git merge-base --is-ancestor "refs/tags/v$previous_final^{commit}" HEAD; then
  if [ "$kind" = "final" ]; then
    cat >&2 <<EOF
v$previous_final, the newest final of an earlier line, is not in the history
of $branch. The first final of this line ($line_base) is derived from it:
merge that line's stable branch into $branch first (see
docs/contributing/howto/releasing/new-line.md).
EOF
    exit 1
  fi
  cat >&2 <<EOF
Warning: v$previous_final, the newest final of an earlier line, is not in the
history of $branch. Merge that line's stable branch into $branch before the
final $line_base (see docs/contributing/howto/releasing/new-line.md).
EOF
fi

# The empty-array guard keeps bash 3.2 (macOS) working under set -u.
computed_raw="$("${PSR[@]}" version --print ${release_flags[@]+"${release_flags[@]}"})"
next_version="$(helper normalize "$computed_raw")" || exit 2
next_dev="$(helper dev-branch "$next_version")"
# Empty unless the computed version is on an earlier line than this branch.
earlier_line="$(helper previous-line-final "$branch" "v${next_version%%-*}")"

if [[ -n "${requested_version:-}" && "$requested_version" != "$next_version" ]]; then
  cat >&2 <<EOF
Requested $requested_version, but the release history and conventional commits
produce $next_version. Refusing to publish an unexpected version.
EOF
  if [ "$next_dev" != "$branch" ]; then
    if [ -z "$earlier_line" ]; then
      level_flags=(--patch)
      forced="--final patch"
      if [ "$kind" = "rc" ]; then
        level_flags+=(--as-prerelease --prerelease-token rc)
        forced="patch"
      fi
      forced_version="$(helper normalize "$("${PSR[@]}" version --print "${level_flags[@]}")")" || exit 2
      if [ "$forced_version" = "$requested_version" ]; then
        echo "A feat or breaking commit landed since the last final, so history derives the next line. To release it on $branch, force the level: $0 $forced" >&2
      else
        cat >&2 <<EOF
A feat or breaking commit landed since the last final, so history derives the
next line, and a forced patch ('$0 $forced') counts from the newest release
tag in the repository and gives $forced_version. This script cannot produce
$requested_version from this history.
EOF
      fi
    elif [ "$(helper dev-branch "$last_version")" = "$branch" ]; then
      cat >&2 <<EOF
No feat or breaking commit landed on $branch since the previous line's final,
so history still derives a version of that line, and a forced level would count
past $requested_version. Land the change that opens this line as a feat (or
breaking) commit, then ask for $requested_version again.
EOF
    else
      forced="minor --allow-major"
      [ "$kind" = "final" ] && forced="--final $forced"
      echo "$next_version is not on the line of $branch. The first release of a line is forced with a keyword: $0 $forced" >&2
    fi
  elif [ "$kind" = "final" ] && [ "$(helper is-prerelease "$last_version")" = "false" ]; then
    echo "If only chore/ci/docs commits landed, force the level: $0 --final patch" >&2
  fi
  exit 1
fi

if [ -z "${requested_version:-}" ] && [ "$next_dev" != "$branch" ]; then
  if [ -n "$earlier_line" ]; then
    forced="minor --allow-major"
    [ "$kind" = "final" ] && forced="--final $forced"
    echo "'$VERSION_ARG' gives $next_version, which is on an earlier line than $branch. The first release of a line is forced with: $0 $forced" >&2
  else
    cat >&2 <<EOF
'$VERSION_ARG' counts from the newest release tag in the repository and gives
$next_version, which is past the line of $branch. Ask for the version itself
instead (X.Y.Z, or X.Y.Z-rc.N for a release candidate).
EOF
  fi
  exit 2
fi
helper validate "$branch" "$next_version" >/dev/null

# A forced level counts from the last release candidate and can jump a version.
skipped="$(helper predecessor "$next_version")"
if [ -n "$skipped" ] && ! git rev-parse --verify --quiet "refs/tags/v$skipped" >/dev/null; then
  cat >&2 <<EOF
Refusing $next_version: $skipped was never released (no tag v$skipped), so this
would skip it. Ask for the version itself, for example '$0 $skipped' for
the final or '$0 $skipped-rc.N' for a release candidate.
EOF
  exit 1
fi
stable="$(helper stable-branch "$next_version")"

if [ "$last_version" = "$next_version" ]; then
  echo "v$next_version is already tagged and nothing releasable landed since. Nothing to release." >&2
  exit 1
fi
helper assert-newer "$next_version" "$current_version" "$last_version" >/dev/null

# A final has to reach the stable branch by fast-forward: catch a diverged
# stable branch now, before an E2E run is spent on the release commit.
# ls-remote exits 2 when the branch is not there; anything else is a failed lookup.
stable_rc=0
git ls-remote --exit-code --heads origin "refs/heads/$stable" >/dev/null || stable_rc=$?
if [ "$stable_rc" -ne 0 ] && [ "$stable_rc" -ne 2 ]; then
  echo "Could not ask origin whether $stable exists (git's error is above); refusing to release." >&2
  exit 1
fi
if [ "$stable_rc" -eq 0 ]; then
  git fetch --quiet origin "+refs/heads/$stable:refs/remotes/origin/$stable"
  if ! git merge-base --is-ancestor "origin/$stable" HEAD; then
    if [ "$kind" = "final" ]; then
      cat >&2 <<EOF
$stable has commits that are not in $branch, so it can't be fast-forwarded
to a release commit made here. Merge $stable into $branch first.
EOF
      exit 1
    fi
    echo "Warning: $stable has commits that are not in $branch; merge it before the final." >&2
  fi
elif [ "$kind" = "final" ]; then
  cat >&2 <<EOF
$stable does not exist on origin. The promotion PR needs it as its base:
create it from a commit that is already in $branch (see
docs/contributing/howto/releasing/new-line.md).
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
breaking-change boundary (per semver): $next_version is the first release
of the v0.$next_minor line. Pass --allow-major to confirm.
EOF
      exit 1
    fi
  fi
elif [ "$next_major" != "$cur_major" ] && [ "$ALLOW_MAJOR" -ne 1 ]; then
  cat >&2 <<EOF
Refusing major bump $last_version → $next_version without --allow-major.

$next_version is the first release of a new major line. Pass
--allow-major to confirm.
EOF
  exit 1
fi

if [ "$kind" = "rc" ]; then
  echo "Releasing v$next_version on $branch (previous release: v$last_version)."
else
  echo "Preparing final v$next_version on $branch (previous release: v$last_version); no tag until --promote."
fi

if git rev-parse --verify --quiet "refs/tags/v$next_version" >/dev/null; then
  echo "Tag v$next_version already exists locally; refusing to reuse it." >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete; no release commit, tag, push, or publication was performed."
  exit 0
fi

# The tool writes the version and changelog, commits and tags locally.
"${PSR[@]}" version ${release_flags[@]+"${release_flags[@]}"} --no-push --no-vcs-release

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
  git push --no-follow-tags origin "$branch"
  git push origin "refs/tags/v$next_version"

  echo
  echo "Pushed v$next_version. publish.yml will fire on the tag and ship to PyPI."
  echo "Track it at: https://github.com/$REPO/actions"
  exit 0
fi

git push --no-follow-tags origin "$branch"
release_sha="$(git rev-parse HEAD)"

cat <<EOF

Pushed the release commit of v$next_version to $branch ($release_sha). No tag yet.

Next:
  1. Hold every merge into $branch until step 3 is done: a commit landing
     after this one forces a new release commit and a new E2E run.
  2. Open the promotion PR $branch -> $stable (or reuse the open one) and
     run E2E on it: comment /run-e2e.
  3. When Tests and $E2E_CHECK are green on $release_sha:
       scripts/release.sh --promote $next_version

Nothing else may merge that PR: no merge button, no auto-merge, no /merge
or /merge-train comment, no Legatus self-merge. --promote fast-forwards
$stable to this commit and GitHub then closes the PR as merged.
EOF
