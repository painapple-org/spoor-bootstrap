# A worked example: first boot for a coffee roastery

Everything else in this repo describes the mechanism. This file runs it
once, end to end, against a business that doesn't exist, so a prospective
adopter can see what the first hour actually looks like before committing a
VPS to it.

**This is illustrative, not authoritative.** Nothing here is a spec, a
default, or a value to copy. Where this document and an actual file in this
repo disagree, the file wins — [`../AGENTS.md`](../AGENTS.md) owns the
interview questions and the guardrails, [`../STARTUP.md`](../STARTUP.md)
owns the first-boot flow, [`../.env.example`](../.env.example) owns the
config schema, and each `SKILL.md` owns its own content. The transcript
below is a plausible reconstruction, not a recording: a real interview
wanders more, and a real agent asks worse questions than these.

The business was picked specifically so its answers *differ* from the
reference deployment this repo was extracted from — a different owner
profile, a different tracker, a different channel, and a live product with
paying customers, which changes the autonomy conversation completely. See
[Why this example and not painapple again](#why-this-example-and-not-painapple-again)
at the end for the side-by-side.

---

## 1. The business

**Northlight Coffee Roasters** — a speciality coffee roastery in Leeds,
five people. Most of the revenue is wholesale: 41 accounts, mainly
independent cafés plus a handful of office subscriptions. Roasting happens
Tuesday and Thursday; wholesale orders for the Tuesday roast close Monday
at 18:00.

**The software.** Two years ago they paid a freelancer to build
`northlight-orders`, a wholesale ordering portal: accounts log in, set a
standing order per bean and grind, adjust or skip a week, and the roastery
pulls a roast-day sheet out the other end. It's a Django monolith with
Postgres behind it, running under docker-compose on a single VPS. The
freelancer moved on. Since then it has been unmaintained: three known bugs
nobody has fixed, a "skip a week" flow that silently doesn't email, and a
dependency set nobody has touched.

**The owner.** Priya Raman, co-owner, runs operations and wholesale. She
is not a developer. She can follow exact terminal instructions, has a
GitHub account because the freelancer made her one, and has never opened a
pull request.

**Why she's doing this.** Not to build a startup — to stop losing an
afternoon a week to a portal that half-works, without paying agency rates
for someone to re-learn the codebase every time.

That last point matters for reading the rest of this document: her failure
mode isn't a wrong architectural call, it's an agent that quietly breaks
invoicing during a Monday order cutoff. The autonomy negotiation in
section 2 is where that gets handled, and it's the part most worth reading
closely.

---

## 2. The first-boot interview

Priya has run `install.sh`, installed Claude Code, and pasted the prompt
from [`../STARTUP.md`](../STARTUP.md). What follows starts after the agent
has read [`../AGENTS.md`](../AGENTS.md).

> **Agent:** I've read AGENTS.md. Before I touch anything I need to
> interview you — the questions from that file, then autonomy, then
> anything specific to your business. First one, and I'm asking rather
> than guessing: how comfortable are you with servers, git and code
> yourself? This changes how much I explain, not what I'm allowed to do.
>
> **Priya:** Not comfortable. I can SSH in and paste commands if you tell
> me exactly what to type, and I understand roughly what a "commit" is
> because our old developer used the word. I couldn't read a diff and tell
> you whether it's right. Assume I can't.
>
> **Agent:** Good — that's a useful "no". Practically it means I explain
> what a change does in terms of what your customers will see, not in
> terms of the code, and when I need a decision from you I'll state it as a
> yes/no question rather than sending you a link and asking you to review.
>
> Second: who is the *product* for? Specifically, is the ordering portal
> used by technical people, or non-technical ones?
>
> **Priya:** Café owners and office managers. Several of them phone us
> rather than use the site. Firmly non-technical.
>
> **Agent:** Then a skill in this repo becomes mandatory rather than a
> preference — `skills/product-tech-stack/SKILL.md` fixes the stack for a
> product aimed at a non-technical end user, so I don't get to invent one.
> I've read it, and there's a conflict I want to name rather than resolve
> on my own: that skill requires FastAPI, SQLModel, Next.js and Postgres.
> `northlight-orders` is Django. Postgres and docker-compose match; the
> rest doesn't.
>
> I'm not proposing a rewrite. A rewrite of a live portal 41 accounts
> depend on is exactly the kind of thing I should not be starting in my
> first hour, and it isn't what you asked for. What I'd like to record is:
> the existing Django app stays Django and I maintain it as it is, and the
> stack requirement applies to anything genuinely new. Does that match what
> you want?
>
> **Priya:** Yes. Don't rewrite it. If you ever think it needs rewriting,
> that's a conversation with a cost attached, not something you just do.
>
> **Agent:** Recorded as an open conflict in your conventions doc, with
> that reading. Third question: where do you want work items — issues,
> tasks — tracked? This repo ships no integration for any tracker, so
> whatever you pick I wire up.
>
> **Priya:** The old developer used GitHub Issues on the repo and there are
> about a dozen still open in there, including the three bugs I mentioned.
> I don't want to learn a new tool. Can you just use those?
>
> **Agent:** Yes, and there's a real cost to it I'd rather you hear now
> than discover later. GitHub issues have two states, open and closed. The
> pipeline in this repo assumes five. So I model the four live states as
> labels, which means nothing in GitHub *stops* an issue carrying two state
> labels at once, or none. It works, and it's what the GitHub adapter notes
> in this repo are for, but it's the loosest of the three trackers it
> covers. Sticking with a tool you already read beats a stricter tool you
> won't open — I'd still make the same call.
>
> **Priya:** Stick with GitHub.
>
> **Agent:** Fourth: where do you want me reachable? A real-time channel is
> preferable to email-only, but it's your choice.
>
> **Priya:** Slack. The five of us live in it. There's a `#tech` channel
> that's basically dead since the developer left — you can have it.
>
> **Agent:** I'll use it. Fifth, and I'm asking this separately rather than
> reading it off the last answer: a single destination for urgent alerts.
> Not a group to pick from — one target, so an escalation never has to
> guess. Is `#tech` that target, or do you want urgent things to come to you
> directly?
>
> **Priya:** `#tech`. If it's on fire I want Dan to see it too, he covers
> Mondays when I'm not in.
>
> **Agent:** Then `#tech` is both the working channel and the alert target.
> One consequence: when something is genuinely for you and not for Dan,
> I'll reply in-thread to your own message or DM you rather than writing
> "Priya:" into the channel, because a name prefix in a busy channel gets
> missed.
>
> Sixth: do I have an email address of my own yet — one that belongs to me
> rather than to any of you? I'm asking outright because an address isn't a
> secret, so there's nothing for you to paste into a chat and nothing for me
> to guess at.
>
> **Priya:** No. Our mail is on `northlightcoffee.co.uk` through the same
> provider as the site. I'd have to make you one. Can you not use `info@`?
>
> **Agent:** I'd rather not, and it isn't squeamishness: `info@` is read by
> five people and replied to by whoever gets there first, so nothing sent
> from it can be attributed to me and nothing sent *to* it is reliably mine
> to act on. So this one stays unanswered rather than answered wrongly —
> the key for it stays blank and creating the address goes on the shopping
> list at the end. It's genuinely blocking, not cosmetic: until it exists,
> anything anyone grants access to *by email address* can't be granted to
> me at all.
>
> Seventh: where does the product repo live, and where does the business's
> own written context live — your public site, price lists, anything that
> describes how the roastery actually works? I need the first to work at
> all, and the second so that if you ever want me proposing work rather
> than only draining a queue, I'm proposing something about coffee and not
> generic software advice.
>
> **Priya:** Repo is `northlight-coffee/northlight-orders` on GitHub, I'm
> an admin on it. The public site is on Squarespace, separate, nothing to
> do with the repo. Our wholesale handbook is a
> Google Doc: pricing tiers, lead times, the split rules. That's the thing
> that actually explains the business.
>
> **Agent:** The site I can read. The Google Doc I can't — I have no
> Google account and no access, and per AGENTS.md I don't register for one
> myself. So that's a blocker rather than a gap: either you export it into
> the repo as markdown, or you share it with an account you provision for
> me. It goes on the shopping list at the end. Until then, anything I
> propose about pricing or lead times would be guesswork, and I'd rather
> propose nothing than guess.

### Autonomy and stop-and-ask

> **Agent:** Now the part that matters most. I've already read the default
> guardrail list in AGENTS.md and it's in force right now — I'm not asking
> permission to have it. I won't read it back to you item by item; what it
> means for *your* business is roughly:
>
> - I ship routine fixes on my own: branch, PR, merge, deploy. Those three
>   open bugs, dependency updates, copy on a page. No asking first, because
>   asking about every one of those is its own failure.
> - I stop and ask before anything I can't undo: deleting data, deleting
>   backups, rotating a password or key, touching your domain or DNS,
>   spending money, or emailing anyone outside the five of you.
> - I stop and ask before anything where I can't tell you the exact steps
>   that would undo it.
>
> What I want from you is the delta. Two directions: is there anything you
> want *tighter* than that, and is there anything routine here that the
> default makes me ask about when you'd rather I just did it?
>
> **Priya:** Tighter, yes. Two things. Anything that touches money — how a
> price is calculated, what an invoice says, the standing-order totals —
> you ask me first, every time, even if it looks like a small fix. And
> anything that sends an email to a wholesale account. If you break the
> order-confirmation email, 41 cafés get either silence or nonsense, and I
> find out from an angry phone call on a Tuesday.
>
> **Agent:** Both accepted, and I want to be precise about the second one,
> because "touches email" could mean anything. My reading: a change to
> *whether, when, or to whom* a customer email is sent, or to the content
> of one, needs your sign-off before merge. A change to something the email
> incidentally renders — fixing a bug in the order total shown in it —
> already needs sign-off under your money rule. Fixing a typo in an
> internal log line near the email code does not. Is that the boundary you
> mean?
>
> **Priya:** Yes.
>
> **Agent:** And "asks me first" — before merging the PR, or before writing
> the code? I'd suggest before merging: I write it, open the PR, and tell
> you in one line what a customer would notice, and you say yes or no. That
> way you're deciding about something real rather than about a proposal.
>
> **Priya:** Before merging. And tell me in English what changes for the
> customer, not what changed in the file.
>
> **Agent:** Recorded. Now the other direction — anything you'd rather I
> stopped asking about?
>
> **Priya:** Two. If the site is down at 6am, restart it. Don't wait for
> me. And the roast-day sheet export fails now and then and the old
> developer's fix was always "run it again" — just run it again.
>
> **Agent:** Both are carve-outs I'll take, with a condition attached that
> I'd want even if you hadn't asked: I tell you afterwards, unprompted, in
> `#tech`. Not asking first is traded against telling you after. If a
> restart fixes it three times in a week, that's not a fix any more, it's a
> symptom, and I'll investigate the cause instead of restarting a fourth
> time.
>
> To be exact about what I'm claiming: restarting an unhealthy container,
> and re-running a failed roast-day export, unattended. Not deleting
> anything, not restoring a backup, not editing order data by hand.
> Deleting or editing live order data stays a stop-and-ask for me, and if
> you're ever tempted to give me that, do it as a specific named exception
> rather than a general one.
>
> **Priya:** Agreed. Editing order data is mine.

### Anything else

> **Agent:** Last section. Things specific to your business that a generic
> template can't guess, and that I'd want a future session of myself to
> already know. I'll ask about a few I can see, then hand it back to you.
>
> Vocabulary first — I've seen "standing order", "the split" and "account"
> in your issues. Define those for me the way you'd define them to a new
> hire, so I use them the way you do.
>
> **Priya:** An "account" is a wholesale customer, never a login — logins
> are "users", one account has several. A "standing order" is the recurring
> weekly order; changing it permanently is different from "skipping a
> week", and the portal confuses those two, which is one of the bugs. "The
> split" is when we divide one roast batch across accounts, and it's a
> spreadsheet thing, not in the portal at all.
>
> **Agent:** Useful — the last one especially, because "add the split to
> the portal" is exactly the kind of thing I'd otherwise propose without
> knowing it lives outside it. Is there a time window when I should not be
> deploying?
>
> **Priya:** Monday afternoon and Tuesday morning. Orders close Monday at
> six and we roast Tuesday. If the portal is down Monday at five, that's
> the worst possible moment.
>
> **Agent:** Recorded as a deploy freeze window, and I'll treat a fix
> during it as a stop-and-ask rather than routine — including a fix for
> something broken inside the window, because "deploy a rushed change at
> the worst moment" is how a small outage becomes a big one. Anything
> else?
>
> **Priya:** One thing. I want every change to have an issue, even a
> one-line text change. Not to slow you down — it's the only way I can see
> what you've been doing, since I can't read the code.
>
> **Agent:** That's a real reason and it changes a default, so it's going
> in the conventions doc: the bar for creating a tracked item is *every*
> change, including copy edits. The issue is your window into the work.

---

## 3. The resulting `.env`

Written from [`../.env.example`](../.env.example), whose field list is the
schema — same keys, no invented ones. Secrets stay blank with a pointer to
where each comes from; Priya edits those in herself once the accounts
exist. A key that genuinely doesn't apply to this deployment stays blank
too, but with the reason written next to it — a blank with no note reads
as an oversight, and the next session can't tell the two apart.

```sh
PRODUCT_REPO_PATH=/home/spoor/northlight-orders

# Product repo had no AGENTS.md or CLAUDE.md, so the conventions doc is
# that repo's own AGENTS.md. Path is relative to PRODUCT_REPO_PATH.
CONVENTIONS_DOC_PATH=AGENTS.md

WORK_TRACKER=github-issues

# Deliberately empty, not blocked: access is the `gh` CLI that install.sh
# put on this box, which carries its own credential from `gh auth login`.
# There is no separate tracker API key for this deployment.
WORK_TRACKER_API_KEY=

# Deliberately empty, not blocked: GitHub Issues has one global API host
# that `gh` already knows. This key is for a tracker hosted per-customer —
# a Jira Cloud site, a self-hosted instance — and there is no such URL to
# record here.
WORK_TRACKER_BASE_URL=

COMMS_CHANNEL=slack

# Slack bot token (xoxb-...) from the Slack app's OAuth & Permissions page.
# Blocked: the app doesn't exist yet — shopping list item 2.
COMMS_CHANNEL_TOKEN=

# #tech in the northlight workspace. Both the working channel and the one
# escalation target.
COMMS_ALERT_TARGET=C07PQ4M3TDS

# Blocked: needs creating on the northlightcoffee.co.uk mail domain —
# shopping list item 1.
AGENT_EMAIL_ADDRESS=

OWNER_TECH_LEVEL=non-technical
END_USER_TYPE=non-technical
```

Note what *isn't* here. The autonomy deltas, the deploy freeze window, the
vocabulary, the Django/stack conflict — none of those got a made-up `.env`
key. They go in the conventions doc, which is what the next section is.

---

## 4. Excerpt from the generated conventions doc

### First, a git identity that actually pushes

Before any of this could ship, `gh auth status` came back empty — the
binary was installed, nothing was logged in. So that got dealt with on the
spot, with Priya still at the terminal: she ran `gh auth login`, picked the
browser flow, and authenticated as her own GitHub account. A
`git push --dry-run` of a throwaway branch name against
`northlight-orders` confirmed write access rather than just a successful
login.

Two credentials got checked there, not one, because pushing and opening the
PR are separate paths — the push rides the git remote, the PR goes through
GitHub's API. Here they turned out to be the same credential: the login
Priya just did set up `gh`'s credential helper for HTTPS pushes *and* left
`gh` holding an API token, so a read of the repo's own permissions through
`gh api` confirmed the API path independently of the push. That's a finding
about this box, not a rule — on a deployment where the push rode a
pre-existing SSH key, the API side would have needed a token of its own,
and nothing about the working push would have told anyone so.

Both invocations went into `git-pr-conventions`' `Auth` section, which is
their one home, along with which account they authenticate as, the fact
that they coincided here, and the fourth thing that section asks for:
whether this remote has a PR mechanism at all. GitHub does, so the answer is
a single line — but it was checked rather than assumed, because a bare git
remote on a box wouldn't, and the whole shipping loop assumes one.

That `Auth` edit is a tracked file in Priya's fork of the bootstrap repo, so
it doesn't get to sit uncommitted: it shipped as its own PR there, alongside
the conventions-doc PR in `northlight-orders`.

Her own account, not the agent's. A GitHub account belonging to the agent
is item 3 on the shopping list below and is the better end state, but it is
an upgrade to an identity that already works — waiting for it would have
meant no first PR at all. Swapping it in later is a re-run of the
specialization pass scoped to that one section.

### The doc

Written to `northlight-orders/AGENTS.md`, and shipped the same way
everything else will be: a branch, a PR, a self-merge. It's the first
change, so it establishes the convention rather than being the exception to
it.

This is an excerpt — the real file also covers the vocabulary, the repo
layout, and how to run the test suite.

> ## Autonomy: deltas from the default guardrails
>
> The default stop-and-ask list lives in `spoor-bootstrap/AGENTS.md` under
> "Default guardrails" and is in force in full. It is not copied here.
> What follows is only what Priya changed. Anything not listed below still
> stands exactly as that file has it.
>
> **Tightened — needs Priya's explicit yes before merge:**
>
> 1. **Anything that changes how money is calculated or presented.**
>    Prices, tiers, discounts, standing-order totals, invoice content. No
>    size exemption: a one-character fix to a total is in scope.
> 2. **Anything that changes a customer-facing email** — whether it sends,
>    when, to whom, or what it says. Not in scope: a change to unrelated
>    code that happens to live near the mail code.
>
> For both: open the PR first, then ask. The question is one line about
> what an account holder would notice, in plain English, not a summary of
> the diff. Priya cannot read a diff and has said so; a link plus "please
> review" is not a question.
>
> **Loosened — do it unattended, then say so in `#tech` afterwards:**
>
> 3. **Restart an unhealthy container.** Including at 06:00 with nobody
>    awake.
> 4. **Re-run a failed roast-day sheet export.**
>
> The trade for not asking first is reporting after, unprompted, every
> time. And the carve-out covers *one* retry: a failure that recurs is a
> cause to investigate, not a restart to repeat. Three restarts in a week
> means the fix is wrong.
>
> Neither carve-out extends to deleting anything, restoring a backup, or
> editing live order data. **Editing or deleting order data is Priya's,
> not this agent's** — she reserved it explicitly.
>
> **Deploy freeze: Monday 12:00 through Tuesday 12:00 Europe/London.**
> Wholesale orders close Monday 18:00 and roasting is Tuesday. No deploys
> in that window, including a fix for something broken *during* it — that
> becomes a stop-and-ask, because a rushed deploy at the worst hour of the
> week is how a small outage becomes a large one. Merge on Wednesday.
>
> ## Open conflict: the mandated stack versus this codebase
>
> `skills/product-tech-stack/SKILL.md` applies here (`END_USER_TYPE` is
> non-technical) and requires FastAPI, SQLModel and Next.js. This app is
> Django. Postgres and docker-compose already match.
>
> Agreed reading, and it is a decision rather than an oversight: the
> existing app stays Django and gets maintained as it is. The stack
> requirement governs anything genuinely new. A migration is a
> conversation with a cost attached, not something to start unasked —
> raise it, don't act on it.
>
> ## Git and PR conventions
>
> - Default branch is `master`, not `main`. The freelancer set it up that
>   way and renaming it is not worth the broken links.
> - Branch naming: `spoor/<issue-number>-<short-slug>`.
> - Commit process trailer, last line of the commit body:
>   `Spoor-Process: <stage>` (e.g. `Spoor-Process: implement`). This is a
>   process marker, not attribution — no AI attribution anywhere, per
>   `git-pr-conventions`.
> - Tracker comment marker, last line of every comment this agent writes
>   on an issue: `— spoor · <stage>`. Its purpose is letting a later run
>   tell its own prior notes from a human's, so it is never omitted.
>
> ## Bar for creating a tracked item
>
> **Every change gets an issue, including one-line copy edits.** This is
> deliberately stricter than the template's suggestion. The reason is not
> process: Priya cannot read the code, so the issue list is her only
> window into what has been happening. An untracked change is invisible to
> her, which makes it worse than a slow one.

---

## 5. Specializing a stub: `work-tracker`, before and after

"Specialize the stub" is the most abstract instruction in the whole flow,
so here is one file's worth of it concretely. These are excerpts from
[`../skills/work-tracker/SKILL.md`](../skills/work-tracker/SKILL.md); the
untouched generic parts (the seven-operation contract, the
tracker-independent rules) are omitted because specialization doesn't
change them.

### Before — as this repo ships it

````markdown
## Status: STUB — needs specialization

### The state machine this repo's pipeline assumes

| Role | What it means |
|---|---|
| unrefined-inbox | A raw idea or request, not yet scoped enough to build |
| ready | Scoped, has acceptance criteria, safe to pick up |
| in-progress | Claimed by a run that is actively working it |
| in-review | Work is done and a PR is open, awaiting the review pass |
| done / cancelled | Terminal |

`TODO(specialize)`: map each row above to the literal state name in the
chosen tracker, and record the mapping here. [...]

`TODO(specialize)`: record the literal label names chosen for these three,
and confirm they actually exist in the tracker. [...]

## How to actually call the tracker

`TODO(specialize)` — fill in, for the chosen tracker:

- **Access mechanism**: an MCP server, an official SDK, a CLI, or raw HTTP.
- **The identity the agent acts as.** [...]
- **The scope identifier**: team/project/board key, repo, or file path.
- **Any known gotchas of that specific API.** [...]
````

### After — specialized for Northlight

````markdown
## Status: PARTIAL STUB — needs specialization

The state machine, the labels and the access mechanism below are real and
usable as written. One marker is left, and only one: the identity the agent
acts as, which waits on a GitHub account for this agent instance.

### The state machine, as it exists in this tracker

GitHub has no state machine: an issue is `open` or `closed`. The four live
states are labels, created in `northlight-coffee/northlight-orders` with
`gh label create` and scoped to that repo:

| Role | This deployment |
|---|---|
| unrefined-inbox | open, and carrying *no* `state:` label |
| ready | `state:ready` + the `refined` label, both required |
| in-progress | `state:building` |
| in-review | `state:in-review` |
| done | closed, `state_reason: completed` |
| cancelled | closed, `state_reason: not_planned` |

The inbox is "no state label" rather than a label of its own, deliberately:
Priya files issues from the GitHub web UI and will never add a label, so an
inbox-by-label would make everything she files invisible.

Nothing in GitHub prevents two `state:` labels on one issue. Always remove
the outgoing label in the same `gh issue edit` call that adds the incoming
one, and treat two state labels on one issue as a loud error to report, not
something to fix by picking one.

### Labels

- refined marker: `refined`
- needs human sign-off: `needs-priya`
- targets the agent's own tooling, not the product: `agent-tooling`

All three exist in the repo. Note that `needs-priya` is *not* how the two
tightened sign-off rules in the conventions doc are enforced — those are
per-PR questions, not a label. This label is for an issue that cannot be
closed at all until she answers.

## How to actually call the tracker

- **Access mechanism**: the `gh` CLI, already installed by `install.sh`.
  No client to write. `gh api` for anything the CLI doesn't expose — the
  sub-issues endpoints, in practice. There is no separate tracker
  credential, so `WORK_TRACKER_API_KEY` in `.env` is empty by design.
- **Scope identifier**: `northlight-coffee/northlight-orders`. Pass
  `--repo` explicitly on every invocation; an unattended run's working
  directory is not reliably what you expect.
- **The identity the agent acts as.** `TODO(specialize)` — blocked on a
  GitHub account for this agent instance, which Priya has to create (see
  the shopping list). `gh` is currently authenticated as Priya's own
  account, which means "assigned to a human" versus "assigned to the
  agent" cannot be distinguished by assignee yet.

  Interim, agreed with Priya rather than invented here: ownership is
  carried by an `agent` label instead. An issue with `agent` is this
  agent's; an issue without it is hers and is inert. Delete this paragraph
  and the label when the real account lands — until then every query below
  that would filter on assignee filters on `agent`.
- **Gotchas hit so far**, on this tracker:
  - `--label` repeated is an AND and there is no `--not-label`. Negation
    needs `--search` with `-label:`, which goes through the search index
    and lags a write by seconds — never use it to verify a change just
    made; read the issue back directly.
  - `gh issue list --limit` defaults to 30 and truncates silently.
  - Sub-issues are a separate REST surface, invisible to
    `gh issue view`. A stage that doesn't ask concludes an issue has no
    children.
  - A PR is an issue. Filter `is:issue`, or the pipeline will claim its
    own PRs as work items.
````

Three things about that "after" worth noticing, because they're where the
instructions in
[`../skills/specialize-skills/SKILL.md`](../skills/specialize-skills/SKILL.md)
actually bite:

- **One marker survived, and a `Status:` heading survived with it.** The
  agent had every opportunity to write a plausible agent login and delete
  the marker. That would have produced a file that looks finished and is
  wrong. A stub that still says "unknown" beats one that confidently says
  the wrong thing. What did change is which heading: `STUB` became
  `PARTIAL STUB`, because everything except that one marker is now real.
  Those two are the only phrasings
  [`../CONTRIBUTING.md`](../CONTRIBUTING.md) allows, so *which* marker is
  outstanding goes in a sentence under the heading rather than into the
  heading text — a third phrasing is what stops the heading being skimmable
  across files.
- **The interim ownership rule was agreed, not invented.** "Never invent a
  specific" doesn't forbid recording a decision — it forbids manufacturing
  one. The distinction is whether a human said it.
- **The unused adapters got deleted.** Northlight uses GitHub, so
  `adapters/linear.md` and `adapters/jira.md` were removed in the same PR,
  and their bullets came out of `adapters/README.md`'s index, per that
  directory's own instruction. Git holds them if Priya ever migrates.
  Keeping notes for two trackers she doesn't use is exactly the "no state
  that isn't real right now" rule this repo applies to itself.

The PR that "same PR" refers to is one PR against Priya's fork of the
bootstrap repo covering the whole pass — every stub the pass rewrote and
the adapter deletions together. The one marker that survived comes back as
its own scoped PR later, once item 3 on the shopping list below exists.

---

## 6. What was still blocked at the end

The first boot ends with a shopping list, not a finished agent. Per
[`../AGENTS.md`](../AGENTS.md)'s self-provisioning section, every item on it
is Priya's to create — the agent does not register itself for anything.

1. **An email address for the agent** on the roastery's mail domain.
   Blocks `AGENT_EMAIL_ADDRESS`.
2. **A Slack app with a bot token**, installed into the workspace and
   invited to `#tech`. Blocks `COMMS_CHANNEL_TOKEN`, and with it every
   outbound message and the whole alert path. Until this exists the agent
   has no way to reach her except the terminal she started it from.
3. **A GitHub account for the agent**, with write access to the repo.
   Blocks the one remaining marker in `work-tracker`, as shown above. It
   does *not* block pushing or opening PRs: both currently authenticate as
   Priya's own account, per section 4 above.
4. **The wholesale handbook**, either exported into the repo as markdown or
   shared with the account from item 1. Without it, any proactive work
   proposal about pricing or lead times would be guesswork.

And the judgment calls the agent made rather than being told, surfaced so
Priya could correct them cheaply:

- Reading her "anything touching email" tightening as *customer-facing*
  email specifically, with the boundary written out.
- Treating a broken thing *inside* the freeze window as a stop-and-ask
  rather than an emergency exception.
- Choosing the "no state label" inbox query over an inbox label, because
  she files issues from the web UI.

None of that is a finished deployment. Wiring up the Slack listener,
writing the per-stage pipeline prompts, and getting a deploy to actually
run are all follow-on work — this repo's own README is explicit that it
gets you to a documented starting point, not to a working agent.

---

## Why this example and not painapple again

The reference deployment answers the same interview very differently, which
is the point: nothing in the interview has a default, and two honest runs of
it produce genuinely different deployments.

| Interview answer | Northlight | The reference deployment |
|---|---|---|
| Owner's technical level | non-technical | technical, hands-on with the VM |
| End user | non-technical (cafés) | non-technical |
| Work tracker | GitHub Issues, on the product repo | Linear |
| Comms channel | Slack | Telegram |
| Product | inherited Django app, live, 41 paying accounts | greenfield, no live customers |
| Autonomy posture | tightened around money and customer email | speed over ceremony; broad carve-outs |
| Deploy freeze | Monday noon → Tuesday noon | none |
| Bar for a tracked item | every change, including copy | small copy edits can ship direct |

The two rows that drive most of the difference are the same one twice:
Northlight has paying customers and an owner who cannot read a diff, so the
safety net can't be "revert it afterwards" alone. The reference deployment
has neither, so it can be.
