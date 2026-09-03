# skills/

This directory holds the harness-agnostic skill definitions for a
spoor-bootstrap deployment. It's the top-level, portable, canonical
source of truth. Each harness that wants to discover these natively gets
its own directory of symlinks back into here — `.claude/skills/` for
Claude Code, `.opencode/skills/` for OpenCode — never a copy. See
[`../CLAUDE.md`](../CLAUDE.md), [`../.claude/skills/README.md`](../.claude/skills/README.md)
and [`../.opencode/skills/README.md`](../.opencode/skills/README.md) for
how those symlinks are set up and why editing happens here, not there.

## What belongs in a SKILL here

A SKILL in this directory is **portable prompt content and instructions
only**: what the agent should do, when it applies, and why. Something that
reads the same regardless of which harness (Claude Code, OpenCode, Codex
CLI, or another) is executing it.

A SKILL here explicitly does **not** include:

- **Scheduling mechanics.** Whether a given skill runs via cron, a
  systemd `--user` timer, a harness's own scheduler, or something else is
  a property of the host and the harness you chose — not something this
  repo standardizes. A SKILL file describes *what* should happen when
  it's invoked; a separate, per-deployment scheduling setup (outside this
  directory) decides *when* to invoke it.
- Harness-specific tool syntax, config formats, or file locations.
- App-specific implementation code. A SKILL is instructions an agent
  reads, not a library it imports.

## Adding a new SKILL

Create a subdirectory here (e.g. `skills/your-skill-name/SKILL.md`) with
the instructions, and reference it from `AGENTS.md` or another SKILL if
something else needs to point at it. Don't copy its content elsewhere —
everything that needs it should link to this file, per this repo's own
"every fact has exactly one home" convention.

Then symlink it into each harness-native skills directory so every
harness can actually discover it (a harness resolves its own native path,
it can't follow a prose pointer into a different directory):

```
ln -s ../../skills/your-skill-name .claude/skills/your-skill-name
ln -s ../../skills/your-skill-name .opencode/skills/your-skill-name
```

Git tracks and clones symlinks natively on Linux/macOS, so once these are
committed a fresh clone already has both harness-native paths resolving
to this directory — no install-time step recreates them.

## Current skills

- [`product-tech-stack`](./product-tech-stack/SKILL.md) — the required
  technology stack when building a product for a non-technical end-user.
  Symlinked at `.claude/skills/product-tech-stack` and
  `.opencode/skills/product-tech-stack`.
