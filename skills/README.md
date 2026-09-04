# skills/

This directory holds the harness-agnostic skill definitions for a
spoor-bootstrap deployment. It's the top-level, portable, canonical
source of truth, and the place edits are made — every harness-native path
is a symlink back to here, per "How harnesses discover these" below.

## How harnesses discover these

This section is the one home for how the skills wiring works; everywhere
else in this repo points here rather than re-explaining it.

Each harness that wants to discover these natively gets there via a
single whole-folder symlink pointing back at this directory —
`.claude/skills` -> `../skills` for Claude Code, `.opencode/skills` ->
`../skills` for OpenCode — never a copy, and never a directory of
per-skill symlinks. Because the entire folder is symlinked, anything
added here is automatically visible at both harness-native paths with no
extra wiring per skill, and there is exactly one copy of each skill's
content regardless of which harness you picked.

Git tracks and clones symlinks natively on Linux/macOS, so once
`.claude/skills` and `.opencode/skills` are committed, a fresh clone
already has both harness-native paths resolving to this directory. The
one way this silently breaks is a non-git copy (a GitHub "Download ZIP"),
which turns each symlink into a plain text file containing its target
path; `install.sh` sanity-checks for exactly that.

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

That's the whole step — a new subdirectory here is picked up by both
harnesses immediately, per "How harnesses discover these" above. Add it to
the "Current skills" list below.

## Stubs, and why they say so out loud

Most skills here ship as **stubs**, marked with a literal
`TODO(specialize)` line at every business-specific gap, and opening with a
`Status:` heading that is removed once no markers remain in the file.

Why they're shaped that way, and how a marker gets turned into a real
answer, lives in [`specialize-skills`](./specialize-skills/SKILL.md) — the
one home for that rationale. [`../STARTUP.md`](../STARTUP.md) invokes it as
a step of the first-boot flow.

## Current skills

This list is the one enumeration of what exists here; nothing else in this
repo re-lists them. Every entry is visible to both harnesses via the
whole-folder symlinks described above.

The stubs below are listed in the order the specialization pass works
through them, since later ones depend on earlier answers.
[`specialize-skills`](./specialize-skills/SKILL.md)'s "The stubs to
specialize" is the one home for that order and for why each one sits where
it does; read it there, and keep this list's order matching it when a skill
is added.

- [`product-tech-stack`](./product-tech-stack/SKILL.md) — the required
  technology stack when building a product for a non-technical end-user.
  Finished and fully opinionated; nothing in it needs specializing.
- [`specialize-skills`](./specialize-skills/SKILL.md) — the one-time pass
  that turns the stubs below into this deployment's real instructions,
  using the first-boot interview answers. Finished too — it's the pass
  itself, so it carries no markers of its own.
- [`work-tracker`](./work-tracker/SKILL.md) — *stub.* Reading and writing
  work items in whichever tracker the owner chose: the tracker-agnostic
  operation contract, the pipeline state machine, and the label vocabulary
  the stages depend on, plus
  [`adapters/`](./work-tracker/adapters/README.md) — reference notes on how
  that contract maps onto GitHub Issues, Linear and Jira, to specialize
  from and then prune down to the one that applies.
- [`git-pr-conventions`](./git-pr-conventions/SKILL.md) — *partial stub.*
  The branch/commit/PR/self-merge shipping loop, the review-branch protocol
  that replaces it on a remote with no PR mechanism, plus the
  worktree-isolation and shared-ref hazards of running unattended alongside
  a human.
- [`comms-channel`](./comms-channel/SKILL.md) — *stub.* Talking to the
  owner over whichever channel they chose: who may instruct this agent,
  the prompt-injection boundary, interrupt versus digest, and how to write.
- [`work-pipeline`](./work-pipeline/SKILL.md) — *stub.* The stage chain
  (refine → critique → resolve-critique → implement → review), what each
  stage owns, and why the reviewing session must not be the implementing
  one.
- [`deploy-and-monitor`](./deploy-and-monitor/SKILL.md) — *stub.* Whether
  this deployment inherits an existing CI/CD pipeline or builds the deploy
  path itself, how a merged change reaches the running product across
  however many environments it has, how it's rolled back, whether the data
  is backed up and whether a restore has ever been verified, how the agent
  knows it's healthy, and what it may fix unattended.
- [`private-networking`](./private-networking/SKILL.md) — *stub.* How
  something this agent builds for the owner alone — an internal dashboard,
  a preview environment, an admin tool — becomes privately reachable over a
  mesh VPN instead of a public port and a real domain: the
  defer-to-what-exists check, the Tailscale-by-default recommendation, the
  sidecar-container pattern for exposing one containerized service, the
  owner/agent split on keys and membership, and the deferred case where
  nothing internal exists yet.
- [`internal-dashboard`](./internal-dashboard/SKILL.md) — *stub.* Building
  an internal operations dashboard: whether one is worth building at all,
  the standalone-project shape that keeps it out of the product's repo and
  compose file, the service-naming prefix convention, the rule that a page
  shows real state or says out loud that it doesn't, and verifying it
  serves rather than merely started. Owns *what it serves* only — reaching
  it privately is
  [`private-networking`](./private-networking/SKILL.md)'s, and the signals
  it displays are
  [`deploy-and-monitor`](./deploy-and-monitor/SKILL.md)'s.
