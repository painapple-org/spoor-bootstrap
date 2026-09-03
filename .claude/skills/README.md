# .claude/skills/

There are no Claude-Code-specific skills in this directory on purpose.

The real, harness-agnostic skills for this repo live at the top level, in
[`../../skills/`](../../skills/README.md) — see that file's own README for
the convention. This repo keeps its actual skill content out of a
Claude-Code-specific path deliberately, so that Claude Code, OpenCode,
Codex CLI, or any other harness reads the exact same instructions instead
of each harness getting its own (potentially drifting) copy.

If you're a Claude Code instance and got pointed here by tool discovery:
go read [`../../CLAUDE.md`](../../CLAUDE.md), then
[`../../AGENTS.md`](../../AGENTS.md), then `../../skills/`.
