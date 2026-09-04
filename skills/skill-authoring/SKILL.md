---
name: skill-authoring
description: How to author a genuinely new skill for a capability this repo ships no stub for — billing, an on-call rotation, a compliance requirement, an analytics pipeline, anything the fixed set doesn't reach. Covers the cheaper answers to try first, the seam test that decides whether it is a new file or a section of an existing one, the file shape CI enforces, the stub-versus-finished decision, when the answer is a runnable template rather than more prose, and how a new skill gets wired into the indexes and the specialization pass. Read before creating any directory under skills/, and before writing a second skill's worth of instructions into a file that already exists.
---

# skill-authoring

## When this applies

You have a capability that no skill here covers, and you are about to write
the instructions for it. That happens in three ways, all normal:

- **During specialization.** The first-boot pass surfaces something this
  template could not have known about — the owner's product takes payments,
  or their sector has a compliance regime with real operational steps.
  [`skills/specialize-skills`](../specialize-skills/SKILL.md)'s "Adding a
  skill that isn't a stub here" is the section that sends you here.
- **During ordinary operation.** A work item turned out to involve a
  non-obvious technique, pitfall or workaround that a future run would
  genuinely be worse off not knowing.
- **Because the owner asked for it**, in as many words: "write down how we
  do X".

It does **not** apply to filling in an existing stub. Turning a
`TODO(specialize)` marker into a real answer is a different job with its
own home, and that home is
[`skills/specialize-skills`](../specialize-skills/SKILL.md) — this file is
only for bringing a file into existence that wasn't there.

## First: is a new skill even the right artifact?

Reach for what exists before building one. This is the same
defer-to-what-is-already-there reasoning that
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md)'s "When the
product repo already exists and doesn't match" applies to an inherited
codebase and [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s
"First: does a deploy pipeline already exist?" applies to an inherited
pipeline, pointed at this directory instead. A new file is the most
expensive answer available here, and three cheaper ones come first:

1. **An existing skill already owns this and is merely unspecialized.**
   The commonest case by a distance, and the easiest to miss, because a
   stub reads as thin when it is actually just unanswered. Before deciding
   nothing covers a capability, read the front-matter `description` of
   every skill in [`skills/README.md`](../README.md)'s "Current skills" —
   not the titles, the descriptions, which is where each file states its
   own scope.
2. **It belongs in this deployment's conventions doc, not in a skill.** A
   fact about *this* owner, product or host — their vocabulary, an agreed
   cadence, which of two tools they use — lives at `CONVENTIONS_DOC_PATH`
   in `.env`. A skill is portable instruction; the conventions doc is local
   truth. Writing local truth into a skill is how a template picks up
   somebody's particulars.
3. **Nothing.** One command you had to look up once is not a skill. Neither
   is a summary of a thing's own documentation, which will be more current
   at the source than in a copy here. The bar is a future run being
   materially worse off without it, and
   [`skills/specialize-skills`](../specialize-skills/SKILL.md) says it
   plainly: don't manufacture one from routine work just to have written
   one.

And one answer that is not cheaper but is sometimes the *right* one, worth
deciding here rather than after the file is written: **the instructions are
not enough and what the capability needs is runnable code.** Where every
deployment would otherwise rebuild the same scaffold from this file's prose,
[`templates/README.md`](../../templates/README.md) is the one home for what
belongs there and for why that directory exists — including that a template
is owned by exactly one SKILL, which means this decision produces *two*
artifacts rather than replacing the skill with a template. The skill still
owns the judgement; the template owns the shape. Deciding it now is cheaper
than discovering it after writing a file that describes an app.

## The seam test

If a new file survives the check above, it still has to earn its own seam.
Ask what **fact** it is the one home for, and say it in a sentence starting
"this file owns". If that sentence needs an "and" for two unrelated things,
that is two skills. If it can only be written as a restatement of a
neighbour, it is a section of the neighbour.

Then name the boundaries — and this is where a seam has two shapes, which
is worth deciding deliberately rather than defaulting to the first:

- **A two-way seam, between peers.** Either file can plausibly be the one a
  session opens first, so each has to send the reader to the other. The
  [`private-networking`](../private-networking/SKILL.md) /
  [`internal-dashboard`](../internal-dashboard/SKILL.md) pair is the worked
  example: one owns *what it serves*, the other owns *how the owner reaches
  it privately*, each names the other explicitly, and neither restates a
  line of the other's mechanism. Editing the neighbour to add that
  paragraph is part of authoring the new skill, not a follow-up.
- **One-way deference, onto something generic.** A new skill for a specific
  capability routinely leans on a general one — its secrets go wherever
  this deployment's secrets go, its alerts go to the one alert destination
  — and the general file must **not** be edited to point back. It has no
  business knowing which specific capabilities exist, the pointer would go
  stale the day the new skill is deleted as unneeded, and every such edit
  makes the generic file a little more of an index.

The test for which shape you have: would a reader who opened *only* the
neighbour be missing something they needed? If yes it is a peer seam and
the neighbour gets edited. If the neighbour is complete without ever
mentioning yours, the deference is one-way and you are done after writing
your own half.

The failure both shapes prevent is the one the one-home rule is entirely
about: a second file that describes the same mechanism slightly
differently, so a later reader acts on whichever they happened to open. Two
files disagreeing is strictly worse than one file being thin.

## The file shape

A skill is a directory under `skills/` containing `SKILL.md`, with YAML
front matter carrying `name` (matching the directory) and `description`.
Read two finished neighbours end to end before writing — the newest ones
are the most refined, and imitating them is faster than deriving the house
style from rules.

Three things about the shape are load-bearing rather than cosmetic:

- **The `description` is the only part a harness reads before deciding
  whether to load the file at all.** Content behind a description that
  doesn't mention the trigger is unreachable in practice. So write it as
  scope plus trigger: what the file owns, and when to read it. Where the
  file ships with unanswered gaps, say that there too, so nobody mistakes a
  stub for finished instruction.
- **What belongs in the file and what doesn't** is
  [`skills/README.md`](../README.md)'s "What belongs in a SKILL here" — in
  short, portable instructions only, no scheduling mechanics and no
  harness-specific syntax. Read it there; it is the one home for that
  boundary, and a new capability is exactly where the temptation to smuggle
  in a cron line arrives.
- **No wiring per skill beyond the index.** Both harnesses see a new
  directory here immediately, for the reason
  [`skills/README.md`](../README.md)'s "How harnesses discover these"
  explains. Do not add a symlink, a manifest entry, or a copy anywhere.

### What CI enforces, and how to check before you push

`.github/ci/check-skills-consistency.py` is executable, stdlib-only and
runs from anywhere. **Run it before you push, every time.** Its own header
is the one home for which rule exists and why; nothing about its rules is
restated here, because a copy of a checker's rules is the one kind of stale
documentation that fails a build.

Two of those rules are worth knowing *while* drafting rather than after,
because they change what you write rather than how you format it:

- **A file's honesty about itself is machine-checked.** Whether it carries
  unanswered markers, whether it says so in a `Status:` heading, and how
  [`skills/README.md`](../README.md)'s "Current skills" labels it all have
  to agree. You cannot ship a stub that reads as finished, or a finished
  file wearing a stub's heading.
- **Prose that cites another file's numbered step or a named heading is
  checked against that file.** So cite precisely and copy the target's
  wording exactly; an approximate heading name fails the build, which is
  the point — the alternative is a reference that stays confidently wrong
  forever because the link itself still resolves.

The other CI jobs that touch a new skill are the link check, which resolves
every relative link and every external URL, and the symlink check. Neither
needs anything from you beyond correct links: prefer a relative link to a
file in this repo over an external URL, and where an external one is right
(a tool's own documentation, which is more current than any summary here),
link the documentation root rather than a deep page that gets reorganized.

## Stub or finished: decide it, don't default

Most skills here ship as stubs because this repo cannot know the owner's
tracker, channel or host. A skill *you* write during a live deployment is in
a different position: you can often just answer the question. So decide
deliberately, per gap, and let the file say which it is:

- **Answer it now** where you have a real source — a value in `.env`, the
  conventions doc, something you verified by running it. This is the
  default for a skill authored on a configured deployment, and a finished
  file carries no `Status:` heading.
- **Mark it** where a real answer belongs and does not exist yet, using the
  same marker convention every stub here uses. Go and read one in
  [`internal-dashboard`](../internal-dashboard/SKILL.md) for the exact
  shape rather than working from memory of it. A marker is a promise that
  the answer is missing, which is honest; the thing it exists to prevent is
  a plausible placeholder, which is indistinguishable from a real answer
  right up until something acts on it.
- **Record a "no"** where the answer is that this deployment doesn't do
  this. That is a real, complete answer and it needs to read as decided
  rather than unasked, exactly as it does in the stubs that ship here.

A marked file has two consequences you are choosing along with the marker:
it needs its `Status:` heading and its stub label, and it has to become an
item of the specialization pass, or nothing will ever go and answer it.

## Honesty about what you actually did

Everything a new skill claims about this deployment is a claim a later
session will act on without re-checking. So the standard is the one applied
everywhere else here, stated once:
[`skills/specialize-skills`](../specialize-skills/SKILL.md)'s "Rules for
what you write" is the one home for the writing rules, and they apply in
full to a file authored from scratch — one home per fact, no secrets, no
state that isn't real in either time direction.

Three failure modes are specific to authoring rather than specializing.
None of them looks like a mistake in the finished file, which is why they
are worth holding in mind while writing it:

- **Claiming a pattern is proven when it has only been written down.** A
  skill may say a pattern is in production only where it is in production
  on this deployment. Where it is a recommendation you have not run, write
  it as one. The two read almost identically and are worth completely
  different amounts.
- **Describing the capability instead of the operating decisions.** A file
  that restates a vendor's own documentation is worse than a link to it and
  goes stale faster. What a skill is for is the part the documentation
  cannot know: which half is the owner's and which is yours, what is
  irreversible, what has to be verified before anything is reported as
  working, where the local fact lives.
- **Inventing the boundary with the guardrails.** Where a capability
  touches money, credentials, identity, public reach or anything else on
  [`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list, a new skill
  does not get to narrow that list, and must not read as though it had. It
  may state precisely where its own work sits relative to the boundary —
  which is genuinely useful, since "build the payment integration" and
  "charge a customer" fall on opposite sides of one — but the boundary
  itself is that file's, and anything genuinely ambiguous is a stop-and-ask
  rather than a paragraph you resolve here.

## Wiring it in

Two edits always, a third where the seam test above says the seam is
two-way, and a fourth where the skill ships a template. The skill isn't
authored until they're made:

1. **[`skills/README.md`](../README.md)'s "Current skills" entry.** That
   list is the one enumeration of this directory, so a skill missing from
   it doesn't exist as far as every other file here is concerned. One
   bullet, first link pointing at the new `SKILL.md`, a *stub* or *partial
   stub* label if and only if the file carries markers, and the boundary
   with any neighbour named the way the existing entries name theirs.
2. **Its position in the specialization pass.**
   [`skills/specialize-skills`](../specialize-skills/SKILL.md)'s "The stubs
   to specialize" is the one home for the pass order and for why each item
   sits where it does; the index's order follows it rather than the reverse.
   Add the new skill where its dependencies put it — after anything whose
   answers it needs — and say what it is waiting on. A skill with nothing
   to specialize still belongs in that list, as the existing finished
   entries do, so that a pass working through it is told explicitly to
   leave it alone rather than left to guess. Inserting one in the middle
   means renumbering the rest: the list has to stay contiguous, and both
   its order and the index's are machine-checked against each other.
3. **The neighbour's boundary paragraph**, where and only where the seam
   test above found a two-way seam. Skipping it on a peer seam leaves the
   neighbour silently incomplete; adding it on a one-way one is an edit to
   a file that shouldn't know you exist.
4. **[`templates/README.md`](../../templates/README.md)'s "Current
   templates" entry**, where and only where the new skill ships a runnable
   template per the fourth answer above. That list makes the same
   one-enumeration claim about `templates/` that the index in edit 1 makes
   about `skills/`, and it fails the same way: a template missing from it is
   a scaffold the next deployment rebuilds by hand, having never been told
   it existed. The entry names the owning skill, since that file requires
   exactly one. Both halves are machine-checked by the same script the next
   section names.

Then ship it the way every other tracked change here ships, through a
branch and a PR per
[`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md). A skill
authored unattended goes through a scratch clone and not the primary
checkout, for the reason that file's "Which repo are you even in?" section
owns.

## Verify it before you report it

A skill is instructions, so the only real test is whether they can be
followed. Two checks, in order, and neither is optional:

- **Run the consistency checker and the link check.** Green CI proves the
  file is wired in and internally consistent. It proves nothing about the
  content, which is why it is the first check and not the last one.
- **Follow the file once, on something real.** Not a re-read — an actual
  use: do the thing the skill describes, or the smallest genuine piece of
  it, working only from the file. Every gap surfaces here and nowhere
  earlier: a step that assumed a value the file never says where to find, a
  boundary that turns out to be ambiguous in the one case that matters, an
  order of operations that only works in the other order. Then **fix the
  file**, rather than noting the gap somewhere else.

When you report it, say which of those two you did. A skill that has passed
CI and never been followed is unverified prose, and calling it more than
that is the failure
[`skills/internal-dashboard`](../internal-dashboard/SKILL.md)'s reporting
rule describes, in a file rather than on a page.

[`skills/billing-and-payments`](../billing-and-payments/SKILL.md) is the
one skill in this repo authored through this process rather than shipped
with the original set, and it is worth reading as the worked example of the
output: a capability the fixed set does not reach, a seam stated in one
sentence, a file that defers to four neighbours without restating any of
them, and unanswered gaps left marked rather than guessed.
