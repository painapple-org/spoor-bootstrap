# spoor-bootstrap

[![CI](https://github.com/painapple-org/spoor-bootstrap/actions/workflows/ci.yml/badge.svg)](https://github.com/painapple-org/spoor-bootstrap/actions/workflows/ci.yml)

`spoor-bootstrap` is a starter kit for standing up your own AI operator on
a VPS you control: an agent that builds, deploys and runs a software
product largely on its own, working through git branches, pull requests
and deploys rather than through a chat window. "Spoor" is Dutch for *track*
or *trail*, and it's the name of the agent instance this bootstraps; the
one that runs [painapple](https://painapple.nl) is the reference deployment
this repo was extracted from.

> **Status: early draft.** What you get here is a design document, an
> install script, and a set of deliberately unfinished skill files — not a
> polished, battle-tested framework. It's meant to be read critically and
> reworked before anyone relies on it. If you use it and it's wrong,
> missing or actively misleading in places, that's expected at this stage:
> open an issue or send a PR.

## What you actually get

Three things, and nothing more:

- **[`install.sh`](./install.sh)** — mechanical OS-level bootstrap. It
  installs three tools and sanity-checks the checkout. It asks no
  questions and writes no config.
- **[`STARTUP.md`](./STARTUP.md)** — the prompt you paste into your agentic
  harness for the first run. The agent interviews you, writes `.env`,
  generates this deployment's own conventions doc, fills in the skill
  files, and hands you a list of accounts to create.
- **[`skills/`](./skills/README.md)** — harness-agnostic instructions the
  agent operates from, with [`AGENTS.md`](./AGENTS.md) as the entrypoint
  that ties them together.

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

If you know [OpenClaw](https://github.com/openclaw/openclaw) or similar
"give an agent a computer" projects, the shape will feel familiar. The two
differences that matter: this is oriented around operating a *product* on a
VPS (deploys, infra, a real running service with real users), not around
being a companion; and its primary interface to the world is a devops
pipeline (git, PRs, CI), not a chat window.

## What it won't do without asking

The autonomy above comes with a default boundary that exists before you've
configured anything. [`AGENTS.md`](./AGENTS.md)'s "Default guardrails"
section is the one home for it — a stop-and-ask list covering irreversible
git operations, destroying data or backups, credential rotation, DNS and
hosting changes, spending money, contacting third parties, and anything with
no concrete rollback. It's read every session, it's in force from the first
one, and your own conventions doc can tighten or extend it but never
silently replaces it. That list isn't restated here; go read it there.

## Before you run `install.sh`

You're about to run a script from a stranger's repo on a box you own, and
then point an AI agent at that box. What that actually involves:

- **Ubuntu or Debian only.** The script refuses to run anywhere else rather
  than guessing at another package manager. On another OS, install the three
  requirements below by hand and skip straight to
  [`STARTUP.md`](./STARTUP.md).
- **It needs root**, via `sudo` (apt installs, plus adding your own user to
  the `docker` group — which it reads from `SUDO_USER`).
- **It pipes two official upstream installers into a shell** — Docker's
  (`get.docker.com`) and `uv`'s (`astral.sh`) — and adds GitHub's own apt
  repository for `gh`. Those, plus the apt repos your box already trusts,
  are the only network calls this repo makes. Nothing here phones home and
  nothing reports to painapple.
- **It hands out no credentials and creates no accounts.** Every token the
  agent eventually uses is one *you* provision and paste into `.env`
  yourself (see [Self-provisioning](#self-provisioning-what-the-agent-needs-and-who-sets-it-up)),
  so the access the agent ends up with is exactly the access you chose to
  give it — not something this repo decides.

The script is short and commented. Read it before running it; that's the
intended way to trust it.

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

1. **Get a VPS you can SSH into**, running Ubuntu or Debian. Any provider
   works. Painapple's own instance runs on OVHcloud; that's not a
   requirement here, just one data point.

2. **Fork `painapple-org/spoor-bootstrap` on GitHub, then clone your own
   fork** onto that VPS (or wherever your harness will run). Don't clone
   upstream directly: this checkout isn't a one-shot installer you throw
   away, it's a repo the agent keeps maintaining afterwards — it opens PRs
   against it for work items that target its own tooling, per
   [`skills/git-pr-conventions`](./skills/git-pr-conventions/SKILL.md) and
   [`skills/work-tracker`](./skills/work-tracker/SKILL.md) — and it can only
   do that if `origin` is a repo you can push to. Any remote you control
   works if you'd rather not fork: create an empty repo, clone this one, and
   repoint `origin` at yours before going further.

   Clone with `git`, not a "Download ZIP": the harness skill symlinks don't
   survive a ZIP.

3. **Read, then run, `sudo ./install.sh`** ([source](./install.sh)) — see
   [Before you run `install.sh`](#before-you-run-installsh) above for what
   it does to the box. It installs Docker, uv and `gh` (skipping any already
   present), and refuses to continue on two things it can't fix for you: an
   `origin` still pointing at upstream, and skill symlinks broken by a ZIP
   download.

4. **Pick and install an agentic harness.** Claude Code, OpenCode, Codex
   CLI, or something else — this repo doesn't prefer one.
   [`AGENTS.md`](./AGENTS.md) holds the harness-agnostic instructions each
   of them should be pointed at, and [`skills/`](./skills/README.md) the
   portable skill definitions — discovered natively by both Claude Code and
   OpenCode, with no per-harness or per-skill wiring to do. See
   [`skills/README.md`](./skills/README.md) for how that's arranged.

5. **Run the harness in this checkout and tell it to read
   [`STARTUP.md`](./STARTUP.md).** That's where the first-boot flow lives:
   the interview (your technical level, who the product is for, work
   tracker, comms channel, autonomy model), writing `.env`, generating this
   deployment's own conventions doc (its path recorded once in
   `CONVENTIONS_DOC_PATH` in `.env`, which is what every skill resolves it
   from), and filling in the skill stubs against your actual answers — including, if you're building for a non-technical
   end-user, the opinionated stack in
   [`skills/product-tech-stack/SKILL.md`](./skills/product-tech-stack/SKILL.md).
   It ends by handing you a self-provisioning shopping list.

6. **Work through that shopping list**, paste the resulting secrets into
   `.env` yourself, and have the agent re-run the specialization step for
   whichever skill files were blocked on an account that now exists.

Everything past that point — actually wiring up the work tracker, the comms
channel, deploy automation, SSH access for whatever automation needs to
reach the box, scheduling — is deliberately left to you and the agent you're
running. This repo gets you to a box with the right tools installed and a
documented starting point; it doesn't hand you a finished agent.

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
until something acts on it. Filling them in is step 5 above, driven by
[`skills/specialize-skills`](./skills/specialize-skills/SKILL.md), and it
runs off the interview answers rather than asking you to edit markdown by
hand. Expect to re-run it, one file at a time, as you work through the
shopping list below and more of the markers become answerable.
[`skills/README.md`](./skills/README.md) is the list of what's there.

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

## Contributing

This repo is public and meant to be forked, diverged from, and contributed
back to. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for what kinds of
changes are welcome and the conventions to follow. MIT licensed — see
[`LICENSE`](./LICENSE).
