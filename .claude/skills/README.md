# .claude/skills/

Every entry in this directory is a **symlink** into the canonical
[`../../skills/`](../../skills/README.md) directory (e.g.
`.claude/skills/product-tech-stack` -> `../../skills/product-tech-stack`).
**Do not edit anything here directly** — you'd be editing through the
symlink into the one real copy anyway, but reach for the canonical path
under `skills/` so it's obvious that's where the edit lives. Do not add a
real (non-symlink) file or directory here either; if a skill doesn't have
a symlink yet, add it in `skills/` and symlink it, per
[`skills/README.md`](../../skills/README.md#adding-a-new-skill).

This exists so Claude Code — which only discovers skills at
`.claude/skills/<name>/SKILL.md` — reads the exact same instructions as
every other harness, instead of getting its own (potentially drifting)
copy. See [`../../AGENTS.md`](../../AGENTS.md) for why the harness-agnostic
`skills/` directory is the one source of truth, and
[`../../.opencode/skills/README.md`](../../.opencode/skills/README.md) for
the equivalent arrangement for OpenCode.

If you're a Claude Code instance and got pointed here by tool discovery:
go read [`../../CLAUDE.md`](../../CLAUDE.md), then
[`../../AGENTS.md`](../../AGENTS.md), then [`../../skills/`](../../skills/README.md).
