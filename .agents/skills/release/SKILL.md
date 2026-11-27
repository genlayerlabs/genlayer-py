---
name: release
description: Cut a genlayer-py release candidate or final, promote it and watch PyPI publishing. Use when asked to release, ship a patch, cut an RC, tag a fix, promote a dev branch, or publish to PyPI.
---

# Release

Follow [release.md](../../../docs/contributing/howto/releasing/release.md); a new line is
[new-line.md](../../../docs/contributing/howto/releasing/new-line.md). Read both on the dev branch you release from,
together with the header comment of `scripts/release.sh`: the script is the source of truth when they disagree

## Ask First

1. The exact version. If none is given, ask whether it is an RC or a final, and propose the one `--dry-run` computes
2. A minor or major bump on 0.x opens a new line: confirm that before anything else
3. Before step 1 of a final, confirm the merge hold on `vX.Y-dev` is announced
4. Before `--promote`: it pushes the stable branch and the tag, and publishing starts unattended

## Do

- Run every command with `--dry-run` first and show its output
- Report a refusal verbatim with the command the script suggests; do not pick a forced level on your own
- Comment a plain `/run-e2e` on the promotion PR, never `/run-e2e all`

## Refuse

- Publishing to PyPI by any path other than a tag pushed by the script
- Merging the promotion PR, or anything other than the `--promote` fast-forward onto a stable branch
- Tagging by hand, or editing the version by hand
- Retrying a failed `publish.yml` blindly: report its error and stop
