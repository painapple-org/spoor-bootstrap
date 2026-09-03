---
name: work-pipeline
description: The stage chain this agent instance moves work through — refine, critique, implement, review, merge — and what each stage is responsible for. Read when acting as any one of those stages, or when deciding whether a request should become a tracked work item at all. Ships as a stub for the per-stage prompts and their triggers.
---

# work-pipeline

## Status: STUB — needs specialization

The stage *shape* below is real and generic. What does not exist yet, and
cannot until a deployment is configured, is: the per-stage prompt files
themselves, the triggering mechanism, and the concrete tracker/git calls
each stage makes. Those are `TODO(specialize)` — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

This SKILL depends on two others and does not restate them: work-item
operations live in [`skills/work-tracker`](../work-tracker/SKILL.md), and
git/PR mechanics in
[`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md).

## Why a pipeline at all

`AGENTS.md` describes this agent as working *through a devops pipeline*
rather than a chat loop. Concretely that means work moves through discrete
stages, each with its own scope and its own session, rather than one
long-running session doing everything. The reason is independence: the
session that reviews a change must not be the session that wrote it, or
the review is worthless.

## The stages

Each stage below is a separate invocation with its own prompt. A stage
reads the work tracker, does its one job, writes its result back to the
tracker, and exits.

1. **refine** — takes a raw item out of the unrefined inbox and turns it
   into a real problem statement, scope, and acceptance criteria. Decomposes
   into sub-items when the work is too big for one change. Applies the
   "refined" marker only when the item is genuinely actionable. Applies the
   "needs human sign-off" marker only for a genuine authority/capability
   gap — never as a default hedge.
2. **critique** — an independent second pass over the just-refined item.
   Comments only; never edits. Its value is entirely in not being the
   refining session.
3. **resolve-critique** — addresses what critique flagged.
4. **implement** — claims eligible items (ready state + refined marker + no
   sub-items + not blocked + assigned to the agent, all five), fans out one
   isolated worker per item, and for each: posts a plan, checks whether an
   existing skill already covers the work, asks what the change makes
   obsolete and deletes that in the same pass, implements, runs the tests,
   commits, pushes, opens a PR, and moves the item to in-review. **Does not
   merge its own PR.**
5. **review** — an independent pass over the open PRs. Reviews each diff on
   its own merits, fixes clear problems directly on the branch, merges, and
   closes the item. Biases hard toward merging: git-reversible work means a
   wrong call costs a revert, not a disaster. Leaves a PR open only for a
   real stop-and-ask category.

Two rules that apply to every stage:

- **Recovery before new work.** Start by finding items already claimed by
  the agent and stuck in-progress — a previous run may have crashed
  mid-work, having done none, some, or all of the work. Verify actual state
  against acceptance criteria and continue from there; never duplicate,
  revert, or clobber what already landed.
- **Reconcile after a parallel batch.** Sibling items can touch overlapping
  code with no formal dependency between them, and parallel workers cannot
  see each other's in-flight edits. After a batch finishes, check the
  results against each other and fix conflicts as a follow-up.

`TODO(specialize)`: the stage list above is the shape this repo assumes, not
a mandate. Record which stages this deployment actually runs — a small
product may collapse refine/critique/resolve into one, and that's a real
choice, not a shortcut. Then write the prompt file for each stage kept, and
record where those prompts live.

`TODO(specialize)`: record what triggers each stage (a schedule, a tracker
webhook, a manual invocation) and where that trigger is configured.
Scheduling mechanics are deliberately outside a SKILL — see
[`skills/README.md`](../README.md) — so point at the host config, don't
inline it.

## Proactive work

The pipeline above is reactive: it drains a queue someone else filled. A
deployment usually also wants stages that *fill* the queue, and stages that
watch for things going wrong:

`TODO(specialize)`: decide with the owner which of these this deployment
wants, and write a prompt for each one kept. Do not create these
speculatively — an unused stage that runs on a schedule is worse than no
stage. Candidates worth discussing:

- **ideation** — proposes new items into the unrefined inbox, assigned to
  the *human*, so they stay inert until the owner reassigns them. This
  needs to know where the business's own context lives (its site, its docs,
  its product content) to propose anything non-generic — that pointer is
  itself a specialization input.
- **responding to a comment** on a work item from someone other than the
  agent.
- **responding to an inbound message** on the comms channel.
- **health/operational checks** on the running product — see
  [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md).
- **an audit pass** over the agent's own behavior: commitments it made and
  didn't keep, lessons it was told and didn't encode.

## Turning a request into a tracked item

A request that arrives outside the tracker (a message, an email) needs a
decision: reply and be done, or create a tracked item?

Create one when the work is substantial, when it will outlive the
conversation, or when the owner wants a record of it. When you do, embed a
marker in the item pointing back at the source message, and check that
marker before implementing — otherwise a live conversational session and a
scheduled implement run can independently build and ship competing
versions of the same request.

`TODO(specialize)`: record the owner's actual preference for the bar here.
Some owners want every change tracked, including one-line copy edits;
others find that friction. Ask, don't infer.
