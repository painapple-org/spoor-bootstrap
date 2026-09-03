---
name: git-pr-conventions
description: How this agent instance ships code — branch, commit, push, PR, self-merge — plus the worktree-isolation and shared-ref hazards that come with running unattended alongside a human. Read before any git operation that mutates a branch or opens a PR. Ships as a stub for the host/auth-specific parts.
---

# git-pr-conventions

## Status: partially generic, partially STUB

Most of this SKILL is real right now: the branch/PR/merge shape and the
concurrency hazards are properties of git and of running unattended, not of
any particular business. The parts marked `TODO(specialize)` depend on the
owner's actual repo, host and auth setup and must be filled in during
first-boot specialization — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

The autonomy model and the stop-and-ask list are **not** restated here.
They are agreed with the owner during the first-boot interview and recorded
in that deployment's own conventions doc (see
[`STARTUP.md`](../../STARTUP.md) step 5). Read that file; do not assume a
default list from this template.

## The default shipping loop

For routine, reversible work — a bug fix, a config change, a scoped feature
from the work tracker:

1. Branch off the default branch. `TODO(specialize)`: record this
   deployment's branch naming convention, if the owner wants one, and the
   name of the default branch if it isn't `main`.
2. Commit. Include a trailer line in the commit body naming which process
   produced it (same style as `Signed-off-by`), so the history can be read
   back later.
3. Push the branch.
4. Open a PR describing the change and linking the work item.
5. Merge it yourself once the review pass has checked the diff.

The PR exists to give a clean revert point and a reviewable diff, **not** to
gate on human approval. Do not wait for per-change confirmation for routine
work. Rollbacks, not up-front caution, are the safety net — but only inside
whatever boundary the owner actually agreed to.

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

Also beware: a stray `cd` into another repo earlier in a session can
silently redirect the next isolated spawn there. Know your working
directory before spawning.

## Auth

`TODO(specialize)` — record, for this deployment:

- Which git remote protocol actually works from an unattended/spawned
  session on this host, and the exact invocation. Do not leave this to be
  rediscovered per session: whichever of HTTPS-with-a-credential-helper or
  SSH works here, write down the working command form and any known
  exception (some hosting providers refuse specific classes of change over
  a token that lacks a specific scope, and only the other protocol works
  for those).
- Which account the pushes authenticate as, and its permission level. This
  should be the agent's own account, provisioned by a human, not the
  owner's personal one.

## Protected branches and irreversible git operations

`TODO(specialize)`: list any branch on this deployment that must never be
force-pushed, and whether a mechanical guard exists (a wrapper that refuses
a force-push regardless of caller is worth far more than a documented rule).

Force-pushing, deleting branches, deleting volumes or backups, and
`git reset --hard` over someone else's work are the archetypal
stop-and-ask items. Whether they're on *this* deployment's list is the
owner's call, recorded in the deployment conventions doc — go read it.
