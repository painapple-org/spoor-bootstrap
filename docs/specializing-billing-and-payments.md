# Specializing billing-and-payments, for a business that charges people

[`skills/billing-and-payments`](../skills/billing-and-payments/SKILL.md)
shipped as a stub, and it shipped with its own
[`TODO(specialize)`](../skills/specialize-skills/SKILL.md) markers
deliberately unanswered, on the honest grounds that no deployment had
specialized it yet. This file is the first deployment to actually try, and
it exists because
[`skills/skill-authoring`](../skills/skill-authoring/SKILL.md)'s "Verify it
before you report it" demands exactly this and nothing less: follow the
file once, on something real, working only from the file, then fix the file
rather than noting the gap somewhere else.

It found eight things wrong or missing. They are fixed in
`billing-and-payments` and `skill-authoring` themselves; this document
records how each was found, so the fixes can be argued with rather than
taken on trust.

**Which half of this is real, stated up front**, because this file is a
hybrid and the two worked-example shapes already in this directory are not:

- **The business is fictional**, like the three in
  [`example-walkthrough.md`](./example-walkthrough.md) and its two
  siblings. Every answer attributed to its owner below is a plausible
  reconstruction, not a recording, and none of it is a default for anyone
  else.
- **The verifications are real runs**, like
  [`live-fire-github-pages.md`](./live-fire-github-pages.md). Where this
  file says something was checked, a command ran and its output is quoted.
  Where it says something was reasoned about, nothing ran and it says so.
  The four rungs of that ladder, and what each one genuinely proves, turned
  out to be finding 2.

Where this file and a `SKILL.md` disagree, the SKILL wins. The corrections
this exercise produced were written into the skills precisely so nobody has
to read this file to get them.

---

## 1. The business

**Duimstok** — two people in Utrecht. The product is a web app that Dutch
and Belgian physiotherapy practices use to assemble and submit their annual
quality-registry export: the practice's own records go in, a validated
submission file comes out, and the thing they used to pay a consultant two
days for takes an afternoon.

**The software.** `duimstok`, built eighteen months ago by a freelancer who
is still occasionally reachable: FastAPI, Postgres, Next.js, docker-compose
on a single VPS. Which stack it is, and what happens when an inherited one
disagrees with this repo's, is
[`skills/product-tech-stack`](../skills/product-tech-stack/SKILL.md)'s
subject and deliberately not this document's — it is named here only
because the entitlement question in section 7 lands in that code.

**The owner.** Marloes Ottevanger, who managed a practice for nine years
before this. She reads SQL, follows terminal instructions exactly, and does
not write code. She is the only person who has ever touched the money.

**How money works today, which is the part that matters here.** 34
practices pay €85 a month, 31 in the Netherlands and 3 in Belgium. Marloes
raises the invoices monthly in her accounting package, they pay by bank
transfer, and when a payment lands — or conspicuously doesn't — she opens
the app's admin and flips that practice's `is_actief` boolean by hand. That
is the entire billing system. There is no payment provider, no card on
file, no subscription object anywhere, and no automated relationship
between "has paid" and "can use the product".

**What she wants.** Self-serve monthly subscriptions, paid by iDEAL or
card, so that signing up a practice stops requiring her. She is not trying
to change the price, the plan, or the invoice her accountant expects.

---

## 2. What already exists — and the first thing the stub got wrong

`billing-and-payments`' "First: what does this product already have?" sends
you to read four things: the dependency manifest for a provider SDK, the
environment config for key names, the schema for customer or subscription
state, and the webhook routes. All four came back empty. `pyproject.toml`
has no payment dependency, `.env.example` has no key resembling one, the
schema's `practices` table holds `is_actief` and nothing else money-shaped,
and there are no webhook routes at all.

By that section's own logic the answer is "no integration exists, so build
one" — and that is a wrong reading of Duimstok, arrived at by following the
file correctly.

Because something *does* already believe it knows who has paid. It is
Marloes, her accounting package, and a boolean she maintains by hand. The
section's whole point is that "a second system that also believes it knows
who has paid" is the failure to avoid, and it looks for that second system
in the product's own code — where, in the commonest starting state for a
small business, it has never been. The incumbent is a human with an
accounting package, and introducing Stripe creates exactly the duplication
the section exists to prevent, invisibly to every check it lists.

That is **finding 7**, and the fix in the file is a short addition to that
section: check for money being collected *outside* the product, name who
does it and in which system, and treat the cutover as a cutover — with a
dual-running period, a named person reconciling the two during it, and the
manual path deleted afterwards rather than left as a fallback.

For Duimstok that shapes the plan concretely: the 34 existing practices are
**not** migrated onto Stripe by this work. They keep paying by transfer.
Stripe takes new sign-ups only, until Marloes has seen a few months of it
work, and migrating the existing 34 is a separate decision with her name on
it. Nobody's payment method changes because an agent shipped a feature.

---

## 3. The provider, and who chooses it

The stub is right that this is the owner's decision and not the agent's,
and it is worth being precise about why, because it is not deference for
its own sake: the account is in her name, she accepts the terms, the fees
come out of her revenue, and she is the one who cannot walk away from it
cheaply.

So the agent's job was to put a decision in front of her, not to make one.
Two candidates, both realistic for a Dutch business selling monthly
subscriptions in euros to NL and BE customers:

- **Mollie** — Dutch, iDEAL-first, Dutch-language support and Dutch-market
  defaults, subscriptions via SEPA Direct Debit. See
  [Mollie's documentation](https://docs.mollie.com/).
- **Stripe** — subscriptions, invoicing and a tax product as first-party
  features, iDEAL and SEPA Direct Debit among the supported methods for
  recurring payments. See [Stripe's documentation](https://docs.stripe.com/).

Marloes picked Stripe, on the strength of the subscription lifecycle being
a first-party product rather than something the integration assembles, and
one thing she asked about directly: whether the agent could work on it
without her being in the room for every step. Which turned out to be the
most interesting question of the exercise.

The agent explicitly did **not** compare transaction fees for her. Two
percentage points on €2,890 a month is a real number and it is hers to
weigh against everything else she knows about her own business; the pages
that quote it are the providers' own and they change.

---

## 4. How the agent gets into test mode at all — finding 1

The stub's owner/agent split is clear about the live half: the owner creates
the account, completes verification, connects the bank, accepts the terms,
and holds the live credentials. It is equally clear that "test mode is the
whole of the agent's working environment here".

What it never says is **who provisions the test credentials**, and following
it leaves you with two readings, both wrong:

- **Wait for the owner.** Test keys arrive with the account, the account
  arrives after identity and business verification, and that has lead time
  measured in days. So the agent is idle for a week on work that touches no
  real money at all.
- **Provision one yourself.** Which is a breach of
  [`AGENTS.md`](../AGENTS.md)'s "Default guardrails" — the "Registering
  accounts or identities anywhere" item, which says it holds without
  exception, and "Self-provisioning: the shopping list", which names
  generating an API key as explicitly the human's job.

That gap is uncomfortable rather than theoretical, because the second
reading has recently become genuinely tempting. Stripe's own sandbox
documentation now addresses coding agents directly, and says a sandbox with
working API keys can be provisioned with **no account registration at all**
— the CLI's own help text for that command, read tonight from the released
binary, describes it as a proof-of-work challenge with a browser fallback:

```
$ ./stripe sandbox create --help
Create a new Stripe sandbox with test API keys.
...
Otherwise, uses a proof-of-work challenge to provision a temporary sandbox
without authentication. If that fails, automatically falls back to
browser-based signup/login.
```

**That command was not run.** No email, no browser and no KYC does not add
up to no account: it provisions a resource at a third party and it issues a
credential, which is the letter of the guardrail, and the guardrail says
without exception. AGENTS.md's own instruction for a case its authors could
not have anticipated is to name the conflict rather than resolve it in
either direction, so it is named here and the command stayed unrun.

The fix in the file is a new short section giving test credentials their own
owner/agent split, and it makes three points the stub had no place for:

1. Test credentials are a **separate shopping-list item** from the account,
   asked for separately, because they unblock all of the agent's work and
   none of the owner's lead time applies to them.
2. Where the provider issues them without registration, that item is one
   command the owner runs — a far cheaper ask than the account, and worth
   presenting as such rather than bundling into "set up Stripe".
3. Running it yourself is still a stop-and-ask. A credential-issuing
   endpoint built for convenience does not narrow AGENTS.md's list, and the
   claim that it does is the shape of reasoning that guardrail exists to
   refuse.

Everything from section 5 on was therefore done at the rung *under* a
sandbox, which is where finding 2 came from.

---

## 5. What is verifiable with no credential at all — finding 2

The stub's "Verifying it, honestly" section has two rungs: test mode, which
verifies the code, and live, which is the first evidence about the money.
There are four, and the two it is missing are the two an agent blocked on
the owner will actually be standing on.

### Rung 1: the provider's published instructions for agents

Checked, and it is not a rhetorical rung. Stripe publishes a machine-
readable index of skills written for coding agents, fetchable with no
account:

```
$ curl -s https://docs.stripe.com/.well-known/skills/index.json | python3 -c ...
8 skills, 3 of them:
- stripe-best-practices | Guides Stripe integration decisions across API selection (Checkout Sessions vs PaymentInte…
- stripe-docs           | Use when the user or agent needs to read, search, or look up Stripe documentation or API r…
- upgrade-stripe        | Guide for upgrading Stripe API versions and SDKs
```

This matters more than a convenience: it is a *maintained* source for
exactly the API mechanics a skill file here must not restate. The stub
already says the provider's documentation is the one home for its signature
scheme; a vendor-maintained agent skill is a stronger form of the same
argument, since it updates without anyone here noticing it should have.
That is **finding 3**, fixed in two places — a line in
`billing-and-payments` telling the reader to look for one before writing a
word about the provider's API, and a sharpening of `skill-authoring`'s
"Describing the capability instead of the operating decisions" failure mode,
which previously warned only against restating documentation.

### Rung 2: a local mock of the provider's API

[`stripe-mock`](https://github.com/stripe/stripe-mock) is a container that
serves the real API's schema with no credentials and no account. Run
locally tonight in a container on a scratch port — written `PORT` below,
since other agents were working on the same box — it answers real requests.
Responses are shown as the field subset a `python3 -c` filter picked out of
the real JSON, not reformatted by hand:

```
$ curl -s -o /dev/null -w '%{http_code}' http://localhost:PORT/v1/prices
401

$ curl -s -X POST http://localhost:PORT/v1/prices -u sk_test_123: \
    -d unit_amount=4900 -d currency=eur -d recurring[interval]=month -d product=prod_x
{'object': 'price', 'unit_amount': 4900, 'unit_amount_decimal': '2000',
 'currency': 'eur', 'recurring': {'interval': 'month', ...}}
```

Two real facts out of that, both useful:

- The API refuses a credential-free request, so a client's auth wiring can
  be exercised at this rung. It accepts *any* `sk_test_` string, so nothing
  about credential validity can be.
- Note `unit_amount_decimal`. The request said 4900 and the response
  volunteers an unrelated `'2000'` next to it, because this rung returns
  **canned fixture values** for anything it does not derive. On the same
  container, a checkout session created with `automatic_tax[enabled]=true`
  came back with `total_details.amount_tax` of `1424534716` — a number with
  no relationship to anything requested.

That is the rung's specific lie, and it is a dangerous one in this domain
precisely because it looks like a passing test: an agent can watch a
"payment" produce an "amount" and a "tax" and conclude a flow works, when
nothing was computed and no state was kept. Schema validation is also not
business validation — the same container accepted `unit_amount=-100`
without complaint.

So rung 2 proves request shape and client wiring, and proves nothing about
amounts, state, entitlement or money. All three sentences are in the file
now.

### Rungs 3 and 4

A provider sandbox with real test keys (blocked on section 4) is where a
checkout is really completed, a webhook is really delivered, and
entitlement really changes. Live is where a real card, a real payout and a
real customer's real tax jurisdiction are first evidence of anything. The
stub already said the second of those well; it now says all four in order,
with what each cannot prove.

---

## 6. The five webhook constraints, as Duimstok's answers — finding 4

The stub names five constraints and calls the obvious implementation wrong
by default. Following it meant producing each failure on purpose and then
preventing it, which was done in a local exercise: a stand-in provider that
signs deliveries the way [Stripe's webhook
documentation](https://docs.stripe.com/) describes, and two handler
variants per constraint. 17 expectations, all met. The exercise was not
committed to this repo, for the reason
[`live-fire-github-pages.md`](./live-fire-github-pages.md) gives about its
own toy app: it is a test subject, not a deliverable of a bootstrap
template.

**1. Verify the signature before parsing.** Duimstok's handler rejects an
unsigned delivery, a body tampered with after signing, and a validly signed
delivery whose timestamp is outside tolerance — the first two obviously,
the third because the timestamp is inside the signed payload and therefore
the only defence against a captured-and-resent delivery.

One documented detail is worth the whole exercise: **Stripe deliberately
sends an extra signature under a bogus `v0` scheme for test-mode events**,
and its documentation says to ignore any scheme that is not `v1` to prevent
downgrade attacks. A handler written to require every signature in the
header to verify therefore fails in test mode and works in live — a
polarity that punishes precisely the environment the stub tells the agent
to spend all its time in. The exercise reproduces it: the same handler code
accepts a test-mode header carrying `v0` and `v1`, and a live-mode header
carrying only `v1`.

**2. Idempotent, keyed on the provider's event id.** Three deliveries of one
event id grant one month; with dedupe removed, the same three grant three.
The sharpening the exercise produced is about the *key*: Stripe's docs say a
retry generates a new signature and timestamp, and that `created` must not
be used to order events or to decide whether one has been seen. The
exercise confirms one event id arriving under three distinct signature
headers. So dedupe keyed on the signature, the header, or a hash of the
delivery silently doesn't — which is a bug that passes every happy-path
test. The stub said "keyed on the provider's own event id" and was right;
it now also says which three plausible keys are wrong.

**3. Out-of-order and late arrival.** Duimstok's cancellation event is
delivered *before* the creation it cancels. The handler that reconciles
against the subscription's current state ends correctly inactive. The
handler that applies events as deltas ends active — a cancelled practice
with working access, found by nobody until it is found by an audit.

**4. Return quickly.** Simulated with a provider that gives up waiting and
retries: a handler doing its work inline is delivered to three times and
grants three months. The same slow handler with constraint 2 in place is
delivered to three times and grants once. The handler that enqueues and
returns is delivered to once. Two things follow, and the file now says
both: constraint 4's real failure is amplification of everything else
rather than latency, and constraint 2 is what makes a slow handler
*wrong* rather than merely *slow*.

**5. Never trust amounts, plans or identity from anything but a verified
payload.** The exercise forges a signed event claiming the free plan at one
cent for a practice the provider says is on €85/month. The handler that
reads the body records one cent. The handler that refetches the
subscription records 8500 and the real price id. Duimstok's rule, written
down: the webhook body is a *notification that something changed*, and
every value acted on comes from a refetch.

---

## 7. Money, entitlement, and the second reader

**Integer minor units** is the one convention the stub states that turned
out to be enforced by the provider rather than merely advisable. Probing
rung 2 with an arbitrary €49.00, every decimal spelling of it was refused
by the API's own schema:

```
unit_amount=4900     -> accepted
unit_amount=49.0     -> Request validation error: ... 'unit_amount' ... value is not numeric
unit_amount=4900.00  -> Request validation error: ... 'unit_amount' ... value is not numeric
unit_amount='4900'   -> Request validation error: ... 'unit_amount' ... value is not numeric
```

Duimstok stores `amount_cents` as an integer and `currency` alongside it,
including on the euro-only path, and stores what the provider's invoice
says rather than what €85 ought to be. The three Belgian practices are why
the currency column is not hypothetical the day a Swiss one signs up.

**The provider is the source of truth**, and the stub's sharpest claim —
that reaching a success page is not evidence of payment — is directly
observable at rung 2. A checkout session, freshly created, reports itself:

```
{'object': 'checkout.session', 'mode': 'subscription',
 'payment_status': 'unpaid', 'status': 'open', 'amount_total': None}
```

`unpaid`, `open`, and no total. Everything a naive success-page handler
would grant access on, the provider is explicitly declining to assert yet.

**Where entitlement lives, and the finding the stub asked for.** The stub
says to record the one place that reads entitlement, and that more than one
is a finding to report rather than a list to write down. Duimstok has two:
an API dependency that guards the app's own routes, and the nightly
export-builder job, which checks `is_actief` separately. Reported to
Marloes as such, with the recommendation that the export job stop asking
and the guard become the single reader — because the *interesting* failure
is not an inactive practice using the app, it is a paying practice whose
export silently stops being built four days before a filing deadline.

That asymmetry also settles the reconciliation question the stub leaves
open. It says a difference safe to auto-correct in one direction may be
corrected, provided it is still reported. For Duimstok the safe direction
is not the obvious one: revoking access from a practice Stripe says has
cancelled is the *dangerous* correction during the annual filing window,
and the nightly pass therefore reports without correcting between January
and the deadline, and corrects in that one direction outside it. Which
direction is safe is a business fact, not a billing default, and the file
now says so in as many words. That is **finding 8**.

---

## 8. Tax, which the agent named precisely and refused to answer

The stub calls this a legal question with an engineering surface and says
never to present a conclusion as settled on the owner's behalf. Followed
literally, that is not a hedge — it produced a specific list of things
Marloes has to get from her accountant, each of which changes the data
model, which is why it went to her before any billing code was written:

- What must appear on the invoice a practice receives, and **who issues
  it** — the provider's invoicing, or her accounting package as today. This
  one is load-bearing beyond tax: two systems issuing invoices with two
  numbering sequences is a bookkeeping problem that outlives the feature.
- Whether the provider's tax product is enabled or her accountant handles
  tax outside the product entirely.
- The three Belgian practices. A cross-border EU B2B sale is a different
  question from the 31 domestic ones, and the agent's job was to notice
  that the number three is not zero, not to answer it.
- Whether her customers' own VAT position changes anything about what
  Duimstok must charge or show them, healthcare being a sector where that
  question comes up at all. Note what the agent did *not* do here: state
  what that position is. It does not know, this is exactly where a model's
  recollection of tax law is worse than silence, and naming the question
  is the whole of the contribution.
- Record retention: how long, and where.

One more owner-side item surfaced from the provider's own documentation
rather than from tax law: accepting iDEAL as a Netherlands-established
business carries a scheme requirement to display the company's KVK
registration number on the site. That is an owner action on a page, found
while reading about a payment method, and it belongs on the shopping list
next to the rest.

All of the above is on Marloes' shopping list, addressed to her accountant,
with nothing resolved in the meantime. Per
[`AGENTS.md`](../AGENTS.md)'s "Self-provisioning: the shopping list", an
open decision recorded as a question is honest; one quietly resolved on the
owner's behalf is the failure that section exists to prevent.

---

## 9. Refunds, disputes, and the question that turned out to be moot

Findings 5 and 6. The stub's last marker asks which named human executes a
refund or a dispute response, since the agent may not, and how the agent
hands one to them.

The answer for Duimstok is Marloes, in the provider's dashboard,
personally. The agent's job is the handoff: a message on the comms channel
naming the customer, the invoice id, the amount, what the agent believes
happened and what it recommends — and then nothing until she has done it.

The stub's owner-only list names "responding to a chargeback or dispute"
alongside refunds, and reading the provider's own documentation for the
payment methods Duimstok is about to enable produced a genuine surprise:
**iDEAL payments cannot be disputed at the customer's bank at all.** For a
practice that signs up and pays that way there is no chargeback path to
respond to; the whole of the remedy is a refund, which has its own window
and can sit pending for days after it is issued. For a card payment the
dispute question is real and has a deadline attached, which is the example
the stub uses for a billing event that interrupts rather than waiting for a
digest.

So which of "who handles a refund" and "who handles a dispute" is
load-bearing depends on the payment methods in use, and on one of them the
second question does not exist. `billing-and-payments` now says that, and
it produced **finding 6**: the stub's own `TODO(specialize)` list asks what
is sold and in which vocabulary, but never asks **which payment methods,
and customers in which countries** — despite that answer determining
dispute exposure, refund mechanics, whether a mandate is needed, and the
shape of the tax question in section 8. It is a marker now.

---

## 10. What this exercise did not prove

Kept separate deliberately, because the stub's own standard for this is the
strictest thing in it:

- **No money moved, and none could have.** No account exists, no live
  credential exists, no charge was issued and no customer is real.
- **No provider sandbox was reached.** Section 4 is why: it was one
  unauthenticated command away and that command is a stop-and-ask. So
  nothing here demonstrates a completed checkout, a delivered webhook, or
  entitlement changing in response to a real provider event. The webhook
  work in section 6 is a handler tested against the *documented* scheme,
  which is a real test of the handler and no test of the provider.
- **The amounts in section 7 came from a mock that keeps no state.** The
  integer-minor-units result is a real API schema refusal. Nothing else
  about money at that rung is evidence of anything.
- **Duimstok's answers are illustrative.** They are what a specialization
  of this file looks like when someone actually does it, not values for
  another deployment to copy. The template still ships its markers
  unanswered, which is correct: they are each deployment's to answer.

The honest sentence at the end of this exercise is that
`billing-and-payments` has now been followed once, by someone trying to act
on it, and is eight findings less wrong than it was. "Verified in test
mode" is a sentence a future deployment gets to write, and "billing works"
is still nobody's.
