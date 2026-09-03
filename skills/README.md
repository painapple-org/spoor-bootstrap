# skills/

This directory holds the harness-agnostic skill definitions for a
spoor-bootstrap deployment. It's the top-level, portable, canonical
source of truth. Each harness that wants to discover these natively gets
there via a single whole-folder symlink pointing back at this directory
— `.claude/skills` -> `../skills` for Claude Code, `.opencode/skills` ->
`../skills` for OpenCode — never a copy, and never a per-skill symlink.
Because the entire folder is symlinked, anything added here is
automatically visible at both harness-native paths with no extra wiring
per skill. See [`../CLAUDE.md`](../CLAUDE.md) and
[`../AGENTS.md`](../AGENTS.md) for why editing happens here, not there.

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

That's the whole step. `.claude/skills` and `.opencode/skills` are each a
single symlink pointing at this directory (not a directory containing one
symlink per skill), so a new subdirectory here is picked up by both
harnesses immediately — there's no per-skill `ln -s` to remember to run.

Git tracks and clones symlinks natively on Linux/macOS, so once
`.claude/skills` and `.opencode/skills` are committed, a fresh clone
already has both harness-native paths resolving to this directory.

## Stubs, and why they say so out loud

Most skills here ship as **stubs**: the parts that are true regardless of
which business, tracker, channel or host a deployment uses are written out
in full, and every business-specific gap is marked with a literal
`TODO(specialize)` line. Such a file opens with a `Status:` heading saying
so, which is removed once no markers remain in it.

That's deliberate, per this repo's "no state that isn't real right now"
principle: a plausible-looking placeholder value is indistinguishable from
a real one until something acts on it, whereas a marker is honest about
being unanswered. Converting those markers into real answers is a concrete
first-boot step, not an implied one — see
[`specialize-skills`](./specialize-skills/SKILL.md), which
[`../STARTUP.md`](../STARTUP.md) invokes as the last step of its flow.

## Current skills

Visible to both harnesses via the whole-folder symlinks above.

- [`product-tech-stack`](./product-tech-stack/SKILL.md) — the required
  technology stack when building a product for a non-technical end-user.
  The one finished, fully opinionated skill here; nothing in it needs
  specializing.
- [`specialize-skills`](./specialize-skills/SKILL.md) — the one-time pass
  that turns the stubs below into this deployment's real instructions,
  using the first-boot interview answers.
- [`work-tracker`](./work-tracker/SKILL.md) — *stub.* Reading and writing
  work items in whichever tracker the owner chose: the tracker-agnostic
  operation contract, the pipeline state machine, and the label vocabulary
  the stages depend on, plus
  [`adapters/`](./work-tracker/adapters/README.md) — reference notes on how
  that contract maps onto GitHub Issues, Linear and Jira, to specialize
  from and then prune down to the one that applies.
- [`git-pr-conventions`](./git-pr-conventions/SKILL.md) — *stub.* The
  branch/commit/PR/self-merge shipping loop, plus the worktree-isolation
  and shared-ref hazards of running unattended alongside a human.
- [`comms-channel`](./comms-channel/SKILL.md) — *stub.* Talking to the
  owner over whichever channel they chose: who may instruct this agent,
  the prompt-injection boundary, interrupt versus digest, and how to write.
- [`work-pipeline`](./work-pipeline/SKILL.md) — *stub.* The stage chain
  (refine → critique → implement → review → merge), what each stage owns,
  and why the reviewing session must not be the implementing one.
- [`deploy-and-monitor`](./deploy-and-monitor/SKILL.md) — *stub.* How a
  merged change reaches the running product, how the agent knows it's
  healthy, and what it may fix unattended.
