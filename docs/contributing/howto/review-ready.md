# Review-Ready

What a change must satisfy before review, checked against the diff and shell

## Intent

1. It does what was asked. The PR traces each requirement to evidence; testing the wrong thing does not count
2. Prefer 1 change, reviewable in 1 sitting. Fix defects inside the diff; record those outside it without folding them
   in or dropping them

## Proof

3. Run locally everything that can run locally: `uv lock --check` and the [unit suite](testing.md#unit), plus the smoke
   or contract e2e tests the change touches. Use CI only for what cannot run locally
4. Map the diff to its tests and run all of them. A bug fix has a test that fails without it

Report a suite that did not run as unrun, never as passed

## The Artifact

5. Read the whole diff, including `uv.lock` and regenerated ABI JSON
6. Leave no known defect, including false prose in comments, docstrings, `README.md` or docs
7. Land documentation in the same PR: `README.md` for user-visible API, `docs/contributing/` for workflows
8. Public API changes are additive on a line that already shipped a final; anything else waits for the next line, see
   [committing.md](committing.md)
9. Mirror the change in genlayer-js, or say in the PR why not

An open PR with green checks completes the list. `E2E Tests`, approval and landing do not, see [pr.md](pr.md)
