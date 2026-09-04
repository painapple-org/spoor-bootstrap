# skills/

This directory holds the harness-agnostic skill definitions for a
spoor-bootstrap deployment. It's the top-level, portable, canonical
source of truth, and the place edits are made — every harness-native path
is a symlink back to here, per "How harnesses discover these" below.

## How harnesses discover these

This section is the one home for how the skills wiring works; everywhere
else in this repo points here rather than re-explaining it.

Each harness that wants to discover these natively gets there via a
single whole-folder symlink pointing back at this directory — never a
copy, and never a directory of per-skill symlinks. Because the entire
folder is symlinked, anything added here is automatically visible at
every harness-native path with no extra wiring per skill, and there is
exactly one copy of each skill's content regardless of which harness you
picked.

Three such paths are committed, because harnesses disagree about the
directory name and each reads only the one it expects:

| Path | Needed by |
|---|---|
| `.claude/skills` -> `../skills` | Claude Code |
| `.opencode/skills` -> `../skills` | OpenCode |
| `.agents/skills` -> `../skills` | Codex CLI |

A harness reading a path it doesn't own is a bonus, not something to
design around: OpenCode happens to scan all three, which is why it logs a
duplicate-skill warning on startup. That warning is expected and
shouldn't be "fixed" by deleting a symlink —
[`docs/harness-verification.md`](../docs/harness-verification.md) records
why, along with what has and hasn't actually been checked under each
harness.

Git tracks and clones symlinks natively on Linux/macOS, so once these are
committed, a fresh clone already has every harness-native path resolving
to this directory. The one way this silently breaks is a non-git copy (a
GitHub "Download ZIP"), which turns each symlink into a plain text file
containing its target path; `install.sh` sanity-checks for exactly that.

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
  reads, not a library it imports. Where a skill genuinely needs runnable
  code as its starting point — a scaffold every deployment would otherwise
  rebuild from the prose — that code lives in
  [`../templates/`](../templates/README.md) and the SKILL points at it.
  That README is the home for what qualifies.

## Adding a new SKILL

Create a subdirectory here (e.g. `skills/your-skill-name/SKILL.md`) with
the instructions, and reference it from `AGENTS.md` or another SKILL if
something else needs to point at it. Don't copy its content elsewhere —
everything that needs it should link to this file, per this repo's own
"every fact has exactly one home" convention.

That's the whole mechanical step — a new subdirectory here is picked up by
every harness immediately, per "How harnesses discover these" above. Add
it to the "Current skills" list below.

Deciding whether a new file is the right artifact in the first place, and
what has to be true of its content, is a bigger question than the wiring
is, and [`skill-authoring`](./skill-authoring/SKILL.md) is the one home for
it — read it before creating the directory, not after.

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
repo re-lists them. Every entry is visible to every harness via the
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
- [`skill-authoring`](./skill-authoring/SKILL.md) — how to author a
  genuinely new skill here for a capability none of the others reach:
  the cheaper answers to try first, the seam test that decides whether it
  is a new file or a section of an existing one, the file shape CI
  enforces, the stub-versus-finished decision, and the three wiring edits
  a new skill isn't finished without. Finished; it carries no markers.
  Owns *bringing a file into existence*;
  [`specialize-skills`](./specialize-skills/SKILL.md) owns *answering the
  markers in one that already exists*.
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
- [`synthetic-monitoring`](./synthetic-monitoring/SKILL.md) — *stub.*
  Continuously re-proving the product's own user-facing flows still work:
  picking the flows whose silent breakage would embarrass the business,
  proving the real side effect rather than a 200, breaking the product once to
  prove the check catches it, keeping marked test data out of production's
  numbers, what the cadence has to satisfy, and why something outside the
  check has to notice when it stops running. Specializes the runnable runner
  in [`../templates/synthetic-check/`](../templates/synthetic-check/README.md).
  Owns *whether the product's flows still work*;
  [`deploy-and-monitor`](./deploy-and-monitor/SKILL.md) owns the deploy path
  and the inventory of every other health signal.
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
  serves rather than merely started. Specializes the runnable scaffold in
  [`../templates/internal-dashboard/`](../templates/internal-dashboard/README.md)
  rather than designing one from scratch. Owns *what it serves* only — reaching
  it privately is
  [`private-networking`](./private-networking/SKILL.md)'s, and the signals
  it displays are
  [`deploy-and-monitor`](./deploy-and-monitor/SKILL.md)'s.
- [`billing-and-payments`](./billing-and-payments/SKILL.md) — *stub.*
  Working on a product that takes money from its users: where the line
  falls between building a payment integration (ordinary reversible work)
  and moving real money (owner-only), the owner/agent split on the
  provider account and its live keys, the provider-is-the-source-of-truth
  rule for entitlement, the webhook and money-representation constraints
  that are wrong by default, what has to be reported rather than retried,
  and why tax is a legal question rather than an engineering one. Authored
  through [`skill-authoring`](./skill-authoring/SKILL.md) as that skill's
  worked example, and an ordinary skill here in every other respect.
