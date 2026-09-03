---
name: work-tracker
description: How this deployment reads and writes work items in whichever work tracker its owner chose (Linear, GitHub Issues, Jira, plain markdown, or another). Read before querying, claiming, commenting on, or closing any work item. Ships as a stub — the tracker-specific half must be filled in during first-boot specialization.
---

# work-tracker

## Status: STUB — needs specialization

This SKILL is deliberately incomplete. `spoor-bootstrap` ships with **no
work-tracker integration at all**, because which tracker a deployment uses
is a first-boot interview answer (see [`STARTUP.md`](../../STARTUP.md)), not
something this template picks. Everything below that is marked
`TODO(specialize)` has to be filled in for the actual chosen tracker before
any pipeline stage that touches work items can run. Fill it in via
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

The tracker's name is recorded in `WORK_TRACKER` in `.env`, and its
credential in `WORK_TRACKER_API_KEY` (renamed to the tracker's own
convention if the owner preferred). Read those rather than assuming a
tracker — if `WORK_TRACKER` is empty, first-boot setup hasn't happened yet
and the answer is to run it, not to guess.

## When this applies

Any time you need to find work to do, record that you're doing it, ask a
question about it, or mark it finished. That covers every stage of the
work pipeline in [`skills/work-pipeline`](../work-pipeline/SKILL.md), plus
ad-hoc requests that arrive over the comms channel and deserve a tracked
item rather than a one-off reply.

## The tracker-agnostic contract

These are the operations every stage in this repo assumes exist. They hold
regardless of tracker; only their implementation differs.

1. **Query work items by state + owner.** You must be able to list items
   filtered by (a) which pipeline state they're in and (b) whether they're
   assigned to *you* (this agent instance) versus a human.
2. **Read one item in full**, including its description, acceptance
   criteria, and its full comment history. Comments are load-bearing: a
   previous run's plan, a human's answer to a blocking question, and a
   prior "still waiting" note all live there.
3. **Claim an item**: set it to the in-progress state *and* assign it to
   yourself, as one atomic-as-possible step before doing any real work, so
   a concurrent run doesn't pick up the same item.
4. **Comment on an item.** Every comment you write ends with a footer line
   naming which process wrote it, so a later run can tell your own prior
   notes apart from a human's. The literal marker convention is recorded in
   the deployment conventions doc — read its path from
   `CONVENTIONS_DOC_PATH` in `.env`, then read that file. It's captured
   during [`STARTUP.md`](../../STARTUP.md) step 5; if it's missing there,
   ask the owner rather than inventing a marker, since an inconsistent
   footer defeats the whole point of having one.
5. **Transition an item's state** through the pipeline.
6. **Create a new item**, assigned either to yourself or to a human.
7. **Read and write labels**, and understand that many APIs *replace* the
   full label set rather than diffing it — always pass back the labels you
   want to keep.

### The state machine this repo's pipeline assumes

Five states, whatever your tracker calls them:

| Role | What it means |
|---|---|
| unrefined-inbox | A raw idea or request, not yet scoped enough to build |
| ready | Scoped, has acceptance criteria, safe to pick up |
| in-progress | Claimed by a run that is actively working it |
| in-review | Work is done and a PR is open, awaiting the review pass |
| done / cancelled | Terminal |

`TODO(specialize)`: map each row above to the literal state name in the
chosen tracker, and record the mapping here. If the tracker has no native
notion of one of these (e.g. a plain-markdown tracker with no "in review"),
say explicitly how it's represented instead — a label, a checkbox, a
directory — rather than leaving the row blank.

### The label vocabulary this repo's pipeline assumes

Three labels carry real behavioral meaning:

- **a "refined" marker** — combined with the `ready` state, this is what
  makes an item eligible to be claimed. Both are required: a refined item
  in the wrong state is invisible to the pipeline forever, which is a
  common and confusing failure, so make the requirement explicit in
  whatever the tracker's own docs/templates are.
- **a "needs human sign-off" marker** — set when an item cannot be closed
  until a specific named person replies on a specific thread. Its presence
  must be a narrow exception for genuine authority/capability gaps, never a
  default hesitation device for ordinary work.
- **a "targets the agent's own tooling, not the product" marker** — set
  when an item's real fix lives in this bootstrap/pipeline repo rather than
  in the product repo at `PRODUCT_REPO_PATH`. Stages behave differently for
  these (see [`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md)).

`TODO(specialize)`: record the literal label names chosen for these three,
and confirm they actually exist in the tracker. Do not invent additional
behavioral labels here — anything else the owner wants is theirs to add and
document in the deployment conventions doc (`CONVENTIONS_DOC_PATH` in
`.env`).

## How to actually call the tracker

`TODO(specialize)` — fill in, for the chosen tracker:

- **Access mechanism**: an MCP server, an official SDK, a CLI, or raw HTTP.
  Prefer something that already exists over writing a client (see the
  "reach for something that exists" principle in the deployment conventions
  doc at `CONVENTIONS_DOC_PATH` in `.env`). Name the concrete
  package/server, not a category.
- **The identity the agent acts as.** The agent must act as its *own*
  tracker account, not the owner's — that's what makes the tracker's own
  permissions able to scope it, and it's what makes "assigned to a human"
  vs "assigned to the agent" a meaningful signal at all. A human provisions
  that account; see `AGENTS.md`'s self-provisioning section.
- **The scope identifier**: team/project/board key, repo, or file path,
  depending on tracker.
- **Any known gotchas of that specific API.** Write these down the first
  time one bites, rather than rediscovering it every run — e.g. a
  parent/child relation that a "get one item" call silently omits, or a
  filter parameter that accepts two identifier forms and only works with
  one of them.

## Rules that hold regardless of tracker

- **An item assigned to a human is inert. Leave it alone**, however long
  it sits. Nothing times out, nothing auto-claims. Reassigning something to
  a human is the owner's deliberate way to pause it, and that only works if
  every stage honors it.
- **Never post a content-free repeat comment.** If your last comment on an
  item was "asked a question, waiting for an answer", do not post that
  again on the next run. Check whether the *specific named person* replied
  on the *specific thread* the question was asked on — unrelated activity
  elsewhere does not count — and if they haven't, drop the item from this
  pass silently: no comment, no state change. The same applies to a
  purely time-gated wait: read the stated target date, compare it to the
  real current date, and if it hasn't passed, drop the item silently.
  Left unchecked, this failure mode produces double-digit near-identical
  comments on a single item within days.
- **Verify actual state against acceptance criteria before closing
  anything.** A plan comment is not evidence the work happened, and its
  absence is not evidence it didn't. Check the real target — the live
  service, the branch, the PR.
- **Name the observable that proves the work is live, and check it.**
  Merging is not the observable. A scheduled job is live when it's in the
  schedule; a config change is live when the running service serves it.
