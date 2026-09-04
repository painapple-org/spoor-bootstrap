# Onboarding from a written profile instead of an interview

The first-boot flow in [`../STARTUP.md`](../STARTUP.md) is a conversation. An
agent reads [`../AGENTS.md`](../AGENTS.md), asks the interview questions one at
a time, pushes back on a vague answer, and writes `.env` and this deployment's
conventions doc from what the conversation turned up. That is the right shape
when there is a human sitting there who wants to be asked.

There are two situations where it is the wrong shape, and this document is
about both:

1. **An owner who would rather fill in a file.** Some people would rather
   spend forty minutes on a document, on their own time, than hold a
   back-and-forth — and the answers are no worse for it. A few are answers
   they need to go and look up anyway (a Slack member id, a project key).
2. **Testing this repo's own onboarding.** Every dry-run of the flow so far
   has cost a human or an agent hand-simulating a fictional owner's answers,
   turn by turn, from scratch. That is the only way it has ever been
   exercised. It works, and it does not scale to running the flow twenty
   times against twenty shapes to find out which of them it breaks on.

So: [`../profile.example.toml`](../profile.example.toml) is a documented
format holding the interview's answers, and [`../spoor-profile`](../spoor-profile)
turns a filled-in one into the same artifacts the interview produces. Three
worked profiles are in [`../examples/`](../examples/README.md).

```sh
./spoor-profile examples/northlight.toml            # write .env and the conventions doc
./spoor-profile examples/northlight.toml --dry-run  # validate and report, writing nothing
./spoor-profile examples/northlight.toml --show     # print the generated files too
./spoor-profile --explain                           # the field list, and which fields it refuses to guess
```

## What it does, and what it deliberately does not

It writes two files: `.env`, at mode 0600 from the moment it exists, holding
exactly the keys [`../.env.example`](../.env.example) declares; and this
deployment's conventions doc, at the path the profile names, with a section per
bullet [`../STARTUP.md`](../STARTUP.md) step 6 asks that doc to record.

Everything else in the flow it reports as outstanding rather than doing. The
script's own header is the one home for the full scope statement — read it
there. The short version is that three kinds of thing cannot come out of a
document:

- **A credential, or anything that contacts a remote.** Establishing a git
  identity, verifying a push, reading a repo's live branch protection
  ([`../STARTUP.md`](../STARTUP.md) step 5) all need a network and a login. So
  does shipping the two generated files through a branch and a PR
  ([`../STARTUP.md`](../STARTUP.md) step 6). `spoor-profile` runs no git at
  all.
- **Writing, as opposed to filling in a blank.** The specialization pass
  ([`../STARTUP.md`](../STARTUP.md) step 7) turns each `TODO(specialize)`
  marker into a real answer, and one stage prompt gets written per pipeline
  stage kept. [`../skills/specialize-skills/SKILL.md`](../skills/specialize-skills/SKILL.md)
  is explicit that inventing a plausible specific is the failure that pass
  exists to prevent, and [`../prompts/README.md`](../prompts/README.md) is
  explicit that a pre-written stage prompt is a confident wrong instruction
  obeyed on every scheduled run. This script touches nothing under `skills/`
  or `prompts/`.
- **Business judgement.** Which is the next section, because it is the part
  worth being careful about.

## The judgement boundary

Most of the interview collects facts. Some of it collects decisions, and those
are the reason the interview exists at all — a generated guess at one is
indistinguishable from a real answer right up until it gets acted on.

So the format marks those fields `judgment`, and they may all be left out. What
lands in the conventions doc for a missing one is a `TODO(owner)` line naming
what is absent and who decides it, never a default. `./spoor-profile --explain`
prints the current list with the pointer for each; the fields, at the time of
writing, are the autonomy deltas and the shipping gate, what may be done to the
running deployment unattended, the product's stack and its rationale where
`END_USER_TYPE` is technical, an existing repo's stack conflict, the bar for
creating a tracked item, which private network anything internal is reached
over, who executes a refund, and the pipeline stage set.

**A profile with every one of those blank is a valid and useful profile.** It
generates a working `.env` and a conventions doc whose judgement sections are
explicit `TODO(owner)` lines — which is the honest state of a deployment nobody
has had the autonomy conversation with yet, and is strictly better than a set
of guardrail deltas the owner never agreed to.
[`examples/kweekhuis.toml`](../examples/kweekhuis.toml) is that case on purpose.

Two things are excluded for a different reason than judgement. The two secret
`.env` fields are always written blank, because a profile file gets committed,
mailed and diffed; a profile that names one is rejected rather than quietly
ignored. And `COMMS_ALLOWLIST` is not a field at all — it is derived from the
people list, since interview questions 1 and 5 are both per-person and `.env`
has one flat list rather than one entry per person.

## Using it for a real deployment

The profile replaces steps 1 to 4 of [`../STARTUP.md`](../STARTUP.md) and the
first half of step 6. Everything else in that flow runs unchanged, in the same
order, and still needs an agent with a terminal. So:

1. Copy [`../profile.example.toml`](../profile.example.toml), fill it in, and
   leave every `judgment` field you have not actually decided blank.
2. Run `./spoor-profile <your-profile>`. Read the report: it names every
   deferred judgement call and every outstanding step.
3. Paste the prompt in [`../STARTUP.md`](../STARTUP.md) into your harness, and
   tell it a profile has already been run — that file's
   "Driving this flow from a written profile" section is the one home for what
   changes about the flow when you do, and is written to be handed to the agent
   directly.

The point of ordering it that way is that the agent still gets to do the parts
that need judgement, a credential or a conversation, and does not get to skip
them on the grounds that a file already looked complete.

## Using it to test the flow

`.github/ci/test-profile.py` runs the generator against every profile in
[`../examples/`](../examples/README.md) on every push, builds a fixture
deployment around the result, and runs [`../spoor-doctor`](../spoor-doctor)
against it. That script's own header is the one home for what each case
asserts.

One of those assertions is worth naming here because it is the load-bearing
one: [`example-walkthrough.md`](./example-walkthrough.md) narrates the
interview for Northlight Coffee Roasters and shows the `.env` it produces, and
[`examples/northlight.toml`](../examples/northlight.toml) is the same business
with the same answers. The test parses the expected values out of the
walkthrough itself and asserts the generated `.env` matches key for key. Read
from the walkthrough rather than copied out of it, so the two cannot drift: a
change to either that breaks the equivalence fails CI rather than going
unnoticed.

What that buys is the thing this document opened with. Adding a shape to test
is now writing a profile file, not driving an interview — and the shape that
gets exercised is the one that actually ships, since the same script does both
jobs.
