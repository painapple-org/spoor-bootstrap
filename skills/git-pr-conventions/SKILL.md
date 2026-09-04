---
name: git-pr-conventions
description: How this agent instance ships code — branch, commit, push, PR, self-merge — plus the worktree-isolation and shared-ref hazards that come with running unattended alongside a human. Read before any git operation that mutates a branch or opens a PR. Ships as a stub for the host/auth-specific parts.
---

# git-pr-conventions

## Status: PARTIAL STUB — needs specialization

Most of this SKILL is real right now: the branch/PR/merge shape and the
concurrency hazards are properties of git and of running unattended, not of
any particular business. The parts marked `TODO(specialize)` depend on the
owner's actual repo, host and auth setup and must be filled in during
first-boot — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md), with the one
exception that the `Auth` section below is filled in earlier than the rest,
for the reason stated there.

The autonomy model and the stop-and-ask list are **not** restated here.
The default stop-and-ask list lives in [`AGENTS.md`](../../AGENTS.md)'s
"Default guardrails" section and is in force at all times. Whatever this
deployment's owner tightened, extended or carved out on top of it during
the first-boot interview is recorded in that deployment's own conventions
doc (see [`STARTUP.md`](../../STARTUP.md) step 6), whose path is
`CONVENTIONS_DOC_PATH` in `.env` — read the variable, then read the file it
names. Never guess that filename or search for it by hunch.

If `CONVENTIONS_DOC_PATH` is empty or names a file that doesn't exist,
first-boot setup hasn't finished; `AGENTS.md`'s default list is then the
whole list, and it applies in full. The same holds for anything the
conventions doc simply doesn't mention.

## The default shipping loop

For routine, reversible work — a bug fix, a config change, a scoped feature
from the work tracker:

1. Branch off the default branch. `TODO(specialize)`: record this
   deployment's branch naming convention, if the owner wants one, and the
   name of the default branch if it isn't `main`.
2. Commit. Include a trailer line in the commit body naming which process
   produced it (same style as `Signed-off-by`), so the history can be read
   back later. The literal trailer text is this deployment's own — it's
   recorded in the conventions doc at `CONVENTIONS_DOC_PATH` in `.env`
   (captured by [`STARTUP.md`](../../STARTUP.md) step 6), not here.
3. Push the branch.
4. Open a PR describing the change and linking the work item.
5. Merge it yourself once the review pass has checked the diff.

The PR exists to give a clean revert point and a reviewable diff, **not** to
gate on human approval. Do not wait for per-change confirmation for routine
work. Rollbacks, not up-front caution, are the safety net — but only inside
the boundary above: [`AGENTS.md`](../../AGENTS.md)'s default guardrails, as
amended by this deployment's conventions doc.

**No AI attribution, anywhere.** No `Co-Authored-By` line naming a model, no
"generated with"/"written by AI" line, in commits, PR bodies, work-item
comments, or any other output. The process trailer in step 2 is a process
marker, not attribution, and is the only thing of its kind that belongs
there.

## Never mutate the primary checkout from an unattended run

This is the single most expensive hazard in this setup, and it is not
hypothetical.

A human may be using the primary checkout interactively at the same moment
a scheduled run fires, and two scheduled runs can fire concurrently. A
`git checkout`/`merge`/`commit` from an unattended session can therefore
leave the tree mid-merge, or commit unresolved conflict markers to the
default branch.

So: **any unattended work that needs to check out a branch, merge, or
commit does it in an isolated git worktree or a fresh scratch clone, never
in the primary checkout.** If your harness offers worktree isolation for
spawned sub-agents, use it. If it doesn't, clone to a scratch path and
remove the clone when finished.

Two consequences worth knowing before they bite:

- **Worktrees of the same repo share refs and config with the primary
  checkout.** A worktree gets its own `HEAD`, index and working tree — it
  does *not* get its own `.git/config`. So changing the `origin` URL or
  adding a credential helper from inside a worktree changes it for the
  primary checkout and every other concurrent worktree too. Use one-off,
  invocation-scoped overrides (`git -c ...`) instead of persisting config.
- **Anything that fast-forwards the default branch locally can race a
  concurrent deploy.** Some conveniences do this silently as a side effect
  of a "just delete the branch" flag. Prefer merging through the hosting
  provider's API (no local checkout involved) and then deleting the merged
  branch through a path that only ever touches the remote — a remote-ref
  delete or an API call — never a local ref delete.
- **Worktree isolation only auto-cleans a worktree with zero changes in
  it.** If your run made real edits and then crashed, the worktree is left
  behind. Remove it as your last action whether the work succeeded or
  failed, and don't rely on any sweep to do it for you.

## Which repo are you even in?

There are at least two repos in play, and they are siblings, not nested:

- **the product repo** at `PRODUCT_REPO_PATH` in `.env` — the thing this
  agent instance exists to build and operate. Almost all work lands here.
- **this bootstrap/pipeline repo** — the agent's own tooling, prompts and
  skills.

Worktree isolation operates against whatever repo the *calling session's*
directory belongs to, so it can only ever reach one of them. A work item
whose real fix is in the agent's own tooling therefore needs the scratch-
clone path instead of the worktree path — that's what the "targets the
agent's own tooling" label in
[`skills/work-tracker`](../work-tracker/SKILL.md) is for. Check the label
before choosing an isolation mechanism, and pass the repo explicitly to any
PR/merge command run from a scratch clone, since the tool can't infer it
from the directory.

**Name the target repo explicitly on every PR/merge command against the
bootstrap repo, too — not only from a scratch clone.** If this checkout is
a *fork* of the upstream template, the CLI resolves the base repo to the
fork's network parent, so an unqualified "open a PR" defaults to opening it
against upstream: a public repo belonging to someone else, which cannot be
merged from here and which publishes this deployment's own specifics in a
public PR. That default is silent and it looks like success. So on every
PR-open and merge command here, name this deployment's own repo (with the
CLI this repo installs: `--repo <owner>/<repo>`, plus `--head
<owner>:<branch>` where the command takes one), and confirm the URL the
command printed names it before merging. Not a fork-only precaution: naming
the repo costs nothing on a non-fork remote and removes the failure mode
entirely.

Also beware: a stray `cd` into another repo earlier in a session can
silently redirect the next isolated spawn there. Know your working
directory before spawning.

**The bootstrap repo is not exempt from the loop above.** First boot writes
real edits into it — the `Auth` section below, and every stub the
specialization pass rewrites — and those ship through a branch and a PR
against whatever repo `origin` points at, exactly like product work
([`STARTUP.md`](../../STARTUP.md) steps 6 and 7). First boot is also the
only time that may happen in the primary checkout, because a human is
sitting there for it; every later re-run is unattended and takes the
scratch-clone path above.

**Know what those edits contain before pushing them anywhere.** This repo
starts as a generic template and stops being one the moment it's
specialized: the `Auth` section below records which account pushes
authenticate as and at what permission level, the section after it lists
this deployment's protected branches, and the tracker and comms-channel
skills record a scope identifier, host specifics and the literal allowlist
of identities permitted to instruct this agent. No credential is among
them — those live in `.env`, which is gitignored, and none of this changes
that — but together they are a precise description of one business's
operational setup, and they are committed here. Where that ends up
readable is entirely a property of `origin`:
[`README.md`](../../README.md)'s "Path to a running instance" is the one
home for that choice, and the short version is that a GitHub fork of a
public template is permanently public while a repo you create yourself can
be private. If a change would put a new class of specific into this repo,
it's worth a sentence to the owner rather than a silent commit.

## Auth

This section is answered **first**, before this deployment's first push —
[`STARTUP.md`](../../STARTUP.md) step 5, not the specialization pass in
step 7. It has to be: every other section here assumes a git identity that
can already reach the remote, so leaving it for the same pass that fills in
branch naming would make the first PR depend on a step that comes after it.
A human is present at that point, which is also the only time an
interactive login is possible at all — later runs are unattended with no
terminal to prompt on. It's *written* there and *shipped* one step later,
for the reason step 6 gives.

`TODO(specialize)` — record, for this deployment:

- Which git remote protocol actually works from an unattended/spawned
  session on this host, and the exact invocation. Do not leave this to be
  rediscovered per session: whichever of HTTPS-with-a-credential-helper or
  SSH works here, write down the working command form and any known
  exception (some hosting providers refuse specific classes of change over
  a token that lacks a specific scope, and only the other protocol works
  for those).
- Which account the pushes authenticate as, and its permission level.
  Note that authenticating to the hosting provider is not the same as
  having write access to the specific repo being pushed to — record that
  the latter was actually verified, not just that a login succeeded, and
  record it **per repo**: both the product repo and this bootstrap repo's
  own `origin`, which are separate repos with separate permissions and are
  both pushed to during first boot. Name what `origin` is here while
  you're at it (a repo the owner created, or a fork of the upstream
  template), since the section above turns on that answer.

  The agent's own account, provisioned by a human, is the end state worth
  getting to, for the RBAC-scoping reason
  [`AGENTS.md`](../../AGENTS.md)'s self-provisioning section gives. It is
  **not** a precondition for pushing at all: the owner's own account is a
  valid answer here in the meantime, and recording that honestly beats
  blocking the first PR on an account nobody has created yet. Swapping in
  the agent's own account once it exists is a re-run of
  [`skills/specialize-skills`](../specialize-skills/SKILL.md) scoped to
  this section.
- **The credential that opens and merges the PR**, which is a separate
  thing from the one that pushes: the push rides the git remote, while the
  PR goes through the hosting provider's API. Record what was verified for
  *that* path too. One credential often serves both, and recording that it
  did is the point — the next session shouldn't have to re-derive whether
  the push working implies the merge will.
- **Whether this remote has a PR mechanism at all.** The loop above assumes
  one. A plain git remote — a bare repo on a box, a self-hosted host with
  no API in use — has no PR object, so "open a PR, merge it yourself" has
  to become something concrete and reviewable instead. Say what it became,
  and say how the default branch gets advanced without the local
  fast-forward the hazard above warns against, since a server-side merge is
  exactly what was avoiding it.

## Protected branches and irreversible git operations

`TODO(specialize)`: list any branch on this deployment that must never be
force-pushed, and whether a mechanical guard exists (a wrapper that refuses
a force-push regardless of caller is worth far more than a documented rule).

Force-pushing, deleting branches, deleting volumes or backups, and
`git reset --hard` over someone else's work are stop-and-ask by default —
they're on [`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list, which
holds unless this deployment's conventions doc explicitly says otherwise.
Read that doc at `CONVENTIONS_DOC_PATH` in `.env` for any deltas; silence
there means the default stands.
