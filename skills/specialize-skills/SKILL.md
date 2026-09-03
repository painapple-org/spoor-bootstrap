---
name: specialize-skills
description: The one-time pass that turns this repo's generic skill stubs into this deployment's real instructions, using the first-boot interview answers. Run once, as the last step of STARTUP.md's flow, after .env and the conventions doc are written and before any product work starts.
---

# specialize-skills

## When to run this

Once, as the final step of the first-boot flow in
[`STARTUP.md`](../../STARTUP.md) — after the interview, after `.env` is
written, after this deployment's conventions doc exists, and **before** any
product feature work begins.

Also run it again, scoped to one file, whenever a `TODO(specialize)` marker
somewhere becomes answerable — e.g. the owner has now provisioned the
work-tracker account, so `skills/work-tracker/SKILL.md` can stop saying
"the tracker isn't chosen yet".

Do not run this on a checkout where `.env` is still empty. Without the
interview answers there is nothing to specialize *from*, and inventing
plausible answers is the exact failure this step exists to prevent.

## Why the stubs exist in this shape

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

Work through these in order — later ones depend on earlier answers:

1. [`skills/work-tracker`](../work-tracker/SKILL.md) — the chosen tracker's
   access mechanism, the state-name mapping, the label names, the agent's
   own account, the scope identifier.
2. [`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md) — the
   default branch and naming convention, the push/auth invocation that
   actually works from an unattended session on this host, the pushing
   identity, any protected branches.
3. [`skills/comms-channel`](../comms-channel/SKILL.md) — the channel's send
   and receive mechanisms, the literal allowlist of who may instruct this
   agent, the single alert destination, and the interrupt-versus-digest
   policy the owner actually wants.
4. [`skills/work-pipeline`](../work-pipeline/SKILL.md) — which stages this
   deployment runs, where each stage's prompt lives, what triggers each,
   and which proactive stages (if any) the owner wants.
5. [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md) — the
   deploy trigger and command, the rollback procedure, the health signals
   that actually exist, and what the agent may fix unattended.
6. [`skills/product-tech-stack`](../product-tech-stack/SKILL.md) — nothing
   to specialize. It is already a finished, deliberately non-negotiable
   requirement. Do not edit it to suit a preference; if it applies, follow
   it.

## How to specialize one file

For each `TODO(specialize)` marker:

1. **Answer it from a real source** — an interview answer, a value in
   `.env`, the conventions doc, or something you verified by running a
   command against the actual host or API. Verifying beats assuming: if the
   question is "which push protocol works from an unattended session
   here", try it and record what actually worked.
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
because they're specific to this product. Write those as new skills under
`skills/` following [`skills/README.md`](../README.md) — instructions only,
no scheduling mechanics, no harness-specific syntax — and add them to that
file's "Current skills" list.

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
