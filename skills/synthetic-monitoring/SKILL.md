---
name: synthetic-monitoring
description: How this agent continuously re-proves that the product's own user-facing flows still work — picking the flows whose silent breakage would embarrass the business, driving each one the way a user does, proving the real side effect happened rather than that an endpoint answered 200, keeping the test data out of production's numbers, and alerting only when a flow actually broke. Read when standing up monitoring for a product that has users, when a break reached a customer before it reached this agent, and before shipping anything that changes a flow a check covers. Ships as a stub — which flows exist, where their evidence lives and how often to run are per-deployment.
---

# synthetic-monitoring

## Status: STUB — needs specialization

Which flows this product has, where each one's side effect can be read back
from, how often a check runs and what the owner agreed about test data in
production are all facts about *this* deployment. Every
`TODO(specialize)` below marks one, and none of them can be answered from a
template — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

## What this owns

**This file owns proving the product's own user-facing flows still work, on a
schedule, from the outside.** Not whether the deploy landed, not whether the
host is healthy, not whether a container is up: whether a person who came to
do the thing the business exists to do could still do it, and whether the thing
that was supposed to happen behind it actually happened.

That is a different question from every other signal, and it is the one that
fails silently. A health endpoint answers 200 with a broken checkout behind it.
A container is up with a mail credential that expired last Tuesday. A deploy
went green and dropped the one environment variable a form submission needs.
In all three the product is *serving*, and the only thing that notices is a
user who quietly leaves — the business finds out weeks later, from the shape of
its own numbers, or never.

The neighbour and the boundary:

- [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md) owns the deploy
  path, the rollback, the backups, and the **inventory of health signals** this
  deployment has — including which of them need access to the product's host
  and which do not. A synthetic check is one entry in that inventory, and the
  entry belongs there; everything about how to choose, build and operate the
  check is here. Its "Monitoring" section is that inventory's one home, and
  this file does not restate a signal from it.
- **A synthetic check is the strongest available form of that file's "A merged
  change that isn't running is not shipped" rule**, which is why the two are
  worth reading together: a check run right after a deploy answers the question
  that rule asks, about the flow rather than about the revision.
- [`spoor-doctor`](../../spoor-doctor) is the same idea aimed the other way. It
  checks *this agent's own deployment* — its config, its credentials, its
  prompts. Nothing in it looks at the product. Neither one covers the other's
  subject, and a green doctor says nothing at all about whether the product
  works.

## Start from the scaffold, not from a blank page

[`templates/synthetic-check/`](../../templates/synthetic-check/README.md) is a
runnable check runner with one example flow, a toy product to point it at, and
a verification script that breaks that toy product ten ways and asserts the
check catches each one. Copy it and replace the flows; that README is the home
for how to drive it, and everything below is the home for the decisions it
cannot make for you.

It is stdlib-only and needs no host access, which is deliberate: a check runs
from wherever the scheduler is, and dependency drift is a way for a check to
stop running for reasons that have nothing to do with the product.

## Which flows get a check

Not many. A check is code that has to be maintained, and it writes to
production every time it runs, so the bar is high and the list is short —
**one flow, done honestly, is worth more than five that only assert a status
code.** Rank the product's flows by one question, which is the whole test:

**If this broke right now, how would the business find out?** Where the honest
answer is "from a customer, if they bother", or "from the monthly numbers", or
"it wouldn't" — that is a flow worth a synthetic check. Where the answer is "an
exception would appear in the error tracker and someone would be paged", the
check adds much less, and may add nothing.

Three properties push a flow up the list:

- **It is the business's revenue or lead path.** Checkout, signup, the contact
  form that is the only way anyone gets in touch, the booking. A broken one is
  not a degraded experience, it is the business being closed while appearing
  open.
- **It crosses a boundary nothing else tests.** Mail delivery, a payment
  provider, a webhook from a third party, a background worker, a queue, a cron
  job that has to fire. These are exactly the parts a deploy pipeline's tests
  mock out, and exactly the parts that break from the outside — an expired
  credential, a provider's policy change, a suspended sender domain — with no
  deploy involved and therefore no moment anyone was watching.
- **Its failure is invisible from inside.** A form that 200s while the
  notification silently goes nowhere produces no error, no log line and no
  alert. The check is the only thing that would ever know.

And two that push a flow down: a flow whose failure is loud anyway, and a flow
whose side effect genuinely cannot be undone or excluded — see the production
data section below, which is a real reason to check a narrower slice instead.

`TODO(specialize)` — record the flows this deployment actually checks, one line
each: what the flow is, what user does it, and the side effect that constitutes
proof. Record the ones deliberately *not* checked too, with the reason, because
"we considered checkout and it can't be synthesized without a real charge" is a
decision a later reader needs to see was made rather than missed.

## Prove the side effect, not the status code

**A check that asserts on a status code is an uptime ping wearing a costume.**
The failure this whole pattern exists for is the flow that answers 201 and
stores nothing, so a check that would pass against that flow is not a check.
Every flow's assertion has to name a durable artifact and go and look at it:

- the row that now exists, read back from the database or an API over it,
- the notification that arrived, read from the mailbox it was sent to, or from
  the mail provider's own delivery record,
- the queued job that ran, the file that appeared, the webhook the product
  received, the invoice the provider now has.

Two things follow that are easy to skip:

- **The evidence has to be read from where the side effect actually landed**,
  not from the same endpoint that claimed to do it. An API that reports on its
  own writes can be wrong in exactly the way being checked.
- **The evidence read is usually a change to the product**, and that is the
  real work of adopting this pattern rather than an obstacle to it: most
  products have no way for an outside caller to confirm one specific record
  exists. Adding one is ordinary reversible work — a token-gated read scoped to
  the checker's own marked data, never a general-purpose export — and it is
  worth building rather than working around, because the alternative is a check
  that asserts what it can see instead of what matters.

**Assert on the flow being usable, not merely completing.** A signup that takes
40 seconds is broken for the person doing it, so a flow carries its own time
budget, chosen from what its users actually experience. And a check must not be
able to hang: a request with no timeout produces no result, no failure and no
alert, which is indistinguishable from a healthy product.

### Break the product to prove the check

**A synthetic check that has only ever been watched passing is unverified**, in
exactly the sense a rollback procedure that has never been run is
unverified. It is also the easiest thing in this repo to get subtly, invisibly
wrong: a check whose evidence query never matches passes as long as it is
looking for the absence of something, and a check whose assertion is `status ==
200` passes forever.

So each flow's check is proven once, deliberately, by breaking the thing it
watches and confirming the check goes red at the named step. Against a staging
environment where one exists, or against a local copy of the product where it
does not — never by breaking production to see what happens.
[`templates/synthetic-check/verify.sh`](../../templates/synthetic-check/verify.sh)
does this for the example flow and is the worked example of the shape.

Two failures this actually caught while that template was being written, both
of which would have produced a confident alert about a completely healthy
product: an evidence lookup that searched for an identifier the product had
case-folded on write, and a query parameter whose `+` the server read as a
space. Neither is visible by reading the code, and both pass CI.

## Not polluting production

The check writes to the live product on every run, which makes test data an
operational concern rather than a tidiness one. Four defences, and they are
cumulative rather than alternatives:

- **Mark every artifact, in a way the product itself recognizes.** A marker in
  the identifier the flow creates — an address, a reference, a name — plus a
  request header on the traffic. The point of a marker the *product* knows
  about is that its own queries can exclude it: analytics, billing, exports,
  any list a human reads, and above all anything that mails a person.
- **Assert the exclusion, as part of the check.** Whether the product still
  honors the marker is itself a thing that breaks, silently, the first time
  somebody writes a query that forgets it — so a flow reads the number a real
  user would move and proves it did not move. A counter is read long before a
  row is deleted, which is why cleanup alone does not cover this.
- **Clean up what the run created, and verify it is gone.** Immediately, in the
  same run, on the failing path as well as the passing one. A purge that
  answers 200 having deleted nothing is the same class of lie the check exists
  to catch, in the direction of test data quietly accumulating.
- **Never let cleanup be able to delete anything but the check's own marked
  data.** A cleanup affordance that accepts an arbitrary identifier is a new
  way to lose real records, which is worse than the pollution it was added to
  prevent.

**Where a side effect genuinely cannot be undone, do not synthesize it.** An
append-only ledger, an audit log, a real invoice, a message to a real person:
these are not cleanup problems to solve cleverly. Check a narrower slice of the
flow that stops short of the irreversible step, and say in the record that the
last step is unchecked, rather than quietly making the check the thing that
pollutes the product's history.

Two boundaries this section does not get to soften, both of them
[`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list's:

- **A check may not reach a real person.** No message, mail or notification to
  a third party, ever, as a side effect of monitoring — the notification a
  check proves is one delivered to the business's own inbox, and it carries the
  marker in its subject so whoever reads that inbox can tell it apart from a
  real lead at a glance.
- **A check may not move real money.** A checkout flow is checked in the
  provider's test mode against test instruments, or not at all;
  [`skills/billing-and-payments`](../billing-and-payments/SKILL.md)'s "The one
  boundary that matters: building it versus moving money" is the home for that
  line, and a synthetic check sits on the same side of it as any other build
  work.

And one that needs the owner's explicit agreement rather than an inference:
**the cleanup step deletes rows from production**, which is on that same
guardrail list. What makes it legitimate is that it deletes only what this
check itself created moments earlier, and that the owner agreed to that
specific arrangement in words. Prefer whatever soft delete or status flag the
schema already supports over a hard delete, per that list's own instruction.

`TODO(specialize)` — record the marker convention (the exact shape, and where
the product's own exclusion rule that matches it lives), what each flow's
cleanup does, and the owner's agreement to it. Note any flow whose data cannot
be cleaned up and what was checked instead.

## Scheduling, and who notices when the check stops

*How* this runs is the host's, not this file's — see
[`skills/README.md`](../README.md)'s "What belongs in a SKILL here". What
belongs here is what the cadence has to satisfy:

- **At least as often as a break may go unnoticed.** The cadence is a decision
  about how long the business is willing to be silently closed, so derive it
  from that rather than from what feels frequent. Multiply it out first: every
  run writes to production, so a check every five minutes is thousands of
  marked records a week to be excluded and cleaned up.
- **Immediately after a deploy, as well as on the clock.** This is the run that
  earns the pattern its keep — the flow that broke because of a merge is caught
  minutes after the merge, by the session that made it, while the rollback is
  still cheap.
- **Not so often that the alert becomes weather.** An alert that fires on every
  run of a persistent failure gets filtered, and a filtered alert is not
  coverage.

**And the failure mode the cadence itself creates: a check that has stopped
running produces no failures at all.** A crashed job, an expired token, a
host reboot that lost the schedule — every one of them looks exactly like a
healthy product from the outside, and it is the commonest way this pattern
dies. So the absence of a run has to be a signal in its own right: a heartbeat
the check pings only on a successful run, watched by something that alarms on
silence. Something *outside* this check has to be what notices, because a check
cannot report its own absence.

`TODO(specialize)` — record the cadence and the post-deploy trigger, name the
host schedule config that owns them rather than copying a cron line here, and
record what watches for the check's own silence. If nothing does yet, that is
the most load-bearing gap in this file and it belongs on the owner's
self-provisioning shopping list per [`AGENTS.md`](../../AGENTS.md), not in a
hedge.

## Alerting

One destination, and it is not this file's to name:
[`skills/comms-channel`](../comms-channel/SKILL.md) owns where an alert goes,
who may be told what, and how a message to the owner should read. What this
file adds is only what a synthetic failure specifically has to carry:

- **Which flow, and which step of it failed.** "Signup is broken" starts an
  investigation from zero; "signup: the row was written, no notification was
  sent" starts it in the right place. A failure report also carries what the
  run *did* manage to prove before it broke, for the same reason.
- **Once per distinct failure, and once on recovery.** Not once per run while
  it stays broken, and not silently on recovery either — a failure alert with
  no closing message leaves the owner unsure whether it is still happening.
- **A judgment about whether it interrupts**, per that file's "What warrants an
  interrupt, and what doesn't". A revenue flow being down is the clearest
  interrupt this deployment has; a slow-but-working flow usually is not.
- **No payload contents.** A check's own test data is safe by construction, but
  a failure report quoting a response body can carry a real user's data into a
  message and a log. Report the step, the assertion and the identifier this
  check created; never the product's response.

An **unknown** result is not a pass. A check that could not run — no
configuration, an evidence source that would not answer, a broken flow file —
has to be visibly distinct from a check that ran and passed, or the pattern's
whole failure mode has been reintroduced one level up. The
[`templates/synthetic-check/`](../../templates/synthetic-check/README.md)
runner separates the two in its exit codes for exactly this reason.

## What this agent may do about a failure

Nothing here widens what
[`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list allows, and a
synthetic failure is a strong signal but not a mandate. Whether this agent may
act on one unattended — roll back the deploy that preceded it, restart a
container, re-run a failed job — is an autonomy question, so it is
[`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s and the
conventions doc's at `CONVENTIONS_DOC_PATH`, not this file's, and this file
does not restate it.

What is always this file's: **report it, with the evidence, and do not
suppress it.** A flaky check gets fixed or deleted, never quietly tolerated —
a check whose failures are habitually ignored is worse than no check, because
it is the reason the real failure gets ignored too.
