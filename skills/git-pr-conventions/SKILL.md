---
name: git-pr-conventions
description: How this agent instance ships code — branch, commit, push, PR, self-merge — including the review-branch protocol that replaces the PR on a plain git remote that has none, plus the worktree-isolation and shared-ref hazards that come with running unattended alongside a human. Read before any git operation that mutates a branch or opens a PR. Ships as a stub for the host/auth-specific parts.
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

   **A repo that was created empty has no default branch to branch off**,
   and won't until something commits to it — a first boot that creates the
   product repo hits this on its very first change. There is nothing to
   branch *from* there, so create the branch, commit onto it, and let the
   merge in step 5 be what brings the default branch into existence.
   Don't treat the absence as an error and don't route around it by
   committing straight to the default branch that doesn't exist yet. One
   mechanical consequence, worth knowing before it costs a confusing
   failure: pushing at a branch that does not exist on the remote yet
   requires the fully-qualified destination refspec
   (`HEAD:refs/heads/<name>`). The unqualified `HEAD:<name>` form is
   resolved by matching an existing remote ref, so it fails outright
   against a repo where that ref isn't there.
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

Steps 4 and 5 assume the remote has a PR object to open and a server-side
merge to trigger. On a plain git remote it doesn't — "Shipping on a remote
with no PR mechanism" below is the default that replaces those two steps,
and nothing else in the loop changes.

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

## Shipping on a remote with no PR mechanism: the review-branch protocol

This is the **default** on the third remote shape — a bare repo on a box
the owner runs, or a self-hosted server whose API nobody has turned on (see
[`README.md`](../../README.md)'s "Path to a running instance" for the three
shapes). It is not a stub and not a question to bring the owner: it works
with nothing but `git` on both ends, so it is available the moment a remote
is reachable at all. Say you're using it, then use it. If the owner wants
something different, that's a delta they record in the `Auth` section
below — the absence of an answer there means this protocol is what runs.

It does not apply to a remote that *has* a PR mechanism. There, use the
shipping loop above unchanged: a real PR gives a review UI, CI checks and a
server-side merge, all of which this protocol only approximates.

**1. Push the work as a review branch instead of opening a PR.**
`review/<slug>`, where `<slug>` is the same identifier the branch would
otherwise have carried (this deployment's branch naming convention is in
the conventions doc at `CONVENTIONS_DOC_PATH`). The `review/` prefix is the
whole signal: a branch under it is a change asking to be reviewed, and its
existence on the remote is the PR-open event. Nothing else marks it, so
don't push work-in-progress there.

**2. The reviewer inspects it with `git` alone.** From a scratch clone or a
fetched worktree — never the primary checkout — against the default branch
(its name is in the conventions doc):

- `git fetch origin`
- `git log --oneline <default>..origin/review/<slug>` — the commits, i.e.
  the PR's commit tab.
- `git diff --stat <default>...origin/review/<slug>` — which files, and how
  much. **Three dots, not two**: three diffs against the merge base, which
  is what a PR shows. Two dots diffs against the default branch's current
  tip and so mixes in everything that landed there meanwhile, reading as
  though this change reverted it.
- `git diff <default>...origin/review/<slug>` — the diff itself.

The reviewing session reads that diff on its own merits, exactly as it
would read a PR, and it is a *different* session from the one that pushed
the branch — that independence is the point of the pipeline stage split
(see [`skills/work-pipeline`](../work-pipeline/SKILL.md)) and it survives
the absence of a PR object untouched.

**When the reviewer is the human owner, send the commands, not a summary.**
Paste the four lines above with `<slug>` and the branch name already
substituted, over this deployment's comms channel, so they can copy one
line into a terminal. For a non-technical owner, lead with the `--stat`
output inline and the one-line description of what changed, and offer the
full `git diff` as the follow-up rather than pasting it unasked.

**3. Run the tests before merging — that's what stands in for CI.** A
remote with no PR API generally has no hosted CI runner either, so the
"self-merge once CI is green" convention becomes "self-merge once this
deployment's own test command passes in the scratch clone". Same gate, same
verdict: a red run blocks the merge exactly as a red check would. What that
command is belongs to the deployment, not here — the conventions doc at
`CONVENTIONS_DOC_PATH` and
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md) own it. If
there is no test suite yet, say so in the merge commit (step 4) rather than
implying a check that didn't run.

**4. Approval is recorded as the merge commit.** Merge in the scratch
clone, always `--no-ff`:

```
git merge --no-ff origin/review/<slug>
```

`--no-ff` even when a fast-forward is possible. The merge commit *is* the
approval record and the revert point — the two things the PR was actually
buying — and without it a fast-forwarded review branch leaves no single
commit to `git revert -m 1`. Its body carries the verdict: what was
reviewed, that the tests passed (or that there are none yet), and the same
process trailer every other commit here carries. `git log --merges` then
reads back as the review history. Don't add a sibling approvals file or a
`reviews/` directory in the tree: that's a second home for a fact git
already owns, and it drifts.

**Rejection is not recorded in git at all**, because nothing gets merged.
It goes in the work item, which is the one home for work-item state (see
[`skills/work-tracker`](../work-tracker/SKILL.md)). Then either fix it
forward with more commits on the same review branch and re-review, or drop
the branch per step 6. A review branch that was never merged and then
deleted is a rejected change, and the tracker says why.

**5. Advance the default branch by pushing from the scratch clone.** The
hazard section above forbids fast-forwarding the *shared* default ref, and
there is no server-side merge here to avoid it with. A scratch clone is the
way out: unlike a worktree, a clone has its own refs and its own config
entirely, so checking out and merging the default branch there touches
nothing the primary checkout or a concurrent deploy can see. Merge there,
then `git push origin <default>`. The primary checkout picks the change up
on its next fetch, never mid-operation.

**A rejected push here is the concurrency check working, not an error.** If
something else advanced the default branch while you were reviewing, git
refuses the push as non-fast-forward — the same condition GitHub calls
"this branch is out of date". Fetch, re-merge onto the new tip, re-run the
tests, push again. **Never force-push to resolve it**; that's on the
stop-and-ask list in [`AGENTS.md`](../../AGENTS.md) and it would silently
drop whatever landed.

**6. Delete the review branch on the remote only.**
`git push origin --delete review/<slug>` — a remote-ref delete, never a
local ref delete, per the hazard section above. The merge commit from step
4 is the durable record; the branch was only ever the request.

**What triggers a deploy from that push** is
[`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s subject,
not this file's. Worth knowing that a bare repo's own `post-receive` hook
is a real option on this shape, since there's no hosted CI to do it.

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
be private — and that on a plain git remote (a bare repo on a box the owner
runs, a self-hosted server with no API in use) the tradeoff doesn't arise at
all, since it's their own box. If a change would put a new class of specific
into this repo, it's worth a sentence to the owner rather than a silent
commit.

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
  you're at it (a repo the owner created, a fork of the upstream template,
  or a plain git remote with no hosting provider behind it — a bare repo on
  a box they own, a self-hosted server with no API in use), since the
  section above turns on that answer.

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
- **Whether this remote has a PR mechanism at all.** The shipping loop
  assumes one. A plain git remote — a bare repo on a box, a self-hosted
  host with no API in use — has no PR object, and "Shipping on a remote
  with no PR mechanism" above is what runs instead. Record which of the two
  applies here, and on the no-PR shape record only the *deltas* the owner
  asked for on top of that protocol: it is the default in full, so there is
  nothing to write down when they simply accepted it.

## Protected branches and irreversible git operations

`TODO(specialize)`: list any branch on this deployment that must never be
force-pushed, and whether a mechanical guard exists (a wrapper that refuses
a force-push regardless of caller is worth far more than a documented rule).

Which git operations are stop-and-ask by default is deliberately not listed
here, not even in part: [`AGENTS.md`](../../AGENTS.md)'s "Default
guardrails" list is its one home, and a partial restatement of a security
boundary is the worst version of it. Go and read it there — it holds unless
this deployment's conventions doc explicitly says otherwise, so read that
doc at `CONVENTIONS_DOC_PATH` in `.env` for any deltas; silence there means
the default stands.
