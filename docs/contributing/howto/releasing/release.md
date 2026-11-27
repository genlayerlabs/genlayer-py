# Releasing

Every release commit is made on `vX.Y-dev` by `scripts/release.sh`. It bumps `pyproject.toml` and `uv.lock`, updates
`CHANGELOG.md` and commits `chore(release): <version>`. The tag push runs `publish.yml`, which publishes to PyPI and
creates the GitHub Release. Why it works this way: [release-trains.md](../../explanation/release-trains.md)

Every command takes `--dry-run`, which runs its checks and changes nothing. Options go before or after the version

## Before Any Release

Run from a local branch named exactly like the dev branch and equal to origin:

```bash
git switch vX.Y-dev
git pull --ff-only origin vX.Y-dev
git log "$(git describe --tags --abbrev=0)..HEAD" --oneline
```

The script needs a green `Tests` run on the commit it starts from

## Release Candidate

```bash
scripts/release.sh --dry-run X.Y.Z-rc.N
scripts/release.sh X.Y.Z-rc.N
```

Commits, tags `vX.Y.Z-rc.N` on the dev branch and pushes both. RCs publish as PyPI prereleases and never replace the
promotion gate of a final. The first RC of a new line is forced with a keyword, see [new-line.md](new-line.md)

## Final

1. Cut the release commit, untagged:

   ```bash
   scripts/release.sh --dry-run X.Y.Z
   scripts/release.sh X.Y.Z
   ```

   The script refuses if `vX.Y` is not an ancestor of `vX.Y-dev`. When the version is refused because a `feat` landed
   (history derives the next line) or only `chore`, `ci`, `docs` and the like did (no bump), force the level:
   `scripts/release.sh --final patch`

2. Hold every merge into `vX.Y-dev` until step 4 is done. Tell the team, and check that no open PR into it has
   auto-merge enabled
3. Open the promotion PR `vX.Y-dev` → `vX.Y` if it is not open; its head is now the release commit. Comment `/run-e2e`
   on it and wait for `Tests` and `E2E Tests` to be green on that commit. Do not merge it
4. Promote:

   ```bash
   scripts/release.sh --promote --dry-run X.Y.Z
   scripts/release.sh --promote X.Y.Z
   ```

   It checks that the dev head is the release commit of that version, that `vX.Y` is its ancestor and that both checks
   are green, then pushes `<sha>:refs/heads/vX.Y` as a plain fast-forward and the annotated tag `vX.Y.Z`. GitHub
   closes the promotion PR as merged. Run it from a checkout that has this version of the script

5. Watch `publish.yml` with `gh run watch`, then confirm with `pip index versions genlayer-py`

## Recovery

| Situation | Fix |
|---|---|
| E2E red on the release commit, or a commit landed after it, and `vX.Y` has not moved | `git revert` the release commit on dev, land the fix, repeat from step 1 |
| `vX.Y` is no longer an ancestor of dev | Merge `vX.Y` into dev, repeat from step 1 |
| `--promote` stopped after the branch push, before the tag | Run it again: it finds the release commit at the `vX.Y` head and pushes only the tag. Revert nothing |
| The promotion push is rejected by the ruleset | The commit lacks a green `E2E Tests` check from the E2E App; get it green, never ask for a bypass |
| The promotion PR was merged by the button | Fast-forward `vX.Y-dev` to the merge commit before the next release |
| `publish.yml` failed outside the commit, such as an expired `PYPI_API_TOKEN` | Fix it, then `gh run rerun <run-id>` |
| `publish.yml` failed on the commit, such as a build or tag/version mismatch | Report it and stop; the fix ships as the next version |
| A broken version shipped | Ship a patch through the same flow first; yank on PyPI only after that, once its impact is assessed |

## Never

1. Merge the promotion PR by the button, auto-merge, `/merge`, `/merge-train` or a self-merge loop
2. Tag by hand: `publish.yml` rejects a final tag that is not the `vX.Y` head, or an RC tag that is not the dev head
3. Release from `main` or a stable branch
4. Edit the version by hand
