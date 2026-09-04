# Stage prompt template

Copy this to `prompts/<stage>.md` and fill it in for one stage. The
sections below are the bones every stage prompt has;
[`README.md`](./README.md) in this directory is the home for what each
individual stage adds on top, and for the rules about what belongs in a
prompt at all.

Delete a section only when it genuinely doesn't apply to the stage, and say
so in one line rather than leaving it blank — a silently missing section
reads as an oversight to the next person editing this.

Nothing in the skeleton below is a value to keep. Every `<...>` is
something this deployment has to answer for itself, and a `<...>` left
unfilled is a prompt that isn't finished.

---

## 1. What stage this is

One sentence: this is the `<stage>` stage. Point at
[`skills/work-pipeline`](../skills/work-pipeline/SKILL.md) for what the
stage is responsible for; do not restate it here.

State outright that this session is a fresh one with no memory of the stage
before it, and that everything it needs is either in this prompt or in a
file this prompt names.

## 2. Read these first

The files this stage must read before doing anything, and why each one:

- `skills/work-pipeline/SKILL.md` — the stage chain and the two rules that
  apply to every stage.
- `skills/work-tracker/SKILL.md` — how to read and write work items, the
  state machine, the label vocabulary.
- `skills/git-pr-conventions/SKILL.md` — only for a stage that touches git.
- [`AGENTS.md`](../AGENTS.md)'s default guardrails, plus this deployment's
  conventions doc at `CONVENTIONS_DOC_PATH` in `.env` — read the variable,
  then the file it names.
- `<any other skill or doc this particular stage needs>`.

## 3. Recovery before new work

`work-pipeline` states this rule for every stage; the prompt has to actually
make the stage do it. Instruct it to find work already claimed by this agent
and stuck in progress, verify the real state against the acceptance criteria
rather than assuming, and continue from there — never duplicating,
reverting, or clobbering what already landed.

## 4. What this stage acts on

The exact selection criteria, stated so that a session can evaluate them
without judgement calls:

- **The query**: `<how to find candidate items in this tracker>`.
- **The eligibility conditions**: `<every condition, all of them required>`.
- **What to do when nothing is eligible**: exit quietly and say so; an empty
  queue is a normal outcome, not a failure to work around.

## 5. The work

The steps this stage performs, in order, in enough detail that two separate
runs would do the same thing. This is the stage-specific body — see
[`README.md`](./README.md) for what belongs here per stage.

Include, where the stage has them: the concrete commands to run (`<test
command>`, `<deploy command>`), and how many items it may work on in one
invocation.

## 6. Write the result back

A stage that leaves its result only in its own session output has done
nothing. Instruct it to write back:

- **To the work item**: what gets recorded, and the tracker comment marker
  from the conventions doc as the last line of every comment it writes, per
  `skills/work-tracker`'s contract.
- **The state/label transition**: `<from state>` → `<to state>`, and which
  markers get set or cleared.
- **To the owner**, if this stage is one that should report — over the comms
  channel per `skills/comms-channel`, to the single alert destination in
  `COMMS_ALERT_TARGET` for anything urgent.

## 7. Hard boundaries

What this stage must **not** do, stated as rules rather than preferences —
this is the section that keeps the stages independent:

- `<e.g. this stage comments and never edits>`
- `<e.g. this stage opens a PR and never merges its own>`
- Anything on `AGENTS.md`'s default guardrail list, as amended by the
  conventions doc: name the conflict and stop, don't resolve it in either
  direction.

## 8. Failing loudly

What to do when this stage cannot do its job: report it where a human will
actually see it, on the same run, rather than exiting clean. Name the
destination (`COMMS_ALERT_TARGET`, or a comment on the item) and say
explicitly that a log line alone is not a report.
