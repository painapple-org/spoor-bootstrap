---
name: specialize-skills
description: The one-time pass that turns this repo's generic skill stubs into this deployment's real instructions, using the first-boot interview answers. Run once, as the specialization step of STARTUP.md's flow, after .env and the conventions doc are written and before any product work starts.
---

# specialize-skills

## When to run this

Once, as the specialization step of the first-boot flow in
[`STARTUP.md`](../../STARTUP.md) — after the interview, after `.env` is
written, after a git identity has been verified against a real push, after
this deployment's conventions doc exists and has shipped through its own
PR, before the self-provisioning shopping list that closes that flow out,
and **before** any product feature work begins.

Also run it again, scoped to one file, whenever a `TODO(specialize)` marker
somewhere becomes answerable — e.g. the owner has now provisioned the
work-tracker account, so `skills/work-tracker/SKILL.md` can stop saying
"the tracker isn't chosen yet".

Do not run this on a checkout where `.env` is still empty. Without the
interview answers there is nothing to specialize *from*, and inventing
plausible answers is the exact failure this step exists to prevent.

## Why the stubs exist in this shape

This section is the one home for this rationale — `README.md`, `AGENTS.md`
and [`skills/README.md`](../README.md) all point here rather than restating
it.

This repo cannot know the owner's tracker, comms channel, host, or product,
so it ships the parts of each skill that are true regardless (the contract,
the state machine, the concurrency hazards, the writing rules) and marks
every business-specific gap with `TODO(specialize)`. That marker is a
promise: it says "a real answer belongs here and does not exist yet",
which is honest, whereas a plausible-looking placeholder value is
indistinguishable from a real one right up until it's acted on.

Your job here is to convert each marker into a real answer, or to delete
it with a reason.

## The stubs to specialize

What each of these skills *is* isn't restated here — that's the "Current
skills" list in [`skills/README.md`](../README.md). What follows is only
the specialization order and what each file is waiting for an answer to.
Work through them in order; later ones depend on earlier answers:

1. [`skills/work-tracker`](../work-tracker/SKILL.md) — the chosen tracker's
   access mechanism, the state-name mapping, the label names, the agent's
   own account, the scope identifier, and where a second auth value comes
   from if that tracker's auth needs one (or that it's token-only). Read
   [`skills/work-tracker/adapters`](../work-tracker/adapters/README.md)
   first if the chosen tracker is one it covers, and follow its instruction
   to delete the per-tracker adapter files this deployment didn't use once
   the SKILL is specialized. Where the chosen tracker *is* one of them,
   that directory's own README stays, as the index other files link to;
   where it's none of them, that README's own last step has the directory
   go too, along with the links into it. Follow whichever case applies
   rather than assuming the first.
2. [`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md) — the
   default branch and naming convention, any protected branches. Its
   `Auth` section is **not** part of this pass: it's answered earlier, at
   [`STARTUP.md`](../../STARTUP.md) step 5, because the first push this
   flow makes happens before this pass runs and cannot wait on it. If you
   find that section still carrying a marker, the fix is to go verify a
   real push, not to fill it in here from what you assume worked.
3. [`skills/comms-channel`](../comms-channel/SKILL.md) — the channel's send
   and receive mechanisms, what the allowlist *means* on this deployment
   (who each identity is, who with channel access is deliberately off it),
   the single alert destination, and the interrupt-versus-digest policy the
   owner actually wants. The literal allowlist is **not** part of this pass:
   it's `COMMS_ALLOWLIST` in `.env`, written back at
   [`STARTUP.md`](../../STARTUP.md) step 4 from the interview answer, well
   before this pass runs. Read it from there rather than re-collecting it,
   and don't copy its values into the SKILL file.
4. [`skills/work-pipeline`](../work-pipeline/SKILL.md) — which stages this
   deployment runs, what triggers each, and which proactive stages (if any)
   the owner wants. Where the prompts live is already answered — it's
   [`prompts/`](../../prompts/README.md) — but the prompt files themselves
   are the one part of this pass that is real writing rather than
   marker-filling, one file per stage kept, from that directory's template.
   Anything you can't finish in this pass is outstanding work to hand back
   with the shopping list, not a marker to leave in this SKILL.
5. [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md) — **whether
   a deploy pipeline already exists at all**, which that file makes the
   first question because every other answer in it changes shape depending
   on it: an inherited pipeline gets recorded and deferred to, not rebuilt.
   Then how many
   environments there are and what gates promotion between them (including
   saying so explicitly when there is only one), the deploy trigger and
   command, the rollback procedure, **what is backed up and whether a
   restore has ever been verified**, the health signals that actually
   exist — including which of them this agent can reach without access to
   the product's host — and what the agent may fix unattended. The backup half is a
   whole section of that file rather than one bullet, and on a product that
   already has users it is the most load-bearing thing in this pass — an
   honest "nothing is backed up" belongs on the shopping list, not in a
   hedge.
6. [`skills/synthetic-monitoring`](../synthetic-monitoring/SKILL.md) — which
   of this product's user-facing flows get a continuous synthetic check, what
   counts as proof of each one's side effect, whether the product can even be
   asked to confirm that side effect yet, the marker-and-cleanup arrangement
   the owner agreed to for test data in production, the cadence and where its
   schedule lives, and what watches for the check's own silence. It comes
   after `deploy-and-monitor` because it is the gap that pass leaves: item 5
   establishes which health signals exist and what they can see, and a
   synthetic check is what covers the flows none of them do. **"The product
   has no users yet, so nothing is worth checking" is a real answer** — record
   it as decided rather than leaving the file unasked, and note that the
   trigger to revisit it is the product getting its first real user. Where the
   evidence read a check needs doesn't exist in the product yet, that is
   ordinary work to do rather than a blocker, and it belongs on the shopping
   list only if somebody else owns the product's code.
7. [`skills/private-networking`](../private-networking/SKILL.md) — which
   mesh VPN this deployment already has or joins, what is exposed on it,
   who besides this box can reach it, and where each node's auth key
   lives. It comes after `deploy-and-monitor` because it is the same
   question asked about the *internal* half: that pass establishes what
   runs where and what access exists, and this one records how anything
   built for the owner alone gets reached. **"Nothing internal exists yet,
   so no mesh" is the expected first-boot answer, and it is a real one** —
   record it as decided in the conventions doc, per that file's "When
   nothing needs it yet", rather than provisioning a network for a tool
   that doesn't exist. Expected rather than required: where the interview's
   internal-tooling question came back yes, the answer is the mesh agreed
   on and what the owner has to provision for it, and item 8 is where the
   tool itself lands. Anything the owner would have to provision on the
   day one does joins the shopping list.
8. [`skills/internal-dashboard`](../internal-dashboard/SKILL.md) — whether
   this deployment wants an internal operations dashboard at all, and if
   so, the stack it's built in and the pages it has. It comes this late
   because it depends on two earlier items: its page list is drawn from the
   health signals item 5 establishes, and it is reached over whatever item 7
   recorded. Take the "no" answer as seriously here as there — that file
   opens by saying not to build one speculatively, so "not wanted, the
   comms channel is enough" finishes this item legitimately and leaves its
   remaining markers moot.
9. [`skills/billing-and-payments`](../billing-and-payments/SKILL.md) —
   **whether this deployment's product charges anyone at all**, which that
   file makes its first question because every other answer in it is moot
   until it's yes. "Nothing is sold yet" is the expected first-boot answer
   and a real one; record it as decided in the conventions doc, per that
   file's own instruction, rather than leaving it unasked. Where it *is*
   yes: the provider and whose account it is, what is actually sold, the
   environment-variable names holding the test and live keys and the
   webhook signing secret, where entitlement is stored and read in the
   product's code, who handles tax and invoicing, and which named human
   executes a refund or a dispute response — since the agent may not. It
   comes last of the stubs because it depends on items 3 and 5: a billing
   alert goes to the destination item 3 establishes, and a payment
   credential is an ordinary secret under item 5's own secrets section. The
   tax half is a legal question rather than an engineering one, so an
   unanswered one belongs on the shopping list and never in a hedge.
10. [`skills/product-tech-stack`](../product-tech-stack/SKILL.md) — nothing
    to specialize. It is already a finished, deliberately non-negotiable
    requirement. Do not edit it to suit a preference; if it applies, follow
    it.
11. [`skills/skill-authoring`](../skill-authoring/SKILL.md) — nothing to
    specialize either, and nothing to fill in: it is generic by
    construction, since how to write a skill doesn't vary by deployment.
    It is in this list because this pass is the commonest place its subject
    comes up — see "Adding a skill that isn't a stub here" below, which is
    the one home for that instruction. Read it there rather than treating
    this item as a step of its own.

## How to specialize one file

For each `TODO(specialize)` marker:

1. **Answer it from a real source** — an interview answer, a value in
   `.env`, the conventions doc at `CONVENTIONS_DOC_PATH`, or something you
   verified by running a command against the actual host or API. Verifying
   beats assuming: if the question is "does this deploy command actually
   work on this host", run it and record what actually happened.
2. **Write the answer in place of the marker**, then delete the marker. A
   marker left next to its own answer is drift waiting to happen.
3. **If the answer is genuinely "not applicable to this deployment", say
   that explicitly and say why**, then delete the marker. `COMMS_CHANNEL=none`
   and "no automated deploy pipeline" are real answers, and a reader needs
   to know they were decided rather than skipped.
4. **If the answer isn't knowable yet** (the account isn't provisioned, the
   product repo doesn't exist), leave the marker and add one line naming
   exactly what unblocks it. Then put that blocker on the
   self-provisioning shopping list you hand back to the owner.
5. **Never invent a specific.** No guessed team key, no assumed state
   names, no example credential, no cadence nobody agreed to. A stub that
   still says "unknown" is strictly better than one that confidently says
   the wrong thing.
6. **Update the front-matter `description`** if the skill's applicability
   changed — the description is what a harness uses to decide whether to
   load the skill at all, so a stale one makes real content unreachable.
7. **Drop the file's `Status:` heading** once no markers remain in it.
   That heading is the file's own honest self-report; leaving it on a
   finished file trains readers to ignore it.

Then, once every file in the pass is done, one bookkeeping step that isn't
per-file: **update the "Current skills" list in
[`skills/README.md`](../README.md)**. That list is the one enumeration of
what exists under `skills/`, and it labels each stub *stub* or *partial
stub* — labels that are false the moment a pass removes the markers behind
them. Drop the label from every skill this pass finished, and correct any
entry whose description no longer matches the file: the `work-tracker`
entry in particular describes `adapters/` as holding notes for three
trackers, which stops being true as soon as you follow
[`adapters/README.md`](../work-tracker/adapters/README.md)'s instruction to
delete the ones this deployment didn't use — and stops naming a real
directory at all if that instruction's none-of-the-three case applied.

Then, once the pass itself is done: **ship it through a branch and a PR**,
per [`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md). These are
tracked files in this repo, and specialization sitting uncommitted in one
working tree has no revert point and no reviewable diff. One PR per pass:
the whole first-boot pass in one, and each later scoped re-run in its own.
A re-run is unattended, so it happens in a scratch clone and not the
primary checkout — that SKILL's "Which repo are you even in?" section is the
home for why and how.

## Rules for what you write

- **Every fact has exactly one home.** Name the constant, file, or config
  key that owns a value; don't copy the value. A copied number is
  indistinguishable from a true one right up until it's wrong, and a stale
  value inside a prompt is a false instruction obeyed on every run — worse
  than stale documentation, because something acts on it.
- **The trigger to watch for**: you are writing prose about config you just
  wrote. At that moment every number, path, name and threshold in that
  prose is a copy of something with an owner. Read it from the source, name
  the owner, or leave it out.
- **No secrets.** Reference the variable name in `.env`, never its value.
- **No state that isn't real right now**, in either direction. Don't leave
  a compatibility note for a system this deployment never had, and don't
  pre-add a placeholder for something that doesn't exist yet either.
- **Centralize exhaustively or not at all.** If you make something
  config-driven while specializing, audit every skill file for the old
  hardcoded form before calling it done.

## Adding a skill that isn't a stub here

Specialization will surface capabilities this template has no stub for,
because they're specific to this product — a compliance regime with real
operational steps, an on-call rotation, an analytics pipeline. Authoring
one is its own job with its own rules, and
[`skills/skill-authoring`](../skill-authoring/SKILL.md) is the one home for
them: whether a new file is even the right artifact, what it has to own to
earn its own seam, and the wiring it isn't finished without. Follow it
rather than deriving the shape from the stubs you have just been reading —
this pass answers markers in files that exist, and that is a different job
from bringing one into existence.

The same applies during ordinary operation: when a work item turns out to
involve a non-obvious technique, pitfall or workaround that would genuinely
help a future run, write it down as a skill. Don't manufacture one from
routine work just to have written one.

## When you're done

Report to the owner:

- which stubs are now fully specialized,
- which still carry markers, and the exact blocker for each (these join the
  self-provisioning shopping list),
- any answer you had to make a judgment call on rather than being told,
  so they can correct it cheaply now instead of discovering it later.
