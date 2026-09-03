# .opencode/skills/

Every entry in this directory is a **symlink** into the canonical
[`../../skills/`](../../skills/README.md) directory (e.g.
`.opencode/skills/product-tech-stack` -> `../../skills/product-tech-stack`).
**Do not edit anything here directly** — add or change a skill in
`skills/` and symlink it from here, per
[`skills/README.md`](../../skills/README.md#adding-a-new-skill).

This exists so OpenCode reads the exact same instructions as every other
harness instead of getting its own (potentially drifting) copy. OpenCode
actually also natively reads `.claude/skills/<name>/SKILL.md` directly
(per [opencode.ai/docs/skills](https://opencode.ai/docs/skills/), it
searches `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` at
the project level), so this directory is not strictly required for
OpenCode to find these skills — it's kept anyway so `.opencode/skills/`
is the unambiguous, harness-native path for anyone or any tooling that
specifically expects it, and so this repo's convention (one canonical
`skills/` directory, one symlink per harness-native path) stays
consistent and predictable across harnesses rather than depending on one
harness's willingness to also read another harness's path.

See [`../../AGENTS.md`](../../AGENTS.md) for why the harness-agnostic
`skills/` directory is the one source of truth, and
[`../../.claude/skills/README.md`](../../.claude/skills/README.md) for the
equivalent arrangement for Claude Code.
