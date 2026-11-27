# Committing

PRs land by fast-forward, so every commit on a PR reaches the branch as written and follows this format. Squash fixups
before review; the PR title follows it too

## Format

```text
<type>(<scope>)!: <subject> <gitmoji>

<body>

BREAKING CHANGE: <what breaks and how to migrate>
```

1. **Type** — from the table below, lowercase
2. **Scope** — optional; the component, such as `fees`, `chains`, `abi`, `release`
3. **`!`** — marks a breaking change, as does a `BREAKING CHANGE:` footer
4. **Subject** — imperative, lowercase, no trailing period, ≲70 characters
5. **Gitmoji** — optional, 1 to 3 trailing [gitmoji](https://gitmoji.dev) glyphs for the precise intent, such as `✨` or
   `🐛`
6. **Body** — why, not what; the diff already says what

## Types and the Version

`scripts/release.sh` derives the next version from these with python-semantic-release, configured in `releaserc.toml`

| Type | Derived bump | Use for |
|---|---|---|
| `feat` | minor | New API or behavior |
| `fix`, `perf` | patch | Bug fixes, performance |
| `feat!`, `fix!`, `BREAKING CHANGE:` | minor | Breaking change |
| `build`, `chore`, `ci`, `docs`, `refactor`, `revert`, `style`, `test` | none | Everything else |

On 0.x the minor component is the breaking boundary, so a derived minor bump means the next line, see
[new-line.md](releasing/new-line.md). A `feat` on a line that already shipped a final is released as a patch with
`--final patch`, see [release.md](releasing/release.md); a breaking change belongs on the next line

## Squash Commits

A commit that squashes several changes lists each as a `* <type>(<scope>): <subject>` bullet in the body; the release
tool parses every bullet as its own entry
