# prompts/

This directory is the home for this deployment's **per-stage pipeline
prompt files** — the actual text a stage is invoked with when the pipeline
in [`skills/work-pipeline`](../skills/work-pipeline/SKILL.md) runs. That
SKILL owns what each stage is *responsible for*; this directory holds the
prompts that make a stage actually run, and this file is the one home for
where they live and how they're shaped.

They live in this repo rather than the product repo because a stage prompt
is the agent's own tooling, not product code — the same split
[`skills/git-pr-conventions`](../skills/git-pr-conventions/SKILL.md)'s
"Which repo are you even in?" section draws.

**No stage prompt ships here.** Which stages a deployment runs is a
per-deployment decision (`work-pipeline`'s own `TODO(specialize)`), and a
prompt is the most business-specific text in the whole setup: it names this
tracker's state names, this deployment's labels, this product's test
command. A pre-written one would be a confident wrong instruction obeyed on
every scheduled run. What ships instead is
[`STAGE_TEMPLATE.md`](./STAGE_TEMPLATE.md) — the structural skeleton every
stage prompt fills in.

## Naming

One file per stage kept, named after the stage: `refine.md`, `critique.md`,
`resolve-critique.md`, `implement.md`, `review.md`, and one per proactive
stage the owner wanted. Nothing parses these names — the point is that a
trigger (a cron line, a timer, a manual invocation) can name exactly one
file, and a reader can tell from the filename which stage they're reading.

## What a stage prompt is, and isn't

- **It is the complete instruction for one invocation.** The session reading
  it is fresh: it has no memory of the stage before it, and that
  independence is the whole reason the pipeline is split into stages at all.
  Anything the stage needs to know has to be in the prompt or in a file the
  prompt tells it to read.
- **It is not a copy of the skills.** Point at
  [`skills/work-pipeline`](../skills/work-pipeline/SKILL.md),
  [`skills/work-tracker`](../skills/work-tracker/SKILL.md) and
  [`skills/git-pr-conventions`](../skills/git-pr-conventions/SKILL.md) and
  have the stage read them; don't restate their contracts here.
- **It is not scheduling.** *When* a stage fires and *how* it's triggered is
  host config, deliberately outside this repo's remit for the reason
  [`skills/README.md`](../skills/README.md) gives. A prompt describes one
  invocation; the trigger lives with the host and is recorded per
  `work-pipeline`'s trigger marker.
- **It is prose about config, which makes it the highest-risk place for a
  copied fact.** A stale label name or state name inside a prompt is a false
  instruction acted on every run, not merely stale documentation. The rules
  in [`skills/specialize-skills`](../skills/specialize-skills/SKILL.md)'s
  "Rules for what you write" apply here in full, and matter more here than
  anywhere else in the repo: name the `.env` key or the conventions doc and
  have the stage read it.

## The common skeleton

Every stage prompt has the same bones, whatever the stage does — see
[`STAGE_TEMPLATE.md`](./STAGE_TEMPLATE.md), which is the one home for that
structure and is meant to be copied per stage and filled in.

## What each stage's prompt needs on top of the skeleton

This is about the prompt's *structure*, not about what the stage does —
`work-pipeline` is the home for the latter, and each prompt should point at
it rather than re-describing the stage's purpose. For the stages this repo
assumes:

- **refine** — needs the sections that turn a raw item into an actionable
  one: what this owner accepts as a problem statement and acceptance
  criteria, when work is big enough to decompose into sub-items and how the
  parent is left behind, and the exact conditions under which the "refined"
  and "needs human sign-off" markers get applied (never as a default hedge).
- **critique** — needs its comment-only boundary stated as a hard rule, plus
  a concrete list of what it is checking *for*, or it degenerates into
  agreeing with the refinement. Its value is entirely in not being the
  refining session, so the prompt must not give it any editing affordance.
- **resolve-critique** — needs a rule for handling each critique comment:
  which it must address, and that rejecting one is allowed but has to be
  written down with a reason rather than ignored silently.
- **implement** — the longest one. Needs the full eligibility test spelled
  out (all of `work-pipeline`'s conditions, not a subset), the fan-out and
  isolation mechanism this host actually has, the plan it posts before
  starting, the check for an existing skill covering the work, the "what
  does this make obsolete, and delete it in the same pass" step, the test
  command for this product, the commit/push/PR loop by reference to
  `git-pr-conventions`, the tracker state it moves the item to, and the
  hard rules `work-pipeline`'s own `implement` entry states about what this
  stage does and doesn't do — by reference to that entry, in full, not
  paraphrased into a subset here.
- **review** — needs the independence rule, everything `work-pipeline`'s
  own `review` entry says this stage is licensed to do (again by reference,
  in full, rather than a subset restated here), the exact
  stop-and-ask categories that are allowed to leave a PR open (by reference
  to [`AGENTS.md`](../AGENTS.md) and the conventions doc, not copied), and —
  where this deployment's remote has no PR mechanism at all — the agreed
  substitute recorded in `git-pr-conventions`' `Auth` section.
- **any proactive stage** (ideation, comment/message response, health check,
  self-audit) — same skeleton. Ideation additionally needs the pointer to
  where the business's own content and docs live, without which it can only
  propose generic work; that answer lives in the conventions doc at
  `CONVENTIONS_DOC_PATH`, so the prompt names the doc rather than the
  answer.
