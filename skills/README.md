# skills/

This directory holds the harness-agnostic skill definitions for a
spoor-bootstrap deployment. It's the top-level, portable counterpart to
whatever harness-specific skill directory your agentic tool also reads
(e.g. Claude Code's `.claude/skills/`) — see [`../CLAUDE.md`](../CLAUDE.md)
and [`../.claude/skills/README.md`](../.claude/skills/README.md) for why
those stay thin pointers into here instead of duplicating content.

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

## Current skills

- [`product-tech-stack`](./product-tech-stack/SKILL.md) — the required
  technology stack when building a product for a non-technical end-user.
