---
name: billing-and-payments
description: How this agent works on a product that takes money from its users — where the line falls between building a payment integration (ordinary reversible work) and moving money (owner-only), the owner/agent split on the payment provider account and its live keys, how the agent gets a test-mode environment to work in at all before that account exists, the provider-is-the-source-of-truth rule for entitlement, the webhook and money-representation constraints that are wrong by default, and what has to be reported rather than retried. Read before touching checkout, subscription, invoicing or entitlement code, and before anything that would issue a charge, a refund or a payout. Ships as a stub — whether this deployment charges anyone, through which provider, and how tax is handled are per-deployment.
---

# billing-and-payments

## Status: STUB — needs specialization

The boundary rules, the owner/agent split and the engineering constraints
below are true of any payment provider and any product. What cannot exist
until a deployment is configured is whether it charges anyone at all,
through whom, and who handles tax. Every marker below has to be answered
before this agent writes billing code — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

This file was authored through
[`skills/skill-authoring`](../skill-authoring/SKILL.md), and is the worked
example that skill names.

## When this applies

The product takes money from its users, or the owner wants it to. Anything
that reads or writes the answer to "has this customer paid, and what does
that entitle them to" is in scope: checkout, subscriptions, one-off
purchases, usage metering that bills, invoices, receipts, dunning, refunds,
entitlement checks in the product's own code.

It does **not** apply to the owner's own spending — the deployment's
hosting bill, a tool subscription, an API's usage cost. Those are the
owner's money going out, and they are governed by
[`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list directly, with
nothing here to add.

## The one boundary that matters: building it versus moving money

These look adjacent and are not, and getting them the wrong way round is
either paralysis or a real incident:

- **Building payment functionality is ordinary, reversible product work.**
  A checkout page, a webhook handler, a subscription model, a pricing page,
  an entitlement check. It ships through the normal branch-and-PR loop in
  [`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md) like
  anything else. It does not need per-change sign-off, and treating it as
  though it did means no product ever gets a way to be paid for.
- **Moving money, or committing to move it, is owner-only** and stops for
  a real yes.
  [`AGENTS.md`](../../AGENTS.md)'s "Spending money or creating a financial
  or legal obligation" guardrail is the home for that rule; this file only
  names where its edge falls in billing work, because the edge is not
  obvious from the guardrail's own wording. On the owner-only side:
  issuing or cancelling a charge against a real customer, issuing a
  refund, responding to a chargeback or dispute, changing a live
  customer's price or plan, applying a discount or credit, triggering a
  payout, and switching an integration from test credentials to live ones.

The distinction is not "is this risky code" but **does this action, taken
now, move real money or bind the owner to something.** Shipping code a
customer later chooses to pay through is the first kind. Running a script
that charges that customer is the second, and it stays the second even when
the code that does it was reviewed, merged and working.

Where a specific case is genuinely ambiguous — a data fix that happens to
change what somebody will be billed next cycle — it is a stop-and-ask, not
a judgment call to make here and record afterwards.

## First: what does this product already have?

Same shape as an inherited stack or an inherited deploy pipeline, and it
settles the same way — see
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md)'s "When the
product repo already exists and doesn't match", which is the home for that
reasoning. **What is already there keeps its job.**

A product that already takes money already has a provider, an account, a
set of live keys and, most importantly, live customers with live
subscriptions against it. Migrating that is not a refactor: in-flight
subscriptions, stored payment methods and dispute history do not move
cleanly, and the failure mode is customers who are charged twice or not at
all. So read before proposing anything:

- the product's own dependency manifest, for a provider SDK,
- its environment configuration, for key names (**names only** — never read
  a live secret value into a session that doesn't need it),
- its schema, for whatever table holds customer or subscription state,
- its webhook routes.

If an integration exists, use it and record it. A second provider alongside
the first means two systems both believing they know who has paid, which is
the one thing this file's central rule exists to prevent.

**All four of those checks can come back empty and still be the wrong
answer**, because they look for the incumbent inside the product's code,
and on a small business it is routinely outside it: the owner raising
invoices by hand in an accounting package, taking bank transfers, and
flipping a flag in an admin screen when one lands. That is a payment system
with a source of truth, and adding a provider to it creates exactly the
two-systems duplication above — invisibly to every check listed here. So
ask the owner directly how money reaches them today, rather than concluding
from the repo that nothing does, and where the answer is a manual process:

- name who does it and in which system, since that person is about to have
  their job partly automated and is the one who knows what the flag means,
- treat the change as a cutover rather than a feature, with a dual-running
  period, one named person reconciling the two during it, and the manual
  path **deleted** afterwards rather than kept as a fallback,
- and don't move existing customers onto the provider as part of building
  it. Their payment method changing is the owner's decision to make and
  announce, not a side effect of a merge.

## The owner/agent split

Split this before starting, because the halves land on opposite sides of
the guardrail list, and the owner's half has lead time measured in days.

**The owner's, and not yours to do**: creating the provider account,
completing its identity and business verification, connecting a bank
account, accepting the provider's terms, and holding the live API
credentials. Every one of those is either registering an identity or
accepting a legal obligation, both owner-only per
[`AGENTS.md`](../../AGENTS.md)'s "Self-provisioning: the shopping list".
Ask for them as shopping-list items. Never drive a signup, never complete a
verification form on the owner's behalf, and never accept terms.

**Yours**: designing and building the integration against the provider's
test mode, the webhook handler, the entitlement logic, the product surfaces
that display price and status, and the reconciliation check below.

**Test mode is the whole of the agent's working environment here**, and the
switch to live credentials is the owner's action, in the owner-only list
above. It is worth being explicit about why, since test mode is otherwise
easy to treat as a formality: a test-mode key cannot charge a real card, so
every mistake made behind one costs nothing, and the same mistake behind a
live key is a real customer's real money and a refund the agent is not
allowed to issue.

Where the live keys live once they exist is not this file's business:
[`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s "Secrets"
is the one home for how this deployment handles secrets, and a payment key
is an ordinary secret under it.

## Before the owner's account exists

The split above puts the account on the owner's side, and identity and
business verification have lead time measured in days. Which raises the
question the split does not answer: **the agent's working environment is
test mode, so who provisions the test credentials?** Not asking it produces
two wrong answers — sitting idle for a week on work that touches no real
money, or quietly provisioning a credential, which
[`AGENTS.md`](../../AGENTS.md)'s "Registering accounts or identities
anywhere" guardrail forbids without exception.

The right answer is that test credentials are **their own shopping-list
item**, asked for separately from the account and ahead of it. They unblock
all of the agent's work and none of the owner's lead time applies to them,
so bundling them into "set up the provider" delays everything behind a
verification queue for no reason. Some providers now issue a test-only
sandbox to a coding agent with no account registration at all, which makes
that item a single command the owner runs — a far cheaper ask, worth
presenting as one, and still theirs to run rather than yours. A
credential-issuing endpoint built for convenience does not narrow that
guardrail, and the argument that it does is the shape of reasoning the
guardrail exists to refuse.

Two things are worth doing while that item is outstanding, rather than
waiting:

- **Find out whether the provider publishes instructions written for
  coding agents**, as distinct from documentation written for people —
  several now ship a maintained, machine-readable set. Where one exists it
  is the source for every API mechanic this file deliberately doesn't
  carry, and it is strictly better than either a summary here or a page of
  prose docs, because it stays current without anyone here noticing it
  should have. Read it before writing a line about the provider's API.
- **Work at the rung below a sandbox.** Several providers publish a local
  mock of their own API that needs no credentials, which is enough to
  exercise request shape and a client's auth wiring. What that rung cannot
  prove is specific and dangerous, and "Verifying it, honestly" below is
  the home for it.

## The provider is the source of truth; your database is a cache

This is the rule the rest of the engineering follows from. The provider
knows whether a payment succeeded, whether a subscription is active, and
whether a card was declined. Your own records are a local copy of that,
useful for speed and for joins, and **wrong whenever the two disagree**.

In practice:

- **Derive entitlement from provider-confirmed state**, not from the fact
  that your own checkout code ran. A user who reached your success page has
  not necessarily paid — they closed the tab mid-redirect, the payment is
  pending, the card was declined asynchronously. Grant access on
  confirmation, not on intent.
- **Never reconstruct money from your own arithmetic** when the provider
  will tell you the amount. Currency conversion, tax, discounts, proration
  and fees are the provider's calculation; recomputing them locally
  produces two numbers that differ by a cent and an argument with a
  customer you cannot win.
- **When the two disagree, the provider wins and a human hears about it.**
  A mismatch is not a thing to quietly correct in either direction; it
  means something upstream is broken.

### The webhook handler, which is wrong by default

Every constraint here is a real failure that the obvious implementation
has:

1. **Verify the signature on every delivery, before parsing the body.** An
   unverified webhook route is a public, unauthenticated write path into
   billing state — anyone who learns the URL can mark themselves paid. The
   provider's own documentation is the one home for how its signature
   scheme works; read it there, and read what it says about *which*
   signatures in the header to check. At least one provider deliberately
   sends an extra signature under a scheme that cannot verify, as a test
   aid, and tells you to ignore any scheme it doesn't name — so a handler
   written to require every signature present to verify fails in test mode
   and passes in live, which is the one polarity guaranteed to waste a day.
2. **Be idempotent, keyed on the provider's own event id** — and on nothing
   else that looks equivalent. Duplicate delivery is normal and documented
   behaviour, not an anomaly, and a handler that grants a month of access
   per delivery grants three. The event id is the only stable key: a retry
   of the same event is commonly re-signed with a fresh timestamp, so
   dedupe keyed on the signature, on the raw header, or on a hash of the
   delivery silently doesn't dedupe at all, and passes every happy-path
   test while doing so.
3. **Assume out-of-order and late arrival.** A cancellation can land before
   the creation it cancels. Reconcile against the object's current state
   rather than applying events as a sequence of deltas, and don't order
   events by the timestamp in the payload — providers say outright that it
   isn't an ordering key, and two events can carry the same one.
4. **Return quickly, and do the slow part elsewhere.** Providers retry on
   timeout, which turns one slow handler into a retry storm against the
   same endpoint. The failure that matters is not the latency: it is that
   every retry is another delivery, so a slow handler multiplies whatever
   constraint 2 was there to prevent. Which is also the order to fix them
   in — idempotency makes a slow handler merely slow, and a fast handler
   without it is still wrong.
5. **Never trust amounts, plans or customer identity from anything other
   than a verified provider payload** — least of all from the client. Price
   arriving from the browser is the oldest bug in this domain.

### Representing money

- **Integer minor units** (cents), never a float. A float will eventually
  produce a total that is a cent off, and every such bug is found by a
  customer.
- **Currency travels with the amount**, always, even in a single-currency
  product. Adding the second currency later to a schema that assumed one is
  a migration across live financial records.
- **Store what the provider charged, not what you intended to charge.**
  They differ, legitimately, through proration and tax.

### Card data never reaches this product

Use the provider's hosted checkout or its client-side field components, so
card numbers go from the customer's browser to the provider and never
through a server here. This is not only a security preference: accepting
raw card details would put this product's own infrastructure in scope for
payment-industry compliance auditing, which is a burden the owner has not
agreed to and this agent cannot discharge. Any design that has a card
number touching this code is the wrong design, however convenient the form
looks.

## Reconciliation, and what has to be reported

Billing fails quietly by nature: nobody notices unbilled usage, and the
customer who was wrongly charged notices before you do. So it needs an
active check rather than an absence of alerts.

- **A scheduled reconciliation pass**, comparing local entitlement state
  against the provider's own record, reporting differences rather than
  fixing them silently. Where a difference is safe to auto-correct in one
  direction, correcting it and still reporting it is the right shape;
  correcting it silently is how a systematic bug runs for a month. **Which
  direction is safe is a fact about the business, not a billing
  default** — revoking access nobody is paying for is the obviously
  conservative move right up against a product whose users have a deadline,
  where wrongly revoking is the expensive error and the safe pass is
  report-only. Ask rather than assuming the obvious direction, and record
  the answer.
- **A failed or declined payment is a report, not a retry loop.** The
  provider's own dunning handles retries. What it cannot do is tell the
  owner that a customer is about to churn.
- **Where a report goes** is not this file's decision:
  [`skills/comms-channel`](../comms-channel/SKILL.md) owns the single alert
  destination and, in its "What warrants an interrupt, and what doesn't"
  section, whether a given event interrupts or waits for a digest. A
  billing event is loud by domain, not automatically urgent — a dispute
  with a deadline interrupts, a monthly reconciliation summary does not.

Scheduling that pass is out of a SKILL's scope, per
[`skills/README.md`](../README.md). Point at the host schedule config.

## Verifying it, honestly

Test-mode verification is real verification of the code and no verification
at all of the money. But there are four rungs here rather than two, and the
two easy to miss are the ones an agent waiting on the owner's account is
actually standing on. In increasing order of what they prove:

1. **The provider's own published instructions**, per "Before the owner's
   account exists" above. Proves nothing was invented. Proves nothing about
   this integration.
2. **A credential-free local mock of the provider's API.** Proves request
   shape and that a client authenticates at all. Proves **nothing** about
   amounts, state, entitlement or money — and lies convincingly while
   doing so, because a mock returns canned fixture values for anything it
   doesn't derive. An amount or a tax total echoed back by one is not a
   calculation, and a flow that "worked" against one may have kept no state
   whatever. Schema validation is not business validation either: a mock
   that type-checks a field will happily accept a nonsensical value in it.
3. **The provider's test mode or sandbox**, with real test credentials.
   This is the rung that verifies the integration, and the bullets below
   are what to do on it.
4. **Live**, which is the owner's action and the first evidence about
   money.

On rung 3, both halves have to be said separately:

- **Exercise the full path in test mode**: a checkout completed with the
  provider's test instruments, the webhook actually delivered and verified,
  entitlement actually granted, then a cancellation, then entitlement
  actually revoked. Assert on the state that resulted, not on the HTTP
  status of each hop.
- **Replay a duplicate and an out-of-order delivery** deliberately. Those
  are the two failures that never appear in a happy-path test and always
  appear in production.
- **Say what test mode did not prove.** It did not prove a real card is
  accepted, that the provider's live account is out of review, that payouts
  reach the bank, or that tax is calculated correctly for a real customer's
  jurisdiction. The first real charge is the owner's action and the first
  real evidence; until it happens, "the integration is verified in test
  mode" is the honest sentence and "billing works" is not.

## Tax, invoicing and what the owner owes somebody

**This is a legal question with an engineering surface, not an engineering
question.** What has to appear on an invoice, which tax applies to a
cross-border digital sale, whether the owner must register for it, and how
long records must be retained are all determined by the owner's
jurisdiction and their customers', and getting them wrong is the owner's
liability rather than a bug.

So the agent's job is to implement whatever the owner (or their accountant)
specifies, and to raise the question early — the answer changes the data
model, so discovering it after launch is a migration across live records.
Most providers sell a tax product that handles calculation and the
compliance filing behind it; whether this deployment uses it, or the owner
handles tax outside the product entirely, is exactly the kind of decision
that has to be recorded rather than assumed.

Never present a tax or compliance conclusion as settled on the owner's
behalf. Naming the question precisely and saying it is unanswered is
correct and useful; answering it from a model's recollection of tax law is
the worst available outcome, because it looks like advice.

## `TODO(specialize)`

Record, concretely:

- **Whether this deployment's product charges anyone at all**, and if not,
  that it deliberately doesn't yet. "Nothing is sold yet, so no provider
  and no integration" is a real, complete answer and the expected one on
  first boot. It is an interview answer rather than something to decide
  here, and its home is this deployment's conventions doc at
  `CONVENTIONS_DOC_PATH` in `.env`, which records it along with the fact
  that this file is the home for the mechanism when that changes — read it
  there. Everything below is moot until that answer is yes.
- **Which provider, and whose account it is** — including whether the
  account already exists with live customers on it, per the
  what-already-exists check above, since that changes every later answer.
- **What is actually sold**, in the provider's own vocabulary: one-off,
  subscription, usage-metered, or a mix. Name the objects that exist today,
  not a pricing model nobody has agreed to — an invented plan name is the
  invented specific this repo's specialization rules forbid.
- **Which payment methods are accepted, and customers in which
  countries.** Not a detail of the above: it decides whether a dispute can
  even happen (some bank-transfer and bank-redirect methods cannot be
  charged back at the customer's bank at all, which makes the refund the
  whole of the remedy and the dispute question moot), how long a refund
  takes to settle, whether a recurring charge needs a mandate set up by a
  separate first payment, and the shape of the tax question below. Record
  the methods actually enabled, not the ones the provider supports.
- **Where the credentials live**, by the name of the environment variable
  that holds each of the test and live keys and the webhook signing secret,
  never the value, and never in this file if this deployment's secrets home
  is elsewhere.
- **How entitlement is stored and checked** in the product's own code: the
  table or field that holds it, and the one place that reads it. If there
  is more than one such place, that is a finding to report, not a list to
  write down here.
- **Who handles tax and invoicing**, per the section above, and whether the
  provider's tax product is in use. An unanswered tax question belongs on
  the shopping list, not hedged into a paragraph here.
- **Who executes a refund or a dispute response**, given it cannot be this
  agent: the named human, and how the agent hands one to them.
