# spoor-bootstrap

**This is a design document and an install script, not a finished product.**
It is a first draft, meant to be read critically and reworked before anyone
relies on it. If you're expecting a polished, battle-tested framework, you're
early — treat everything here as a starting position, not a spec.

## What this is

`spoor-bootstrap` is a starter kit for standing up your own AI operator on a
fresh VPS: an agent that autonomously builds and runs a product for you, the
way [Spoor](https://painapple.nl) does for painapple. Clone it onto a box you
control, run `install.sh`, and you have the scaffolding to start.

It is explicitly **not**:

- A fork of any specific company's private agent setup. This repo has no
  opinions about *your* product, your work tracker, or your comms channel —
  those are choices you make, not defaults baked in here.
- A chat assistant. The agent this bootstraps is meant to do its work
  *through a devops pipeline* — branching, opening PRs, deploying — the same
  way a human engineer would, not through a conversational buddy loop. If
  you want a personal assistant, this isn't aimed at that.
- A single canonical product. Every deployment of Spoor is expected to
  diverge from every other one over time. There is no "the" Spoor — only
  instances that started from the same seed and grew differently based on
  what their product and owner needed.

If you know [OpenClaw](https://github.com/openclaw/openclaw) or similar "give an agent a
computer" projects, the shape will feel familiar. The two differences that
matter: this is oriented around operating a *product* on a VPS (deploys,
infra, a real running service with real users), not around being a
companion; and its primary interface to the world is a devops pipeline
(git, PRs, CI), not a chat window.

## What it won't do without asking

The autonomy above comes with a default boundary that exists before you've
configured anything. [`AGENTS.md`](./AGENTS.md)'s "Default guardrails"
section is the one home for it — a stop-and-ask list covering irreversible
git operations, destroying data or backups, credential rotation, DNS and
hosting changes, spending money, contacting third parties, and anything with
no concrete rollback. It's read every session, it's in force from the first
one, and your own conventions doc can tighten or extend it but never
silently replaces it. That list isn't restated here; go read it there.

## Hard requirements

Only three things are non-negotiable, and `install.sh` sets all three up:

- **Docker** — everything the agent builds and runs is containerized.
- **uv** — Python dependency management for whatever tooling the agent
  writes for itself.
- **GitHub CLI (`gh`)** — the agent operates through branches, PRs, and the
  GitHub API; `gh` is how it authenticates and acts.

Everything else — which agentic harness you run, which work tracker you
use, which chat platform you wire up, which email provider you pick — is a
choice this repo asks you to make, not something it assumes for you.

## Path to a running instance

1. **Get a VPS.** Any provider works. Painapple's own instance runs on
   OVHcloud; that's not a requirement here, just one data point.
2. **Set up SSH access** to that VPS for yourself and, eventually, for
   whatever automation needs to reach it (CI runners, deploy hooks).
3. **Fork `painapple-org/spoor-bootstrap` on GitHub first, then clone your
   own fork** onto the VPS (or wherever your harness runs from). Do not
   clone `painapple-org/spoor-bootstrap` directly: this checkout is a repo
   the agent keeps maintaining after setup — it opens PRs against it for
   work items that target its own tooling, per
   [`skills/git-pr-conventions`](./skills/git-pr-conventions/SKILL.md) and
   [`skills/work-tracker`](./skills/work-tracker/SKILL.md) — and it can only
   do that if `origin` is a repo you can push to. Cloning upstream directly
   leaves `origin` pointing somewhere you have no write access, and the
   failure only surfaces later, the first time the agent tries to push a
   branch.

   Clone with `git`, not a "Download ZIP": the `.claude/skills` and
   `.opencode/skills` symlinks don't survive a ZIP, and `install.sh` will
   refuse to continue if they're broken.

   If you'd rather not fork, any remote you control works — create an empty
   repo, clone this one, and repoint `origin` at yours before going further.
4. **Pick an agentic harness.** Claude Code, OpenCode, Codex CLI, or
   something else — this repo doesn't prefer one. See
   [`AGENTS.md`](./AGENTS.md) for the harness-agnostic instructions every
   harness should be pointed at, and [`skills/`](./skills/README.md) for
   the portable skill definitions — `.claude/skills` and
   `.opencode/skills` are each a single whole-folder symlink back at that
   same directory, so there's exactly one copy of each skill's content
   regardless of which harness you picked, and a new skill added under
   `skills/` needs no extra wiring to show up in either harness.
5. **Run `./install.sh`.** It installs the three hard requirements above —
   nothing else. It asks no questions and writes no config. Concretely, it
   sets up:
   - Docker, uv, and the GitHub CLI (installed if missing, skipped if
     already present).
   - A sanity check that the `.claude/skills`/`.opencode/skills` symlinks
     resolved correctly (they only break if you got this repo via a ZIP
     download instead of `git clone`).
   - A check that `origin` isn't still pointing at the upstream
     `painapple-org/spoor-bootstrap`, since the agent can't open PRs
     against a repo you don't control.
6. **Run your chosen agentic harness in this checkout and tell it to read
   [`STARTUP.md`](./STARTUP.md).** That's where the actual first-boot flow
   lives now: the interview (your technical level, who the product is for,
   work tracker, comms channel, autonomy model), writing `.env`, generating
   this deployment's own conventions doc (its path recorded once in
   `CONVENTIONS_DOC_PATH` in `.env`, which is what every skill resolves it
   from), specializing the skill stubs in
   [`skills/`](./skills/README.md) against your actual answers, and — if
   you're building for a non-technical end-user — a pointer to the
   opinionated stack in
   [`skills/product-tech-stack/SKILL.md`](./skills/product-tech-stack/SKILL.md).
   The agent hands you a self-provisioning shopping list at the end.

Everything past that point — actually wiring up the work tracker, the comms
channel, deploy automation, scheduling — is deliberately left to you and the
agent you're running. This repo gets you to a box with the right tools
installed and a documented starting point; it doesn't hand you a finished
agent.

## What the skills are, and what "stub" means here

[`skills/`](./skills/README.md) holds the portable, harness-agnostic
instructions this agent operates from. Only one of them
(`product-tech-stack`) is finished; the rest ship as **stubs** — written out
in full wherever a fact is genuinely universal (how a work-tracker state
machine has to behave, why an unattended run must never touch the primary
git checkout, who is allowed to instruct an agent with real tool access),
and marked with a literal `TODO(specialize)` everywhere the real answer
depends on *your* tracker, channel, host and product.

Nothing here guesses those answers on your behalf, which is the point: a
plausible-looking placeholder is indistinguishable from a verified value
until something acts on it. Filling them in is a concrete step in
[`STARTUP.md`](./STARTUP.md)'s flow, driven by
[`skills/specialize-skills`](./skills/specialize-skills/SKILL.md), and it
runs off the interview answers rather than asking you to edit markdown by
hand. Expect to re-run it, one file at a time, as you provision the
accounts on the shopping list below and more of the markers become
answerable. See [`skills/README.md`](./skills/README.md) for the current
list.

## Self-provisioning: what the agent needs, and who sets it up

Once running, the agent instance you've bootstrapped will need its own
identity, separate from yours: its own email address, ideally a real-time
comms channel, its own GitHub account, and its own account on whatever work
tracker and other platforms you've chosen to give it access to.

**A human provisions these — the agent does not register itself for
them.** This is a shopping list handed to you, not a capability the agent
exercises on its own. The reason the identity has to be the agent's own,
rather than reused from your personal accounts, is RBAC: a platform can
only scope what an agent instance is allowed to touch if that instance has
its own account with its own permissions, distinct from yours. See
[`AGENTS.md`](./AGENTS.md) for how this is worded to the agent itself.

## Status

Draft. If you use this and it's wrong, missing, or actively misleading in
places, that's expected at this stage — open an issue or send a PR.
