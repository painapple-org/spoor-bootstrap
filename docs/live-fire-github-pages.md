# A live-fire record: specializing deploy-and-monitor against a real host

Everything else in this repo, including the three worked examples in this
directory, describes or reconstructs the mechanism. This file is the one
document here that is a **recording**: a real toy product, deployed to a
real hosting platform, reached over the public internet, broken on purpose,
and rolled back — with the commands that ran and what they actually
returned.

That distinction is the entire reason it exists.
[`example-walkthrough.md`](./example-walkthrough.md) says of itself that it
is "a plausible reconstruction, not a recording", and the other two say the
same. That is honest and it is also a gap:
[`skills/deploy-and-monitor`](../skills/deploy-and-monitor/SKILL.md) had
never been followed against a live host, so nothing distinguished its
guidance being *correct* from its guidance being *plausible*. This exercise
was run to find out, and it found four things wrong or missing. They are
fixed in that file; this one records how they were found, so the fixes can
be argued with rather than taken on trust.

**Scope, stated up front.** This is a record of one deploy shape on one
platform, not a recommendation of either. Nothing here is a default. Where
this file and a `SKILL.md` disagree, the SKILL wins — the corrections this
exercise produced were written into `deploy-and-monitor` itself precisely so
that nobody has to read this file to get them.

## The setup

**The business** is fictional: Vlinder Vintage, a one-person second-hand
furniture shop, whose product is a single public page — this week's stock,
opening hours, address. Deliberately the smallest thing that can still be
deployed, broken and rolled back, because the object under test is the
deploy procedure, not the app.

**The target** is GitHub Pages, chosen for one reason that mattered more
than its merits: it is the only free hosting platform reachable with
credentials this deployment already had, so the exercise could run without a
human-gated step. See "What needed a human, and what didn't" below, which is
the part of this file most likely to be the reason someone is reading it.

**The toy app was not committed to this repo**, and shouldn't be. It is a
test subject, not a deliverable of a bootstrap template — it lived in a
throwaway repository outside this one for the duration.

## What needed a human, and what didn't

**Nothing needed a human.** That was not the expected result and it is worth
being precise about, because "free tier" and "usable by an agent" are
routinely different claims: most free hosting tiers gate signup behind a
browser flow, a CAPTCHA, or a card, and an agent that reaches one of those
has to stop and hand back. GitHub Pages does not, *for a deployment that
already has a GitHub token* — which this repo's own conventions mean is the
common case rather than a lucky one, since the git remote and the work
tracker frequently sit on the same account.

Two steps that would plausibly have been the human gate, and weren't:

- **Creating the target repository** — one `gh repo create --public` call.
- **Enabling Pages on it** — one `POST` to the repository's `pages`
  endpoint with the source branch and path. This is the step worth knowing
  about, because Pages is overwhelmingly documented as a settings-page
  toggle and reads as browser-only; it is a plain API call, and it returns
  the eventual public URL in its response before the first build has even
  started.

Neither required a scope beyond `repo`. No email confirmation, no payment
method, no interactive prompt.

**What this does not generalize to.** The token was already provisioned by a
human, once, before any of this — which is the shape
[`AGENTS.md`](../AGENTS.md)'s self-provisioning rule already describes, and
not a counterexample to it. And the free tier is a real constraint with real
edges: Pages serves static files only, over HTTP, from a public repository.

**The honest limitation, named rather than buried:** that last point means
the product deployed here could not be the stack this repo requires.
[`skills/product-tech-stack`](../skills/product-tech-stack/SKILL.md)
mandates FastAPI, PostgreSQL, Docker and the rest for a non-technical
end-user's product, and **none of that can run on a static host.** So what
was live-fired is the deploy, rollback and monitoring loop — which is what
`deploy-and-monitor` owns and what was untested — against a product simple
enough to fit the only ungated target available. A deploy of the mandated
stack still has not been exercised end to end, and that gap is unchanged by
this exercise. Anyone reading this as "the required stack is now proven
deployable" has read it wrong.

## What the run actually did

In order: pushed the page and enabled Pages; confirmed the public URL
served it; shipped a content change (a price edit) and watched it
propagate; reverted that change and watched the revert propagate; committed
a deliberately invalid build config to force a failed deploy; observed what
each available signal said while the deploy was broken; removed the bad
config and confirmed recovery.

Every measured duration below is a historical observation from that single
session, not a figure this repo owns or a threshold to build against. One
sample, one platform, one afternoon.

- **Push to live, for a normal change:** the public URL served the new
  content 31 seconds after the push. The platform's own build-status field
  reached `built` in the same poll that the content appeared, so on this
  sample it lagged the deploy by nothing measurable.
- **Rollback to live:** a `git revert` plus a push had the previous version
  observably live again 40 seconds later. This is the number the
  corresponding `deploy-and-monitor` bullet now asks specialization to
  measure, and the reason it asks: it is the difference between a rollback
  being a real option mid-incident and being a hope.
- **A failed deploy:** the Actions run for it completed with `failure` in
  40 seconds, correctly and promptly.

## The four findings

Each of these was a wrong or missing instruction in
`deploy-and-monitor/SKILL.md`, found by following it rather than by reading
it. Each is now fixed there — this section records the evidence, not the
rule.

### 1. A failed deploy left every obvious signal green

The most consequential finding, and the one that justifies the whole
exercise. With the deploy definitively broken:

- The platform's **build-status field sat at `building`** — a non-terminal
  value — for over ten minutes, with its own error field empty. It never
  flipped to `errored`. It returned to `built` only after a *subsequent
  successful* build, meaning the misleading state persisted exactly as long
  as the failure did. A monitor whose condition is "status is the failure
  value" would never have fired, and a dashboard rendering that field would
  have shown a deploy still in progress indefinitely.
- The **public URL answered HTTP 200** throughout, serving the last good
  release with a completely valid body. Failing safe rather than serving an
  error is good platform behavior and terrible monitoring input: the black-box
  check the SKILL recommends was green the entire time nothing was shipping.
- The **CI run list** reported the failure correctly within 40 seconds, and
  the **deployment records** were right by omission — the failed build
  created no new deployment entry.

So of four available signals, two were green during a total deploy failure
and two were accurate. The SKILL named all four categories but ranked none
of them, which meant following it faithfully could produce a monitoring
setup built entirely on the two that lie. It now says to prefer a signal
guaranteed to reach a terminal state, to alert on elapsed time in a
non-terminal state rather than only on an explicit failure value, and to
treat the absence of a new success as the most reliable form of the signal.

### 2. "Assert on something in the body" is not enough to detect a deploy

Directly downstream of the above. The SKILL's black-box guidance said to
assert on status and on something in the body rather than only on the
connection succeeding — which is right against the failure it was written
for, an app that is down, and useless against this one. A platform serving
the previous release passes any assertion about valid content, because the
content *is* valid; it is merely old.

The fix is a marker that changes per release, asserted against the value
expected for the revision under test. The toy app carried a literal build
identifier in its footer for exactly this reason, and it is the only reason
the stale-content failure was visible at all rather than being recorded as
a successful deploy.

### 3. "Is the latest build green?" answered about the previous build

Measured directly: a status check issued in the seconds after a push
returned `built` — the previous build's result, because the new build did
not exist yet. This is a false green delivered precisely when someone is
watching for it, and the SKILL had nothing about it.

It now says to correlate on the revision actually shipped rather than
trusting whatever "latest" returns, and where only a poll is available, to
require the record's own identity to have changed before reading its status.

### 4. A rollback that never ran looked exactly like a rollback in progress

This one was an accident, which is what makes it worth keeping. The first
rollback attempt used an invalid flag; the command errored and did nothing.
The verification loop that followed — polling the public URL until the old
version reappeared — then ran for five minutes producing output
indistinguishable from a slow but working rollback, because "the bad version
is still live" is what both situations look like from outside.

Five minutes of a fabricated recovery, during a real incident, on the one
procedure this repo's whole autonomy model treats as the safety net. The
SKILL said the rollback must be a known, tested procedure; it said nothing
about verifying the rollback was *initiated* before starting to wait on it.
It does now, alongside the requirement to actually perform one real rollback
during specialization rather than only writing one down — which is what
would have caught the invalid command on a quiet afternoon instead.

## What a specialized answer looked like

For the record, and not as a template to copy: on this target, the answers
`deploy-and-monitor`'s markers ask for came out unusually short, and the
shortness is itself informative about the static-host shape.

- **Pipeline**: one already existed and was not built here — enabling Pages
  provisions a provider-managed workflow. This is the inherited-pipeline
  case from that file's first section, arriving on a brand-new repository,
  which is not how one expects to meet it.
- **Environments**: one. Production, no staging, nothing to promote.
- **Trigger**: a push to the default branch. Merging is deploying, so the
  merge is not the cheap reversible act the shipping loop otherwise treats
  it as.
- **Rollback**: revert the commit and push. Verified live, once, for real.
- **Backups**: the stateless case — the product holds no data of its own,
  so the source repository is the only copy of it and its host is the
  single point of failure. This is the answer the backup section now
  distinguishes from an unprotected product, because the exercise made
  clear how identically the two read as "no backups".
- **Monitoring**: entirely black-box, not by choice. There is no shell, no
  container and no host, so every white-box signal that file lists is
  structurally unavailable rather than merely unconfigured — which is what
  prompted the correction to its opening Docker assumption.

## Reproducing it

The throwaway repository this ran in was disposable by design and is not
linked from here, so that this repo's link checking never depends on an
artifact meant to be deleted. Reproducing the exercise needs no artifact
from it: a GitHub token with `repo`, a single static file carrying a
per-release marker, `gh repo create`, one `POST` to the repository's `pages`
endpoint, and then the four findings above are reachable in about twenty
minutes — including the failed-build one, which needs nothing more than
committing an invalid build config on purpose.

Doing that is the recommendation this file ends on, and it is aimed at
`deploy-and-monitor`'s specialization pass rather than at a reader: the
findings above were not visible from reading a careful document, and would
not have been found by writing a more careful one.
