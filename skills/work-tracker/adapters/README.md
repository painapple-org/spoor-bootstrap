# work-tracker adapters

Reference notes for mapping the tracker-agnostic contract in
[`../SKILL.md`](../SKILL.md) onto a specific real tracker. One file per
tracker; pick the one the owner named in
[`STARTUP.md`](../../../STARTUP.md)'s interview.

These are **not** a specialized skill. They're the research an agent would
otherwise have to redo from scratch — the API shapes, the state-model
mismatches, the gotchas that cost a run — written down once so the
specialization pass has something concrete to work from. `SKILL.md` stays
the single home for the contract, the five-state machine, the label
vocabulary and the tracker-independent rules; these files never restate
any of that, they only say how it lands in one tracker's API.

## Available adapters

- [`github-issues.md`](./github-issues.md) — GitHub Issues via the `gh` CLI
  and REST. No native state machine beyond open/closed, so the pipeline
  states have to be modeled as labels.
- [`linear.md`](./linear.md) — Linear via GraphQL or its MCP server. The
  closest native fit to the contract: real per-team workflow states, and
  state+assignee move in one mutation.
- [`jira.md`](./jira.md) — Jira Cloud via REST v3. Native statuses, but you
  can only reach them through *transitions*, which is the one structural
  difference from the contract's "set the state" verb.

## How to use one during specialization

1. Read the adapter for the chosen tracker along
   [`../SKILL.md`](../SKILL.md).
2. **Verify before you write.** Every adapter marks the parts its author
   was not certain of, and says which of that tracker's own docs to check.
   Treat those as unanswered questions, not as facts with a hedge attached
   — a wrong API shape written into a skill file is a false instruction an
   agent will follow literally on every run. Where a claim is checkable by
   running one command against the real tracker with the real credential,
   run it; that beats both the adapter and the docs.
3. Fill the `TODO(specialize)` markers in `SKILL.md` with the concrete
   answers for *this* deployment: the literal state names, the literal
   label names, the scope identifier, the access mechanism, the agent's own
   account. An adapter cannot answer those — it doesn't know the
   deployment.
4. **Delete the per-tracker adapter files you didn't use, once `SKILL.md` is
   specialized** — but keep this file. A deployment runs one tracker;
   keeping notes for two others is exactly the "no state that isn't real
   right now" rule this repo applies to itself — see
   [`CONTRIBUTING.md`](../../../CONTRIBUTING.md#no-state-that-isnt-real-right-now).
   Git holds them if the owner ever migrates trackers. This README stays because it's the
   permanent index for the directory and several files across the repo link
   to it; remove the bullet for each deleted adapter from "Available
   adapters" above instead.

   **If the owner's tracker is none of the three**, every adapter goes and
   this directory is left indexing nothing — which is the one case where
   keeping this file is worse than removing it. Delete the whole
   `adapters/` directory then, and repoint the links to it (in
   [`../SKILL.md`](../SKILL.md) and
   [`skills/README.md`](../../README.md)) at `../SKILL.md`'s own "How to
   actually call the tracker" section, which by that point holds the real
   answer for this deployment. See the next section for the notes worth
   writing instead, and where.

## If the owner's tracker isn't one of these

With this directory gone per step 4 above, the notes below belong in the
"Known gotchas" part of [`../SKILL.md`](../SKILL.md)'s own tracker section
rather than in a new file here — there is no longer a directory for them to
live in, and one deployment runs one tracker, so a separate adapter file
buys nothing.

Write them as you discover them, in the same shape:
the seven contract operations, how state and labels are modeled, and where
it diverges. The divergences are the valuable part — the happy path is in
that tracker's own quickstart, the gotchas aren't.
