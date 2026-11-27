---
name: review-ready
description: The bar a genlayer-py change clears before it is handed back. Use before pushing, opening or updating a PR, or reporting a change finished, and when asked whether something is ready for review.
---

# Review-Ready

Walk [review-ready.md](../../../docs/contributing/howto/review-ready.md) against the actual diff and shell, not memory.
[pr.md](../../../docs/contributing/howto/pr.md) has the target branch, checks and landing

## Report Review-Ready, Never Done

Only 2 answers exist:

- **Review-Ready** — evidence per item, including commands and their output
- **Not Review-Ready** — naming the item that fails and the blocker behind it

An unchecked item means **Not Review-Ready**, not a partial pass. Never report **Done**, which also requires review,
`E2E Tests`, landing and release

## While You Work

- Fix defects in your diff without asking
- Raise concerns about the requirement before building on it
- Never land a PR, post `/merge`, or enable auto-merge yourself

## Adapt It

With an escaped-defect fix, say which item should have caught it, why it did not, and propose the amendment
