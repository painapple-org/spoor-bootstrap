# Contributing to spoor-bootstrap

This repo is a template. It's public because it's more useful copied than
admired, and contributions back are welcome — especially from anyone who
has actually run it on a box and hit something wrong.

Note the asymmetry before you fork: a fork is the right mechanism for
sending changes *back here*, and not the one to run your own instance on,
because a fork of a public repo is permanently public and a specialized
checkout holds real operational detail about its deployment.
[`README.md`](./README.md)'s "Path to a running instance" owns that
choice, and note what it actually says: a fork is a supported shape for
your own instance with that cost attached, not a shape that doesn't work.
If you do both, keep them as two separate repos.

It's also an early draft (see [`README.md`](./README.md)), so "this is
wrong / misleading / missing" is a perfectly good contribution on its own.
You don't need a fix to open an issue.

## How to propose a change

1. **Open an issue first for anything non-obvious.** Not as a gate — as a
   way to avoid two contributors rewriting the same file in incompatible
   directions. For a typo, a dead link, or a clearly wrong fact, skip
   straight to a PR.
2. **Fork, branch, PR.** One logical change per PR. A PR that fixes a bug
   *and* restructures a doc is two PRs.
3. **Say what you actually ran.** If your change touches
   [`install.sh`](./install.sh), say which OS and version you ran it on and
   whether it got to the end. If it touches a skill file, say which harness
   read it.
4. **Get CI green.** Every PR runs the jobs in
   [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) — shellcheck, a
   real execution of `install.sh` in throwaway containers (root and
   sudo-user, asserting docker/uv/gh end up runnable and that docker can
   actually run a workload), a markdown link check across every tracked
   `.md`, a consistency check on [`skills/`](./skills/README.md) and the
   docs that index it, and an integrity check on the harness skill
   symlinks. A dead link in a doc fails the build, which is intentional —
   so does a stub whose `Status:` heading disagrees with its own
   `TODO(specialize)` markers, a skill missing from
   [`skills/README.md`](./skills/README.md)'s index, and a "`STARTUP.md`
   step N" reference pointing at a step that no longer exists.
5. **It gets squash-merged.** Your commits don't need to be tidy; your PR
   description does.

## Who reads your PR

Worth knowing before you spend an evening on one, because it isn't the
usual answer: this repo is maintained the way it tells you to run your own
instance. The agent instance operating [painapple](https://painapple.nl) —
the reference deployment [`README.md`](./README.md) says this repo was
extracted from — is what reviews and squash-merges here, through the same
branch/PR/self-merge loop
[`skills/git-pr-conventions`](./skills/git-pr-conventions/SKILL.md)
describes. Its human owners are the escalation path, not a review gate in
front of every merge.

What that means for you, concretely:

- Expect an actual argument about the diff rather than a rubber stamp, and
  expect the conventions below to be quoted back at you.
- If something needs a human — the project's direction, licensing, or
  anything the agent's own guardrails
  ([`AGENTS.md`](./AGENTS.md)'s "Default guardrails") stop it on — say so
  in the PR and it gets escalated to one.
- No outside contribution has come in yet, so there's no track record here
  to judge this by. Every merged PR so far is the maintaining instance's
  own work on its own template.

## What's welcome

- **OS support for `install.sh`.** It currently refuses anything that isn't
  apt-based, on purpose, and says so in its own failure message. Adding a
  package manager is the most obviously useful contribution here.
- **Fixes to wrong, stale or dead facts** anywhere in the docs — including
  broken links and instructions that don't match what the code does.
- **Real-world corrections to the skill stubs**, where you found the
  generic half is actually wrong rather than merely incomplete.
- **A work-tracker adapter**, or a correction to an existing one — notes on
  mapping the tracker-agnostic contract onto a real tracker's API. See
  [`skills/work-tracker/adapters/README.md`](./skills/work-tracker/adapters/README.md),
  which describes the shape and what a correction is worth. Verified-against-
  the-real-API beats plausible here; mark anything you couldn't check.
- **A new skill** that is genuinely universal across deployments — see
  [`skills/README.md`](./skills/README.md) for what belongs in one.
- **Harness support**, if you got this working under a harness that isn't
  Claude Code or OpenCode and it needed something the repo doesn't have.

## What's probably not welcome

- **Filling in a `TODO(specialize)` marker with a specific value.** Those
  markers exist for each deployment to answer for itself; a value that's
  right for your tracker is a wrong value shipped to everyone else's.
- **A stage prompt file in [`prompts/`](./prompts/README.md).** That
  directory ships with the template and no stage prompt, deliberately: which
  stages a deployment runs is a per-deployment decision, and a prompt names
  that deployment's tracker states, labels and test command. A pre-written
  one is a confident wrong instruction obeyed on every scheduled run — the
  same class of thing as filling in a `TODO(specialize)` marker above.
  [`prompts/README.md`](./prompts/README.md) owns that reasoning. Fixes to
  [`prompts/STAGE_TEMPLATE.md`](./prompts/STAGE_TEMPLATE.md)'s skeleton, or
  to that README's per-stage notes, are welcome — an actual `refine.md` is
  not.
- **Working integration code for one particular work tracker, comms channel
  or host.** The repo deliberately ships none — reference notes an agent
  reads (the adapters above), yes; a client library or wired-up API call,
  no. That's the whole design, not an omission: see the "not a fork of any
  specific company's private agent setup" point in
  [`README.md`](./README.md), and "a SKILL is instructions an agent reads,
  not a library it imports" in
  [`skills/README.md`](./skills/README.md#what-belongs-in-a-skill-here).
- **Scheduling mechanics** (cron files, systemd units, harness schedulers).
  Explicitly out of scope per
  [`skills/README.md`](./skills/README.md#what-belongs-in-a-skill-here).
- **Marketing copy.** This thing is early and the docs say so. Please keep
  it that way until it isn't.
- **Large speculative restructuring** ahead of anyone needing it. See the
  "no state that isn't real right now" principle below.

## Conventions this repo already follows

These aren't new rules for contributors — they're what the existing files
do, and a PR that breaks one will get asked to change.

### Every fact has exactly one home

Named as such in [`skills/README.md`](./skills/README.md). A copied fact is
indistinguishable from a true one right up until it's wrong, and by then
the copy is what gets acted on. So: link to the file that owns a fact,
don't restate it. [`CLAUDE.md`](./CLAUDE.md) is the worked example — it's a
pointer at [`AGENTS.md`](./AGENTS.md) and explains in the file itself why
it isn't a copy.

This applies hardest to prose about code you just wrote. Every number,
path, flag and filename in that prose is a copy of something with an owner.
Name the owner, or leave it out.

### No state that isn't real right now

Also named in
[`skills/specialize-skills/SKILL.md`](./skills/specialize-skills/SKILL.md#rules-for-what-you-write),
as one of the rules the specialization pass writes under. No placeholder for
something that doesn't exist yet, and no legacy scaffolding for something
that's gone. A plausible-looking placeholder value is indistinguishable
from a real one until something acts on it — which is why unanswerable
gaps carry a literal `TODO(specialize)` marker rather than a confident
guess. Git holds both directions; add config when the thing it configures
actually exists.

Corollary: a decision to remove something isn't done until the code is
gone. Don't leave a note saying a file is dead.

### Fail loudly, never quietly

[`install.sh`](./install.sh) is the model: `set -euo pipefail`, a `fail()`
helper that prints a real explanation and exits non-zero, and an explicit
refusal on an unsupported OS instead of a best-effort guess. No `|| true`
that swallows a failure, no defaulting past a missing value. Quietly broken
is worse than a crash, because it leaves no handle to grab.

### Shell scripts

- `bash` with `set -euo pipefail`, tab-indented, and `shellcheck`-clean at
  the severity CI enforces — see the `shellcheck` job in
  [`.github/workflows/ci.yml`](./.github/workflows/ci.yml), which is the one
  home for that bar.
- Use the existing `log()` / `fail()` helpers rather than bare `echo`.
- Every install step is idempotent: check whether the tool is already
  present, skip with a message if so, and verify it's on `PATH` after
  installing.
- A top-of-file comment block explaining the script's scope and what it
  deliberately does *not* do.

### Markdown, skill and prompt files

- Prose hard-wrapped at roughly 76 columns, matching the existing files.
- A `SKILL.md` opens with YAML frontmatter carrying `name` and a
  `description` that says when to read it — see any file under
  [`skills/`](./skills/README.md).
- A skill that still has `TODO(specialize)` markers also carries a
  `## Status: STUB — needs specialization` heading, removed when the last
  marker in it goes. One variant is allowed, for a file whose unmarked half
  is genuinely usable as shipped rather than a placeholder:
  `## Status: PARTIAL STUB — needs specialization`, followed by a sentence
  saying which parts are real now and which wait on specialization. Nothing
  else — a third phrasing is what makes the heading unskimmable.
- [`prompts/STAGE_TEMPLATE.md`](./prompts/STAGE_TEMPLATE.md) is a skeleton
  to be copied per stage, not a document to be completed here: every value
  in it is an angle-bracketed `<...>` placeholder naming what a deployment
  has to answer, and its numbered sections are the bones
  [`prompts/README.md`](./prompts/README.md) refers to per stage. A change
  that adds or removes a section changes what every stage prompt is expected
  to contain, so it belongs with the corresponding change to that README's
  per-stage notes in the same PR. Don't replace a `<...>` with a concrete
  value to make the template read better — that's the same failure as
  filling in a `TODO(specialize)` marker.
- **Harness-agnostic.** Nothing under `skills/` may assume a particular
  agentic harness's tool syntax, config format or file paths. If it only
  makes sense under one harness, it doesn't belong there.

### Comments and docs describe the current state

No changelog comments, no dated "changed X because Y", no issue or PR
numbers in the files. Git history and PR descriptions are the historical
record. A comment that narrates change goes stale the moment the code
moves.

## Licensing

Contributions are made under the repo's [MIT license](./LICENSE). By
opening a PR you're agreeing your contribution can ship under it.
