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

Four things, and nothing more:

- **[`install.sh`](./install.sh)** — mechanical OS-level bootstrap. It
  installs three tools and sanity-checks the checkout. It asks no
  questions and writes no config.
- **[`STARTUP.md`](./STARTUP.md)** — the prompt you paste into your agentic
  harness for the first run. The agent interviews you, writes `.env`,
  generates this deployment's own conventions doc, fills in the skill
  files, and hands you a shopping list — identities to provision, open
  decisions, and work it couldn't finish.
- **[`skills/`](./skills/README.md)** — harness-agnostic instructions the
  agent operates from, with [`AGENTS.md`](./AGENTS.md) as the entrypoint
  that ties them together.
- **[`prompts/`](./prompts/README.md)** — the home for the per-stage
  pipeline prompts the agent runs on, plus the template each one starts
  from. It ships with no stage prompt in it, deliberately: which stages your
  deployment runs is one of the things the first boot decides, and writing
  those files is part of it.

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
configured anything: a stop-and-ask list the agent reads every session,
in force from the first one, which your own conventions doc can tighten or
extend but never silently replaces.

What's actually on that list is deliberately not restated here — not even
in summary, because a partial summary of a security boundary is the worst
version of it. [`AGENTS.md`](./AGENTS.md)'s "Default guardrails" section is
its one home; go read it there.

## Before you run `install.sh`

You're about to run a script from a stranger's repo on a box you own, and
then point an AI agent at that box. What that actually involves:

- **apt-based Linux only** — Ubuntu, Debian, or a derivative that declares
  one of them in `/etc/os-release`'s `ID_LIKE` (Linux Mint, Pop!_OS,
  Raspberry Pi OS, Devuan and friends). The script refuses to run anywhere
  else rather than guessing at another package manager, and names both
  fields it read when it does. On another OS, install the three requirements
  below by hand and skip straight to [`STARTUP.md`](./STARTUP.md).
- **It needs root**, either as root directly or via `sudo` (apt installs,
  plus adding a user to the `docker` group). It stops immediately if it has
  neither. Run under `sudo`, it adds the invoking user to that group. Run as
  root directly it can't: there's no invoking user to infer, and the account
  that will run the agent may not exist yet. In that case add it yourself
  once it does — `usermod -aG docker <account>` — or every docker command
  from that account will need `sudo`.
- **Docker-group membership is root-equivalent access to this host**, and
  that is what the bullet above is granting, so decide it knowingly rather
  than reading it as a convenience. Anyone who can talk to the docker
  socket can start a container that bind-mounts `/` and `chroot` into it,
  which is full root on the box by a different route — no `sudo` password,
  no sudoers entry, nothing to audit. This is a well-known property of
  Docker's architecture, not a flaw in this script; it is the reason
  `install.sh` runs this step at all, since a containerized product the
  agent deploys needs the socket. But it means the account you point the
  agent at effectively has root here from install time, before any
  guardrail in [`AGENTS.md`](./AGENTS.md) is in force. If that isn't
  acceptable for your box, the answer is a rootless Docker setup (which
  `install.sh` detects the absence of a `docker` group for and reports
  rather than fighting), or a host you're willing to hand over entirely.
- **It runs two upstream installer scripts as root, unverified** —
  Docker's (`get.docker.com`) and `uv`'s (`astral.sh`) — and adds GitHub's
  own apt repository for `gh`. Those, plus the apt repos your box already
  trusts, are the only network calls this repo makes. Nothing here phones
  home and nothing reports to painapple. Be precise about what is and
  isn't protected here, because the two are easy to conflate:
  - `install.sh` downloads each script to a tempfile and *then* executes
    it, rather than piping `curl` straight into `sh`. That protects
    against one failure mode only: a transfer that dies partway can't hand
    `sh` a truncated script that runs half of itself.
  - It does **not** verify what was downloaded — no pinned checksum, no
    signature check. So if either endpoint were compromised, or the fetch
    were MITM'd past TLS, you would be executing whatever it served, as
    root, and this script would not notice. What you are trusting is
    Docker's and Astral's own distribution security, plus your transport,
    exactly as you would be piping into `sh`. The download-then-run
    pattern buys robustness, not trust.
  - As a partial mitigation it logs the `sha256sum` of each script it
    downloaded before running it, so you at least have a record of what
    executed on your box and can compare two installs. That's an audit
    trail after the fact, not a check that stops anything.
  - The keyring for `gh` is fetched the same unverified way, and what it
    leaves behind outlives the script: an apt trust anchor plus a source
    entry, both written under `/etc/apt`. The two installers above execute
    once; this one is a standing grant, so that repository can install
    packages as root on every later `apt-get upgrade` too. Delete both
    files if you'd rather get `gh` some other way — `install.sh` skips the
    whole step when `gh` is already on PATH.
  - `get.docker.com` is Docker's own convenience script, and
    [Docker's documentation states it is not recommended for production
    environments](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script).
    It's here because it is the shortest path to a working daemon on a
    fresh box. If this box matters, install Docker from its apt repository
    per those same docs and let `install.sh` skip the step — it does skip
    it when `docker` is already on PATH.
- **It hands out no credentials and creates no accounts.** Every token the
  agent eventually uses is one *you* provision and paste into `.env`
  yourself (see [Self-provisioning](#self-provisioning-what-the-agent-needs-and-who-sets-it-up)),
  so the access the agent ends up with is exactly the access you chose to
  give it — not something this repo decides.

The script is short and commented. Read it before running it; that's the
intended way to trust it.

## Hard requirements

These are the three things `install.sh` sets up **on the box, for the agent
itself to operate**:

- **Docker** — everything the agent builds and runs is containerized.
  Required on every deployment.
- **uv** — Python dependency management for whatever tooling the agent
  writes for itself. Required on every deployment.
- **GitHub CLI (`gh`)** — required for the two GitHub-shaped remotes in
  [Path to a running instance](#path-to-a-running-instance) below (a private
  repo of your own, or a fork). On those the agent operates through
  branches, PRs and the GitHub API, and `gh` is how it authenticates and
  acts. On the third shape — a plain git remote with no GitHub-style host
  behind it — there is no such API to call and nothing for `gh` to
  authenticate against, so it isn't a requirement there: plain `git` plus
  the review-branch protocol that item points at are what that shape runs
  on.
  `install.sh` installs the binary either way, since it asks no questions
  and so cannot know which shape you picked. It never logs it in:
  authenticating needs a decision (which account, which protocol) and an
  interactive prompt, both of which belong to the first-boot flow.
  [`STARTUP.md`](./STARTUP.md)'s own step 5 is where a working git identity
  gets established and verified, before anything tries to push — and where
  the plain-remote case skips the login instead.

This is the agent's own host tooling, not a statement about what the
product it builds is written in. That's a separate decision with its own
home in
[`skills/product-tech-stack/SKILL.md`](./skills/product-tech-stack/SKILL.md),
which applies only when the product targets a non-technical end-user. Some
entries appear in both because the agent needs them locally *and* that
stack requires them for the product — the overlap is real, not a copy of
one list into the other.

Everything else — which agentic harness you run, which work tracker you
use, which chat platform you wire up, which email provider you pick — is a
choice this repo asks you to make, not something it assumes for you.

## Path to a running instance

**See a worked example first, if you'd rather read than run:**
[`docs/example-walkthrough.md`](./docs/example-walkthrough.md) takes one
fictional small business — a five-person coffee roastery with an inherited,
half-maintained wholesale ordering portal — through the whole of item 5 in
the list below: the interview with plausible answers, the autonomy negotiation, the
resulting `.env`, an excerpt of the conventions doc it produces, and one
skill stub shown before and after specialization. It's illustrative, not a
default; every file it quotes remains the home for its own content.

1. **Get a VPS you can SSH into**, running Ubuntu, Debian or an apt-based
   derivative of either. Any provider works. Painapple's own instance runs
   on OVHcloud; that's not a requirement here, just one data point.

2. **Put this checkout on a git remote you control, and pick which shape
   that remote takes.** There are three supported shapes, all covered in
   this item: a new private repo of your own (the recommended default), a
   GitHub fork, or a plain git remote with no GitHub-style host behind it
   at all. They differ in what they cost you, not in whether they work.
   Read to the end of this item before setting `origin`.

   For the default: clone this repo onto that VPS (or wherever your harness
   will run), create an empty private repo on your own account, and repoint
   `origin` at it before going further. Create that empty repo in the GitHub
   web UI: `gh` isn't on the box until item 3, so the one-command version
   (`gh repo create --private --source=. --remote=origin --push`) isn't
   available to you yet at this point.

   ```
   git clone https://github.com/painapple-org/spoor-bootstrap.git
   cd spoor-bootstrap
   git remote set-url origin <the URL of your own new private repo>
   git push -u origin HEAD
   ```

   **That last push is yours, on your own existing git credentials.** It
   happens before `gh` is even on the box (item 3) and well before the
   agent establishes a git identity of its own
   ([`STARTUP.md`](./STARTUP.md) step 5), so whatever `git` on this box
   already has — an SSH key your host account holds, a personal access
   token in a credential helper — is what authenticates it. That's a
   separate thing from `gh`'s own login, which comes later and is the
   agent's. If the push is refused, the fix is at the OS/git level here,
   not something a later step resolves for you.

   Two separate reasons it has to be a remote you own, and not upstream:

   - **The agent keeps maintaining this checkout.** It isn't a one-shot
     installer you throw away — the agent opens PRs against it for work
     items that target its own tooling, per
     [`skills/git-pr-conventions`](./skills/git-pr-conventions/SKILL.md)
     and [`skills/work-tracker`](./skills/work-tracker/SKILL.md), starting
     with the first boot itself. That needs an `origin` you can push to.
   - **Once specialized, this checkout holds real operational detail about
     your business.** Filling in the skill stubs (item 5 below) writes down
     things like who the people on your comms channel are and which of
     them is deliberately excluded from instructing the agent, which
     account its pushes authenticate as and at what permission level, your
     tracker's scope and host specifics, and which of your branches must
     never be force-pushed. None of that is a credential — actual secrets
     live in `.env`, which is gitignored, and so does the literal
     allowlist of identities permitted to instruct the agent
     (`COMMS_ALLOWLIST`) — but all of it is identifying, operational detail
     about a specific deployment, and it gets committed here.

   Pulling later template updates doesn't need a fork: a private copy can
   add upstream as a second remote (`git remote add upstream <this repo's
   URL>`) and fetch from it. What a fork adds on top is GitHub's own
   compare/PR-across-the-network machinery, which matters mainly if you
   intend to contribute changes back — see
   [`CONTRIBUTING.md`](./CONTRIBUTING.md), and note that a fork made for
   that purpose is best kept separate from the checkout your agent
   specializes and operates from.

   **Forking on GitHub is an opt-in alternative, with a real tradeoff.** A
   fork gets you that machinery and a one-click setup. But **a fork of a
   public repo cannot be made private** — GitHub permanently keeps it
   public — so everything in the "Once specialized, this checkout holds
   real operational detail about your business" bullet ends up publicly
   readable, forever, along with the PRs that shipped it.
   Fork only if you've read that sentence and are fine with it. If you fork
   and later change your mind, a fork can't be converted: you have to
   create a fresh private repo, push to it, and delete the fork — and
   anything already pushed to the fork has to be treated as public.

   **A plain git remote is the third supported shape, and it's the right
   answer if you don't have a GitHub-style host at all.** A bare repo on a
   box you own (`git init --bare` and an SSH path), or a self-hosted server
   whose API nobody has turned on, works as `origin` for both this checkout
   and your product repo. Nothing in the setup requires GitHub as such.

   What it costs is the pull request, which several things here assume
   exists: a remote like that has no PR object. That is already answered
   rather than left to you —
   [`skills/git-pr-conventions`](./skills/git-pr-conventions/SKILL.md)'s
   "Shipping on a remote with no PR mechanism" section is a complete
   git-only default for this shape (a named review branch, a diff you read
   in a terminal, a merge commit that records the verdict), and
   [`STARTUP.md`](./STARTUP.md) step 5 has the agent tell you it's using it
   and then carry on rather than wait for you to approve it. What you
   actually give up is the web review UI, not the reviewable diff or the
   revert point. Note too that on this shape the privacy tradeoff in the
   fork paragraph above doesn't apply at all: it's your box.

   Whichever of the three you pick, clone with `git`, not a "Download ZIP" — see
   [`skills/README.md`](./skills/README.md) for what the harness skill
   symlinks are and the one thing that breaks them.

3. **Read, then run, `sudo ./install.sh`** ([source](./install.sh)) — see
   [Before you run `install.sh`](#before-you-run-installsh) above for what
   it does to the box. It installs Docker, uv and `gh` (skipping any already
   present), plus the apt packages needed to fetch them at all (`curl`, a CA
   bundle, `git`) on an image minimal enough not to have them. It then
   checks the docker daemon is actually reachable, starting it via systemd
   if it isn't — and where there's no systemd to start it with (typical
   inside a container), it says so as an explicit NOT VERIFIED rather than
   claiming a check it couldn't run. It refuses to continue on two
   things it can't fix for you: an `origin` whose URL is still literally
   upstream's, and skill symlinks broken by a ZIP download. That origin
   check is a URL comparison and nothing more — it cannot tell whether you
   can actually *push* to whatever `origin` names, since `gh` isn't logged
   in yet at that point; proving write access is
   [`STARTUP.md`](./STARTUP.md) step 5's job. Re-running it is safe — every
   step is skipped if it's already done. It does not log `gh` in; that
   happens in the first-boot flow, item 5 of this list.

4. **Pick and install an agentic harness.** Claude Code, OpenCode, Codex
   CLI, or something else — this repo doesn't prefer one.
   [`AGENTS.md`](./AGENTS.md) holds the harness-agnostic instructions each
   of them should be pointed at, and [`skills/`](./skills/README.md) the
   portable skill definitions; that file's "How harnesses discover these"
   section explains how the same skill content reaches whichever harness
   you picked.

5. **Run the harness in this checkout and tell it to read
   [`STARTUP.md`](./STARTUP.md).** That's where the first-boot flow lives:
   the interview (whose questions are enumerated in
   [`AGENTS.md`](./AGENTS.md)), agreeing on an autonomy model, writing
   `.env`, getting `gh` logged in and proving a push actually works — to
   the product repo *and* to this checkout's own `origin`, since the
   first-boot flow ships its own edits here through a PR too, or through
   the review-branch protocol on a remote that has no PRs (expect
   to be walked through `gh auth login` here, with whichever GitHub account
   you want the agent pushing as for now — your own is fine to start),
   generating this deployment's own conventions doc (its path
   recorded once in `CONVENTIONS_DOC_PATH` in `.env`, which is what every
   skill resolves it from), and specializing the skill stubs in
   [`skills/`](./skills/README.md) against your actual answers. That last
   part is also where [`prompts/`](./prompts/README.md) stops being empty:
   deciding which pipeline stages your deployment runs and writing one
   substantial prompt file per stage kept is the largest single deliverable
   of the pass. It ends by handing you a self-provisioning shopping list.

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
instructions this agent operates from. Most ship as **stubs**: generic
where a fact is universal, and marked with a literal `TODO(specialize)`
everywhere the real answer depends on *your* tracker, channel, host and
product. Nothing here guesses those answers on your behalf, and the
reasoning for that is stated once, in
[`skills/specialize-skills`](./skills/specialize-skills/SKILL.md)'s "Why
the stubs exist in this shape".

Filling them in is item 5 of "Path to a running instance" above, driven by
that same SKILL, and it runs off
the interview answers rather than asking you to edit markdown by hand.
Expect to re-run it, one file at a time, as you work through the shopping
list below and more of the markers become answerable. See
[`skills/README.md`](./skills/README.md) for which skills exist and which
of them are stubs.

## Self-provisioning: what the agent needs, and who sets it up

Once running, the agent instance you've bootstrapped will need its own
identity on several platforms, separate from yours — and **a human
provisions those; the agent does not register itself for them.** It's a
shopping list handed to you at the end of the first boot, not a capability
the agent exercises on its own.

What's actually on that list, and why the identity has to be the agent's
own rather than reused from your personal accounts, is stated once in
[`AGENTS.md`](./AGENTS.md)'s "Self-provisioning: the shopping list" — the
same wording the agent itself reads.

## Contributing

This repo is public and meant to be copied, diverged from, and contributed
back to. Contributing back is the one case where a GitHub fork is the right
mechanism — a fork you send PRs from, not the checkout your own instance
specializes itself in (item 2 above says why). See
[`CONTRIBUTING.md`](./CONTRIBUTING.md) for what kinds of changes are
welcome and the conventions to follow. MIT licensed — see
[`LICENSE`](./LICENSE).
