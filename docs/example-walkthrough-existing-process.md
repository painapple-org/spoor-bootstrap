# A worked example: first boot into a team's existing engineering process

Everything else in this repo describes the mechanism. This file runs it
once, end to end, against a business that doesn't exist, so a prospective
adopter can see what the first hour actually looks like before committing a
VPS to it.

It is the **third** worked example here, and the three cover deliberately
different shapes. This one is the shape where *the agent is the newcomer*:
a four-engineer team that has been shipping the same product for years, with
a protected default branch it cannot merge to, CI it has to satisfy,
conventions already written down in a `CONTRIBUTING.md` it must defer to
rather than replace, and a hundred-plus-issue Jira backlog that predates the
deployment and must not be dragged into the pipeline on the first run. The
other two:

- [`example-walkthrough.md`](./example-walkthrough.md) — a five-person
  coffee roastery with an *inherited, unmaintained* codebase and a
  non-technical owner. Superficially similar to this file (an existing repo,
  existing issues) and different in the way that matters: nobody there has
  a process to join. The freelancer left, `main` is unprotected, there is no
  CI, and the conventions are the agent's to propose.
- [`example-walkthrough-solo.md`](./example-walkthrough-solo.md) — one
  technical person starting from nothing: no product repo, no work tracker,
  no chat platform and no git hosting account at all, so the pull request
  itself has to be replaced by an agreed substitute.

All three are honest runs of the same interview; almost every answer
differs. The three-way side-by-side is at
[Why this example and not the other two](#why-this-example-and-not-the-other-two).

**This is illustrative, not authoritative.** Nothing here is a spec, a
default, or a value to copy. Where this document and an actual file in this
repo disagree, the file wins — [`../AGENTS.md`](../AGENTS.md) owns the
interview questions and the guardrails, [`../STARTUP.md`](../STARTUP.md)
owns the first-boot flow, [`../.env.example`](../.env.example) owns the
config schema, and each `SKILL.md` owns its own content. The transcript
below is a plausible reconstruction, not a recording: a real interview
wanders more, and a real agent asks worse questions than these.

---

## 1. The business

**Salvia Systems** — eleven people in Ghent, four of them engineers,
selling one product to hospital pharmacies: software for *compounding*, the
part of a hospital pharmacy that mixes preparations to order rather than
dispensing them off a shelf. A pharmacy technician follows a recipe on
screen, scans each ingredient lot, gets a second technician to verify the
weighings, and the software produces the batch record and the labels that go
on the finished preparation. Twenty-three hospitals run it, each on its own
instance.

**The software.** `compound`, a pnpm monorepo on GitHub: a NestJS API and a
React front end over Postgres with Prisma, plus a second repo,
`compound-labels`, a small Kotlin service that drives the label printers
because the printer vendor only ships a JVM SDK. Both have been in
continuous development for four years. There is CI — lint, typecheck, unit
tests, an end-to-end suite and a licence scan — and there is a protected
`main` that nobody, including the founders, can merge to without someone
else's approving review. That protection is not fussiness: hospital
customers audit their suppliers, and "no change reaches a customer without a
second pair of eyes" is a claim the company has made in writing.

**The team.** Naomi Vervoort, tech lead, does the interview. Timo Aerts,
senior engineer. Fien Deprez, six months out of university. Joris Maes, a
platform contractor two days a week who owns the deploys. And Hannelore
Steurs, quality and regulatory officer — not an engineer, sits in the same
chat channel as the four of them, and owns sign-off on anything a hospital
inspector could end up reading.

**Why they're doing this.** Not to replace anybody. The backlog has grown
faster than four engineers can drain it for two years, and the bottom half
of it is small, well-understood, nobody-wants-it work: a validation message
that reads badly in French, a report that times out over 90 days, sixteen
dependency majors behind. They want that half drained by something that
follows their process rather than around it.

That last clause is what makes this deployment different from the other two
examples. There is a process here, it predates the agent, and it is written
down. The failure mode isn't a wrong architectural call or a broken
production service — it's an agent that arrives and starts inventing
conventions a team settled two years ago, or that mistakes their backlog for
its own inbox and posts a hundred and eighty refinement comments onto an
audited board overnight. Sections 2 and 5 are where those get handled, and
they are the parts most worth reading closely.

---

## 2. The first-boot interview

Naomi has cloned this repo into a private copy on the company's GitHub org,
run `install.sh`, installed her harness, and pasted the prompt from
[`../STARTUP.md`](../STARTUP.md). What follows starts after the agent has
read [`../AGENTS.md`](../AGENTS.md).

> **Agent:** I've read AGENTS.md. Before I touch anything I need to
> interview you — the questions from that file, then autonomy, then anything
> specific to your business. First one, and I'm asking rather than guessing:
> how comfortable are you with servers, git and code yourself? This changes
> how much I explain, not what I'm allowed to do.
>
> **Naomi:** Technical. I've been writing software for twelve years and I'm
> the one who set up our CI. Don't explain git to me.
>
> **Agent:** Good. I'll write to you in code and commands. I'll come back to
> this question once I know whether there are other people, because there's
> normally more than one and they're not all at the same level.
>
> Second: who is the *product* for? Specifically, is it aimed at technical
> people or non-technical ones?
>
> **Naomi:** Pharmacy technicians and hospital pharmacists. As non-technical
> as it gets, and under time pressure while they use it — they're standing
> at a laminar flow cabinet with gloves on.
>
> **Agent:** Then a skill in this repo becomes mandatory rather than a
> preference — `skills/product-tech-stack/SKILL.md` fixes the stack for a
> product aimed at a non-technical end user, and I don't get to invent one.
> I've read it, and there's a conflict: it requires FastAPI, SQLModel,
> Next.js and Postgres. `compound` is NestJS and React over Postgres with
> Prisma, and `compound-labels` is Kotlin. Postgres matches. Nothing else
> does.
>
> That skill already says how a conflict like this resolves, so I'm not
> deciding it here — its "When the product repo already exists and doesn't
> match" section says the existing app keeps its stack and gets maintained
> as it is, and the requirement governs genuinely new work. The first half
> is easy: four years of TypeScript stays TypeScript, and a rewrite would be
> a conversation with a cost attached rather than something I start in my
> first hour. The second half isn't, and I'd rather find out now than in
> three weeks — is there any genuinely new, separable thing coming?
>
> **Naomi:** Yes, and it's in the backlog. A stock-forecasting service —
> predicting which preparations a ward will need next week from historical
> batch data. It's separable, it's new, and it's the one thing in the
> backlog I'd actually enjoy building.
>
> **Agent:** Then that's a real conflict rather than a dormant one, and I
> don't think I should resolve it myself. Reading that requirement literally
> means the forecasting service arrives in Python and FastAPI, and you'd
> have four engineers maintaining a second language and a second toolchain
> for one service.
>
> **Naomi:** No. Absolutely not. We have one Kotlin service because a
> printer vendor forced it on us and I regret it every time Fien has to
> touch it.
>
> **Agent:** I hear that, and I'd recommend the same thing you're saying —
> but I'm not going to write down that the requirement is waived, because
> it's a requirement of this template rather than a preference of mine, and
> a first-hour interview isn't where I overrule it on my own say-so. What
> I'll record is the conflict, both readings, my own recommendation and the
> fact that it's undecided, and it goes on the shopping list as an open
> decision. It blocks nothing today: the forecasting ticket isn't work
> either of us is starting this week.
>
> **Naomi:** Fine. Flag it, we'll settle it properly.
>
> **Agent:** Third: where do you want work items tracked? This repo ships no
> integration for any tracker, so whatever you pick I wire up.
>
> **Naomi:** Jira. Not because we love it — the hospitals' own change
> processes want an auditable trail and Jira is what we already have. Cloud,
> project key `CMP`, company-managed, and the workflow has been the same for
> three years.
>
> **Agent:** Then two things follow, and one of them is the biggest single
> risk in this whole setup, so I want to spend real time on it.
>
> The easy half: an existing tracker with existing conventions is a complete
> answer to this question, and I'm not going to re-litigate it or propose
> something stricter. AGENTS.md's repo question says so outright.
>
> The hard half is your backlog. The pipeline in this repo has a five-state
> machine, and the first of those states is an *unrefined inbox* — the queue
> a refine stage drains. The obvious mapping onto your workflow is that my
> inbox is your `Backlog` status. How many open issues are sitting in
> `Backlog` right now?
>
> **Naomi:** A lot. Let me look. One hundred and eighty-three, and honestly
> some of those are from before Fien was born, professionally speaking.
>
> **Agent:** Then the obvious mapping is a disaster and I'd rather say so
> loudly than discover it tonight. The GitHub adapter notes in this repo call
> this out as a trap and it applies identically to Jira: if my inbox is your
> `Backlog`, then on my first scheduled run all 183 of those read as fresh
> intake. A refine stage would work through them, rewrite descriptions, add
> acceptance criteria and comment on each one — including the four-month-old
> design discussion you're still arguing about and whatever Timo is halfway
> through. On a board your customers can audit.
>
> **Naomi:** That would be a very bad Monday.
>
> **Agent:** There are three ways to avoid it. Two are in the adapter notes
> and I don't like either for you.
>
> One: backfill a state onto all 183 once, deliberately, so "in the inbox"
> means what it says from then on. On GitHub that's adding a label. Here it
> would mean transitioning 183 issues through your own workflow, which moves
> them on your board, fires 183 notification mails at everyone watching, and
> writes 183 status changes into a history hospitals read. No.
>
> Two: scope my inbox query to issues created after today. Cheap, needs
> nothing from you — and it permanently hides the pre-existing backlog from
> the pipeline. Which is precisely backwards here, because the bottom half of
> that backlog is the entire reason you're doing this.
>
> Three, and this is what I'd propose: my inbox isn't a status at all. It's
> an opt-in label — a `spoor-inbox` label, in a `spoor-` namespace so it's
> obviously not yours — that one of you puts on a ticket to hand it over.
> My inbox query becomes "in `Backlog` **and** carrying that label", which
> today matches zero issues. Your board doesn't change, your 183 tickets are
> untouched and stay yours, and the old ones become available to me one at a
> time as somebody decides they're worth handing over. The cost is a manual
> step per ticket, and I think that's the right cost to pay in the first
> month.
>
> **Naomi:** Do that. And it's not really a cost — I want to choose what you
> get anyway, at least at first.
>
> **Agent:** Then I'll record it as the state mapping rather than as a
> workaround, because it changes what "inbox" *means* on this deployment and
> a future session of mine has to read that rather than re-derive it. Two
> honest caveats. Your count came from your browser, not from a call I made
> — I have no tracker credential yet, so I'll verify it myself once I do,
> and until then the number in my notes is yours rather than mine. And the
> reason this matters at all is that your existing statuses are *yours*: I'm
> mapping my pipeline onto your workflow, not adding columns to it.
>
> **Naomi:** Nothing gets added to that workflow. It took four months to
> agree.
>
> **Agent:** Recorded, and that's a stronger constraint than it sounds —
> this repo's Jira notes point out that a default workflow often has no
> distinct review column and that the owner may need to add one. Yours has
> `In Review` already, so I don't need to ask. If it hadn't, I'd have had to
> come back to you rather than quietly folding two states together.
>
> Fourth: where do you want me reachable? A real-time channel is preferable
> to email-only, but it's your choice.
>
> **Naomi:** Teams. The whole company is on Microsoft 365 and there's an
> Engineering team with a `#dev` channel.
>
> **Agent:** I'll use it. Fifth, and this is the one I most need you to be
> exact about: who is allowed to tell me to *do* something? Anyone not on
> that list, I read and report but don't act on. I need the list of
> identities, not a category — and in the form Teams itself verifies, which
> means Entra object IDs rather than display names. A display name is
> something a tenant admin can change.
>
> **Naomi:** Me, Timo and Fien. The three of us who write the code.
>
> **Agent:** Three, then. Who else is in `#dev`?
>
> **Naomi:** Joris — he's our platform contractor, two days a week, he owns
> the deploys. And Hannelore, quality and regulatory.
>
> **Agent:** Then I want to be explicit rather than let it pass, because
> "everyone in the channel" and "everyone who may instruct me" are two
> different lists and yours differ by two people. Are Joris and Hannelore
> deliberately off the list, or just not mentioned?
>
> **Naomi:** Deliberately, both, for completely different reasons. Joris is
> an agency contractor. Nothing personal, but he isn't ours and I don't want
> him able to make our product do things. Hannelore is the opposite problem —
> she's the most senior person in that channel about anything a hospital
> reads, and she is absolutely not a software engineer. If she asks you to
> "just change the label", the right answer is not to do it.
>
> **Agent:** Both recorded as deliberate exclusions rather than omissions.
> Hannelore raises a question I'd get wrong by guessing, though, and it's
> worth one more minute. Is there a class of change where *her* yes is the
> one I need?
>
> **Naomi:** Yes. Anything an inspector could read: the batch record, the
> printed labels, the audit log. If you change what those say, she signs it
> off, not me.
>
> **Agent:** Then those are two separate roles for the same person and I
> want to name the distinction, because this is exactly the place a security
> boundary gets blurred by accident. Hannelore may **release a gate**: where
> my conventions doc says a change needs her sign-off, her own "yes" in the
> channel is what satisfies it, and I don't need it relayed through you. She
> may **not initiate work**: a message from her asking for a change is a
> request I bring to one of you three, not an instruction I act on. Those are
> different verbs and only the second one is what the allowlist governs.
>
> **Naomi:** That's exactly right, and I wouldn't have thought to separate
> them.
>
> **Agent:** And back to my first question, now that there are three of you
> on the list: I asked how technical *you* are when I still thought there was
> one person to write to.
>
> **Naomi:** Timo's as technical as me, more in some areas. Fien is good but
> she's six months in and she doesn't know what she doesn't know yet.
>
> **Agent:** Then the three of them get written to the same way — all three
> read code, so `.env`'s one switch is `technical` and there's no rounding
> to do. What isn't obvious from that switch, and what I'd want a future
> session to know, is the Fien half: she can instruct me, and I'll treat a
> request of hers exactly like one of yours *except* where it changes the
> batch or audit schema, where I'll confirm with you before starting. That's
> not a comment about her competence, it's that a migration on those tables
> is one of the few things here I can't cleanly undo.
>
> **Naomi:** Agreed. She'd agree too.
>
> **Agent:** Sixth, and I'm asking it separately rather than reading it off
> your channel answer: one destination for urgent alerts. One target, so an
> escalation never has to guess. `#dev`?
>
> **Naomi:** I suppose `#dev`. It's where everything else is.
>
> **Agent:** I'd push back, and this is the one place I'll argue with an
> answer. `#dev` has Joris and Hannelore in it, and an alert from me is
> often a stack trace or a failing query — the kind of thing that can quote
> whatever data made it fail. On a product handling patient preparations, I'd
> rather not be the process that pastes that into a channel with a contractor
> in it. `#dev` is also busy, which is the other half: an escalation in a
> busy channel gets scrolled past. Could we have a channel with just the
> three of you?
>
> **Naomi:** Yes. I'll make `#spoor-alerts` with the three of us.
>
> **Agent:** Then that's the one target, and I'll note why it isn't `#dev`
> next to it, because the reason is the thing that keeps someone from
> "simplifying" it back later.
>
> Seventh: do I have an email address of my own yet — one that belongs to me
> rather than to any of you? I'm asking outright because an address isn't a
> secret.
>
> **Naomi:** No, and I can't make you one. Our tenant is administered by an
> external IT partner. I can't create a mailbox, I can't register an app, I
> can't grant admin consent. I raise a ticket and they do it.
>
> **Agent:** Then it's blocked rather than merely missing, and it's the item
> everything else on my shopping list hangs off, which I'd rather show you
> than assert. Three things need that one account:
>
> - the address itself, for `AGENT_EMAIL_ADDRESS`;
> - my Jira credential, because Jira Cloud's API auth is Basic with an email
>   address as the username — this repo's Jira notes are explicit that the
>   username reads from `AGENT_EMAIL_ADDRESS` rather than getting a slot of
>   its own, so no mailbox means no tracker access, even with a token in
>   hand;
> - the Teams bot, which needs an app registration and admin consent in your
>   tenant.
>
> So until that ticket is done I can read your repos and write files, and I
> cannot touch your board or send you a message. That's worth knowing before
> you plan around me. And to be clear about a boundary: I don't register
> accounts for myself — that's yours to ask your IT partner for, per
> AGENTS.md.
>
> **Naomi:** I'll raise it this afternoon.
>
> **Agent:** Eighth, and it's really three questions. Where does the product
> repo live, what do the people in it already do, and where does the
> business's own written context live?
>
> **Naomi:** `salvia-systems/compound` on GitHub, and `compound-labels`
> alongside it. As for what we do — it's in `CONTRIBUTING.md`, and it's
> current, because commitlint fails the build if you get the commit format
> wrong so nobody can drift from it.
>
> **Agent:** I read it before asking, which AGENTS.md tells me to do rather
> than spending your time on something I could have looked up. What I found,
> so you can correct me: branches are `<initials>/<CMP key>-<slug>`; commits
> are Conventional Commits with the Jira key in the footer, enforced by
> commitlint; there's a PR template with a four-item checklist; and there's a
> definition of done that includes a test and a changeset. The last fifty
> branch names on the remote match it, so it's live rather than aspirational.
>
> Two things I want to say about that. First: those are yours, they predate
> me, and I'm joining your workflow rather than establishing one. I will not
> be writing branch naming or a commit format into my own conventions doc —
> `CONTRIBUTING.md` owns them, my doc will point at it, and if I copied them
> across then the day you edit yours my copy becomes a confidently wrong
> instruction I follow on every run.
>
> Second: your convention has a hole I fall through, and it's the only edit I
> need. `<initials>/` assumes an actor with initials. What do I put there?
>
> **Naomi:** Huh. `spoor/`, obviously. I'd never have thought about it until
> the first branch showed up called `undefined/CMP-1201-whatever`.
>
> **Agent:** Then `spoor/<CMP key>-<slug>`, and it goes in my doc as an
> *addition* to yours rather than a replacement of it — along with two other
> things your conventions have no reason to cover, because no human needed
> them: a trailer on my commits naming which process produced them, and a
> footer on every Jira comment I write so a later run of mine can tell its
> own prior notes from a human's. Is there anything in `CONTRIBUTING.md`
> you've been meaning to change anyway, so I don't cement something you're
> already unhappy with?
>
> **Naomi:** The changeset requirement is dead. We stopped publishing the
> packages separately a year ago and nobody removed it.
>
> **Agent:** Then I'm not going to honor a dead requirement or quietly ignore
> it either — removing it is a change to your repo, so it's a ticket, and
> it's a good first one. What I won't do is write "the changeset rule doesn't
> apply" into my own doc, because that's a second home for a fact and the
> file itself is the place to fix it.
>
> And the third part: where does the business's own written context live —
> what the product does, what a customer expects, the vocabulary?
>
> **Naomi:** Confluence, same Atlassian site. And the validation master
> file, which is the regulatory documentation, but that's on a SharePoint
> Hannelore controls and I'm not going to be the one who gives an AI access
> to it.
>
> **Agent:** Confluence I can read once the account exists — same
> credential, which is one more thing hanging off that IT ticket. The
> SharePoint I'll record as a *deliberate* exclusion rather than a gap,
> because those look identical to a future session six months from now and
> they're not the same thing at all. What it costs, so it's written down
> rather than discovered: I will never be able to tell you whether a change
> affects the validated state of your system, because the document defining
> that state is one I can't read. So I don't get to say "this doesn't affect
> validation" — that's Hannelore's sentence, not mine.

### Autonomy and stop-and-ask

> **Agent:** Now the part that matters most. I've already read the default
> guardrail list in AGENTS.md and it's in force right now — I'm not asking
> permission to have it. I won't read it back to you item by item; what it
> means for *your* business is roughly:
>
> - I ship routine work on my own: branch, PR, deploy where that's mine.
>   Bugs, dependency bumps, copy fixes. No asking first, because asking
>   about every one of those is its own failure.
> - I stop and ask before anything I can't undo: destroying data or backups,
>   rotating a credential, DNS, spending money, contacting anyone outside
>   your circle, force-pushing or rewriting pushed history, registering an
>   account anywhere, widening my own permissions.
> - I stop and ask before anything where I can't name the exact steps that
>   would undo it.
>
> One of those needs saying out loud in your case rather than left in a
> list, because your repo makes it tempting: **changing your branch
> protection, or adding myself to a bypass list, is on that stop-and-ask
> list twice** — as a protection change and as widening my own permissions.
> If your rules block me from merging, that is your review policy working
> as designed and I'm one more author subject to it. It is never something I
> route around.
>
> What I want from you is the delta. Two directions: anything you want
> *tighter*, and anything routine the default makes me ask about when you'd
> rather I just did it.
>
> **Naomi:** Tighter, three things.
>
> Anything an inspector reads — batch record content, label content, what
> goes into the audit log — needs Hannelore's yes before it goes anywhere
> near review. You already have that one.
>
> **Agent:** I do, and let me sharpen the boundary so it's usable rather
> than a vibe, because "touches the label" could mean anything. My reading:
> a change to *what a batch record or a label says*, to what gets written to
> the audit log, or to whether something gets written there at all, needs her
> explicit yes — before I ask a human for their review, not after, so nobody
> spends review time on something she'll reject. A change to code that
> happens to live in the same module, or a refactor that provably doesn't
> alter the rendered output, doesn't. If I can't tell which side of that line
> a change falls on, I treat it as needing her. Right boundary?
>
> **Naomi:** Right, and I like "if you can't tell, it needs her".
>
> Second: migrations. Additive is fine — new table, new nullable column. But
> nothing that drops or rewrites a column on the batch, weighing or audit
> tables. Those records have a retention obligation measured in years and
> they are the evidence a hospital shows an inspector.
>
> **Agent:** Accepted, and I want to name why it's a real extension rather
> than something the default already covers, because it nearly is. The
> default guardrail is about destroying data. This is stricter in two ways:
> it covers *rewriting* as well as dropping, and it applies even where I can
> write you a clean down-migration. A reversible migration on those tables
> still breaks the thing that makes them evidence, which is that nobody
> edited them. So "I can describe the rollback" is not a licence here.
>
> **Naomi:** Third: production. There are twenty-three hospital instances
> and you will never have credentials to any of them. Joris deploys, on a
> Tuesday release train, and the hospitals have their own change windows.
>
> **Agent:** Then I'll record that as a fact about this deployment rather
> than as a rule I'm agreeing to observe, because those behave differently: a
> rule I could be persuaded out of, a fact I have to plan around. It means my
> pipeline stops at a merged PR, deploy-and-monitor has very little to say
> here, and I don't get to verify a fix in production — I verify it in
> staging and hand it to Joris' train. It also means I should never ask you
> for those credentials, including when it would be convenient, and I'd
> rather write that down than rely on my own restraint at 2am.
>
> **Naomi:** Good. Looser, two. Dependency updates: just open the PRs. We're
> sixteen majors behind on something and I don't want to be consulted about
> each one.
>
> **Agent:** Taken, and it's cheaper for you than it sounds because of your
> own protection: every one of those still needs a human approving review
> before it merges, so "don't ask first" here means "don't ask before opening
> the PR", and your existing gate is still in front of the merge. I'd
> propose one addition of my own: batched by risk rather than one PR per
> package, and majors separated from patches, because a review of nineteen
> mixed bumps is a rubber stamp and a rubber stamp is worse than no review.
>
> **Naomi:** Yes. And second: our end-to-end suite is flaky. If a job fails
> on a known flake, re-run it. Don't ask.
>
> **Agent:** Taken, with the condition I'd want even if you hadn't asked: I
> tell you afterwards, unprompted, in `#spoor-alerts`. Not asking first is
> traded against reporting after. And the carve-out covers *one* re-run: if
> the same spec fails three times in a week, that's not a flake, it's a
> failing test, and I'll open a ticket for the cause rather than re-running a
> fourth time. To be exact about what I'm claiming: re-running a failed CI
> job, and restarting the shared staging stack. Not touching a hospital
> instance, not re-running a deploy, and not merging anything on a green
> re-run that a human hasn't approved.
>
> **Naomi:** Agreed.

### Anything else

> **Agent:** Last section. Things specific to your business that a generic
> template can't guess, and that I'd want a future session of myself to
> already know. I'll ask about a few I can see, then hand it back to you.
>
> Vocabulary first — I've seen "batch", "prep", "recipe" and "verification"
> in your repo and your tickets, and I'd rather use them the way you do than
> the way I'd guess.
>
> **Naomi:** A "recipe" is the template — how to make something. A "prep" is
> one thing actually made for one patient or one ward. A "batch" is a set of
> preps made together from the same ingredient lots, and the batch record is
> the document that proves it. "Verification" is specifically the
> second-technician double-check on a weighing; it is not code review and it
> is not QA, and it turns up in three of our tables.
>
> **Agent:** Useful, and the last one especially — I'd have written
> "verification failed" in a status message meaning a test, which in your
> product means a technician disagreed about a weight. Next: is there a
> window when I shouldn't be shipping?
>
> **Naomi:** Not a clock. Once a month we do a validation run — Hannelore
> and Joris walk the whole system against a script and sign the result.
> While that's happening, `main` doesn't move. Not for anything.
>
> **Agent:** Then it's a state gate rather than a calendar, which is a
> genuinely different shape and worth recording as such. How would I know
> it's happening?
>
> **Naomi:** There's a `CMP` ticket for each run and it sits in `In
> Progress` while it's live.
>
> **Agent:** Then that's the mechanism and I'll use your existing signal
> rather than inventing one: before any merge, read the state of the open
> validation ticket, and if it's live, don't merge — including a merge a
> human has already approved, and including a fix for something broken
> *during* the run. That last part is deliberate: a rushed change in the
> middle of a signed validation is how a small problem becomes a regulatory
> one. It becomes a stop-and-ask instead.
>
> **Naomi:** Correct, and thank you for getting that without me spelling it
> out.
>
> **Agent:** Last thing, and I'm asking because you're technical and it will
> annoy you if I get it wrong: what's the bar for creating a tracked item?
>
> **Naomi:** Everything I hand you already has a ticket — that's the whole
> point of the label. What I don't want is you creating *new* tickets on that
> board. It's audited, our product owner grooms it, and a bot filing things
> into it is noise in a place that can't afford noise.
>
> **Agent:** Then I'll read that as a decision about a pipeline stage rather
> than a preference, and read it back precisely: no proactive ideation stage,
> nothing of mine files work proposals onto your board. Decided against, not
> left open — those look identical in the code and completely different in a
> year. What I would still want, and it's a different animal, is a proactive
> upkeep pass: dependencies and CVEs, which produce PRs against a ticket you
> already handed me rather than new tickets of their own.
>
> **Naomi:** That's fine. That's not a feature request, that's maintenance.
>
> **Agent:** And one exception I'd ask for on the no-new-tickets rule: if I
> find something genuinely broken while working on something else — a real
> bug, not a nit — I'd rather tell you in `#spoor-alerts` than either file it
> or drop it. Then filing it is your call.
>
> **Naomi:** Perfect.

---

## 3. The resulting `.env`

**Shown in its final state, at the end of the whole flow.** Step 4 of
[`../STARTUP.md`](../STARTUP.md) is where this file gets written, but that
step explicitly leaves `CONVENTIONS_DOC_PATH` blank — step 6 fills it in,
once the agent has actually decided where that doc lives. It's populated
below because this is the after picture, not because step 4 knew it.

Written from [`../.env.example`](../.env.example), whose field list is the
schema — same keys, no invented ones. Secrets stay blank with a pointer to
where each comes from; Naomi pastes those in once the IT partner has
provisioned the account. A key that genuinely doesn't apply to this
deployment stays blank too, but with the reason written next to it — a blank
with no note reads as an oversight, and the next session can't tell the two
apart.

```sh
# The primary product repo. `compound-labels` is the second one; the
# conventions doc lists both, since this variable is singular.
PRODUCT_REPO_PATH=/home/spoor/compound

# The product repo already has a CLAUDE.md (four years of accumulated
# instructions for the team's own harness use), so this deployment's
# conventions doc is a clearly-named sibling rather than a clobbering of it.
# Path is relative to PRODUCT_REPO_PATH.
CONVENTIONS_DOC_PATH=SPOOR.md

WORK_TRACKER=jira

# Jira Cloud API token, minted from the agent's own Atlassian account at
# id.atlassian.com. Blocked: that account doesn't exist yet — shopping list
# item 1, which item 2 hangs off.
WORK_TRACKER_API_KEY=

# Jira Cloud is per-customer hosted, so this key has a real value here
# rather than being blank the way a single-global-host tracker leaves it.
WORK_TRACKER_BASE_URL=https://salvia-systems.atlassian.net

COMMS_CHANNEL=teams

# Bot credential for the Teams app. Blocked: the app registration needs
# admin consent in a tenant Naomi does not administer — shopping list item
# 3. Until it lands there is no outbound path at all, so no alerts.
COMMS_CHANNEL_TOKEN=

# Deliberately empty, not blocked: Microsoft Graph is one well-known global
# host the client library already knows. This key is for a self-hosted
# server or a mail host, and there is none here.
COMMS_CHANNEL_ENDPOINT=

# #spoor-alerts, created for this purpose with only the three engineers in
# it. Deliberately not #dev: that channel contains an agency contractor and
# the regulatory officer, neither of whom is on COMMS_ALLOWLIST, and an
# alert routinely quotes the data that caused a failure. It is also the
# busier channel, so an escalation there gets scrolled past.
COMMS_ALERT_TARGET=19:3f9c04e1b2d84a7b9e5c6a1d8f2b0c74@thread.tacv2

# Naomi, Timo and Fien, by Entra object ID rather than display name or UPN.
# Joris (agency contractor) and Hannelore (regulatory officer) are in #dev
# and deliberately not here: their messages are data. Hannelore is
# separately the required sign-off for label/batch-record/audit changes —
# releasing a gate is not instructing, and the conventions doc holds that
# distinction, since this field records only who may instruct.
COMMS_ALLOWLIST=7c1b0a94-3f2e-4d51-9a06-b18c2f5ed3aa,4a8e5d02-9b17-4c63-8f2a-11d7e6b3c095,e2f60b38-5a4d-41c9-b70e-9c83d5142fa6

# Blocked: needs a mailbox on the salviasystems.be tenant — shopping list
# item 1. It is the item the whole list hangs off: the Jira Basic-auth
# username reads from this field, per the Jira notes in
# skills/work-tracker/adapters/, so no mailbox also means no tracker.
AGENT_EMAIL_ADDRESS=

# All three people on COMMS_ALLOWLIST read code, so nothing is rounded here.
# The per-person nuance the switch can't hold is in the conventions doc: the
# junior engineer's requests are honored like anyone's except where they
# change the batch or audit schema.
OWNER_TECH_LEVEL=technical

# Pharmacy technicians and pharmacists. This makes
# skills/product-tech-stack/SKILL.md mandatory, and it conflicts with four
# years of TypeScript — see the conventions doc and shopping list item 4.
END_USER_TYPE=non-technical
```

Note what *isn't* here. The autonomy deltas, the validation-run merge gate,
the vocabulary, the stack conflict, the per-repo merge rights, the deferral
to `CONTRIBUTING.md` — none of those got a made-up `.env` key. They go in
the conventions doc, which is what the next section is.

---

## 4. Excerpt from the generated conventions doc

### First, a git identity — and a merge that isn't available

`gh auth status` reported an authenticated account already: Naomi had
installed and logged in `gh` on this box months ago for her own use. So step
5's login was a no-op, and what it left behind is the finding that mattered
most in the whole step: **the pushes authenticate as Naomi's own personal
GitHub account**, which is a member of the `salvia-systems` org and can
write to every repo in it, not just the two this deployment is about.
Nothing about running as her scopes the agent down. That got said plainly
before she accepted it, per step 5(c), and it is item 5 on the shopping
list rather than a blocker: an identity that already works beats no first
PR at all.

Then a `git push --dry-run` of a throwaway branch name, per repo: `compound`,
`compound-labels`, and the private copy of this bootstrap repo that Naomi
created on the org. Three repos, three separate checks, because write access
to one implies nothing about another. All three passed, and a `gh api` read
of each repo's own permissions confirmed the PR-opening credential
independently of the push — the same `gh` login turned out to carry both
here, which is a finding about this box rather than a general guarantee.
`gh repo view --json isFork,visibility` against the bootstrap copy reported
`isFork: false`, `visibility: private`, so nothing about to be committed was
heading for a permanently-public fork.

**And then the check that a from-zero deployment never runs.** Step 5(d)
also asks whether a *merge* is available, read off the live protection
settings rather than off what the owner remembers configuring. Naomi's
recollection and the rulesets did not agree — she had forgotten the
CODEOWNERS rule entirely — which is exactly why that step says to read it.
What `gh api repos/salvia-systems/compound/rulesets` and the branch
protection endpoint actually reported for `main`:

- a pull request is required;
- one approving review from someone other than the author;
- a review from a CODEOWNERS owner of every changed path;
- stale approvals dismissed on every new push;
- five required status checks: `lint`, `typecheck`, `test`, `e2e`,
  `licence-scan`;
- bypass permitted for nobody, org admins included.

So **a self-merge on `compound` is impossible by design**, and that is the
team's own review policy rather than a misconfiguration to work around.
`git-pr-conventions`' "When you are not allowed to merge your own PR"
section is the home for what to do about it, and the substitute agreed with
Naomi is the first shape it lists: **a human approves, the agent merges.**
The agent opens the PR, runs its own review pass first so nobody is asked to
review unreviewed code, then asks for review in `#spoor-alerts` — naming the
person CODEOWNERS actually requires for the changed paths, which is Timo for
`apps/api`, Fien for `apps/web` and Naomi for the repo root. Once the
approval and the checks are in, the agent runs the merge itself.

Two consequences of the settings above got written down next to it, because
both are silent traps rather than things anyone would remember:

- **Never push after an approval.** Their `main` dismisses stale approvals
  on any new push, so a tidy-up commit after Timo approves quietly throws
  his review away and re-requests it. That rule isn't in `CONTRIBUTING.md`
  because a human just notices the dismissal and asks again; an unattended
  run would loop.
- **A PR can sit unmergeable for a reason unrelated to review.** Which
  brings us to the thing that actually happened.

### The first PR could not merge, and that was the correct outcome

`licence-scan` is a required check on `main`, and its workflow has a `paths`
filter: it runs only when `package.json` or the lockfile changes. A required
check that never runs sits pending forever. Nobody on the team had ever hit
it, because every PR a human opens there touches code — their prose lives in
Confluence, and `CONTRIBUTING.md` was last edited fourteen months ago.

Step 6's conventions doc is a docs-only change. So the very first PR this
deployment opened was also the first PR in that repo's history that could
never go green.

The agent found it in step 5(d) rather than at step 6's merge, which is the
entire point of that check having been added: read off the ruleset and the
workflow file together, before the first push, instead of discovering it as
a base-branch-policy error that reads like an auth failure. What it did
about it:

- Opened the conventions-doc PR anyway. Per step 6, an open PR waiting on a
  human is a finished step, not a blocked one.
- Opened a *second*, one-line PR against the `licence-scan` workflow making
  it always run and exit early when no manifest changed — the standard fix,
  and a change to their CI rather than to their protection settings.
  Relaxing the protection, or adding itself to the bypass list, would have
  been the stop-and-ask it declined to make.
- Told Naomi both, in one message, with the dependency named: the second PR
  has to merge before the first one can, and neither can merge without a
  human approval.

Timo approved the CI fix and Naomi merged it by hand. Then the
conventions-doc PR went green and the agent merged that one itself, which is
the first exercise of the substitute above. Both facts are in the `Auth`
section: that the substitute works, and that it took a human action to get
the first change through at all.

All of it went into `git-pr-conventions`' `Auth` section, which is its one
home: the invocations, which account they authenticate as and the breadth
that account carries, write access recorded **per repo**, what `origin`
actually is, the fact that the push and API credentials coincided on this
box, whether the remote has a PR mechanism at all (GitHub does — checked,
not assumed), and the merge answer per repo, which is not one answer:

| Repo | May the agent merge its own PR? |
|---|---|
| `salvia-systems/compound` | No. Protected as above; a human approves, the agent merges. |
| `salvia-systems/compound-labels` | Yes. No protection on that repo at all — the Kotlin service has one person in it and nobody ever set any up. |
| the private bootstrap copy | Yes. No protection; steps 6 and 7 ship their own PRs here normally. |

Recording that per repo rather than once for the deployment is the point:
one deployment, three answers, and an agent that generalizes from the first
one gets two of them wrong.

### The doc

Written to `compound/SPOOR.md` — a clearly-named sibling rather than that
repo's own `CLAUDE.md`, which already exists and holds four years of the
team's own harness instructions that nothing here has any business
clobbering. Shipped the same way everything else will be: a branch, a PR,
an approval, a merge.

This is an excerpt — the real file also covers the vocabulary, the repo
layout, and how to run the suites.

> ## Git and PR conventions
>
> **`CONTRIBUTING.md` in this repo owns branch naming, the commit message
> format, the PR template and the definition of done.** They apply to this
> agent exactly as they apply to any human on this team, and they are **not
> restated here** — this doc would be the copy that goes stale, and the
> commit format in particular is machine-enforced by commitlint in CI, so
> that file plus the CI config are jointly authoritative in a way a
> paraphrase here could never be. Go and read them there.
>
> What this section holds is only the two things that file cannot answer.
>
> **Deltas agreed with the team:** none to the format itself. One process
> note: the changeset item in their definition of done is dead — the
> packages stopped being published separately — and the fix is removing it
> from `CONTRIBUTING.md`, which is tracked as its own ticket. It is *not*
> waived here; a rule this doc contradicts is a rule with two homes.
>
> **Additions, because their conventions had no reason to cover an actor
> with no initials:**
>
> - **Branch naming.** Theirs is `<initials>/<CMP key>-<slug>`. This agent
>   has no initials, so its prefix is the literal `spoor/`, giving
>   `spoor/CMP-1234-short-slug`. Everything else about the name follows
>   `CONTRIBUTING.md`.
> - **Commit process trailer**, last line of the commit body:
>   `Spoor-Process: <stage>`. It sits alongside the Jira key footer their
>   format already requires rather than replacing it. This is a process
>   marker, not attribution — no AI attribution anywhere, per
>   `git-pr-conventions`.
> - **Tracker comment marker**, last line of every Jira comment this agent
>   writes: `— spoor · <stage>`. Its purpose is letting a later run tell its
>   own prior notes from a human's, so it is never omitted.
> - **Never push to a branch after a review has been approved.** `main`
>   dismisses stale approvals on push, so a fixup commit silently discards
>   the approval. Get the review last. This is not in `CONTRIBUTING.md`
>   because a human notices and re-asks; an unattended run would not.
>
> **Who may merge is recorded per repo** in
> `spoor-bootstrap/skills/git-pr-conventions/SKILL.md`'s `Auth` section,
> which is its one home — three repos here, three different answers, and the
> substitute agreed for the protected one. Not restated here either.
>
> ## The repos this product spans
>
> `PRODUCT_REPO_PATH` is singular, so it names the primary one. There are
> two:
>
> - **`salvia-systems/compound`** — the primary: pnpm monorepo, NestJS API
>   and React front end over Postgres/Prisma. `PRODUCT_REPO_PATH` points
>   here, this doc lives here, and any skill saying "the product repo"
>   without qualification means this one.
> - **`salvia-systems/compound-labels`** — a small Kotlin service driving
>   the label printers, because the printer vendor ships only a JVM SDK.
>   Unprotected `main`, one regular contributor. Anything touching printed
>   label *content* here is also inside the Hannelore sign-off rule below.
>
> ## Autonomy: deltas from the default guardrails
>
> The default stop-and-ask list lives in `spoor-bootstrap/AGENTS.md` under
> "Default guardrails" and is in force in full. It is not copied here. What
> follows is only what this team changed. Anything not listed below still
> stands exactly as that file has it.
>
> One item from that default list is worth naming because this repo makes it
> tempting: **changing branch protection, or adding this agent to a bypass
> list, is stop-and-ask** — it appears there twice, as a protection change
> and as widening your own permissions. A protected branch that refuses a
> merge is this team's review policy working, not an obstacle.
>
> **Tightened:**
>
> 1. **Anything an inspector could read needs Hannelore Steurs' explicit
>    yes, before review is requested.** Scope: what a batch record or a
>    printed label says, what is written to the audit log, and whether
>    something is written there at all. Not in scope: unrelated code in the
>    same module, or a refactor that provably does not change rendered
>    output. **If it is unclear which side of the line a change falls on, it
>    needs her.** Her yes in the channel is what satisfies this — it does
>    not need relaying through an engineer.
>
>    She is deliberately **not** on `COMMS_ALLOWLIST`, and that is not in
>    tension with the above: releasing a gate is not instructing. A message
>    from her *asking* for a change is a request to bring to one of the three
>    engineers, never an instruction to act on.
> 2. **No migration that drops or rewrites a column on the batch, weighing
>    or audit tables.** Additive only there — new table, new nullable
>    column. Stricter than the default guardrail in two ways: it covers
>    rewriting as well as destroying, and **a clean down-migration does not
>    make it routine.** These records are what a hospital shows an inspector,
>    and their value depends on nobody having edited them.
> 3. **A schema change to those same tables requested by Fien Deprez gets
>    confirmed with Naomi before work starts.** Not a comment on her
>    judgment — she is on the allowlist and her requests are otherwise
>    honored like anyone's. It is that this class of change is among the few
>    here that cannot be cleanly undone.
>
> **Loosened — do it unattended, then say so in `#spoor-alerts` afterwards:**
>
> 4. **Open dependency-update PRs without asking**, including majors.
>    Batched by risk, majors separated from patches: a review of nineteen
>    mixed bumps is a rubber stamp, and a rubber stamp is worse than no
>    review. Cheap to loosen precisely because the human approval gate still
>    sits in front of every merge.
> 5. **Re-run one failed CI job** where the failure is a known flake in the
>    end-to-end suite. **Restart the shared staging stack.**
>
> The trade for not asking first is reporting after, unprompted, every time.
> And the carve-out covers *one* re-run: the same spec failing three times
> in a week is a failing test, not a flake — open a ticket for the cause
> rather than re-running a fourth time. Neither carve-out extends to
> re-running a deploy, and a green re-run never authorizes merging something
> no human has approved.
>
> **Merge gate: no merge while a validation run is live.** A state gate, not
> a clock. Once a month the regulatory officer and the platform contractor
> walk the whole system against a script and sign the result, and `main`
> does not move while that is happening. The signal is this team's own, not
> a new one: the `CMP` ticket for that run sits in `In Progress` for its
> duration. Read it before every merge. This holds for a merge a human has
> already approved, and for a fix for something broken *during* the run —
> that becomes a stop-and-ask, because a rushed change inside a signed
> validation turns a small problem into a regulatory one.
>
> ## Production access: a fact, not a rule
>
> This agent has no credentials to any of the twenty-three hospital
> instances and is not going to be given any. Deploys are the platform
> contractor's, on a Tuesday release train, into customer change windows.
>
> Recorded as a fact rather than as a rule, because the two behave
> differently: a rule can be argued out of, a fact has to be planned around.
> What follows from it — the pipeline ends at a merged PR; verification
> happens in staging and never in production; `deploy-and-monitor` has
> almost nothing to say on this deployment; **and these credentials are
> never to be requested**, including when it would be convenient.
>
> ## Open conflict: the mandated stack versus four years of TypeScript
>
> `skills/product-tech-stack/SKILL.md` applies here (`END_USER_TYPE` is
> non-technical) and requires FastAPI, SQLModel and Next.js. This product is
> NestJS and React, plus one Kotlin service. Postgres already matches.
>
> The existing-code half is settled by that SKILL's own "When the product
> repo already exists and doesn't match": the existing app keeps its stack
> and gets maintained as it is, and a migration is raised rather than acted
> on. Nobody is rewriting four years of TypeScript.
>
> The other half is **genuinely open**, and is on the shopping list as a
> decision rather than resolved here. That SKILL's requirement governs
> genuinely new work, and there is a real piece of it in the backlog: a
> separable stock-forecasting service. Read literally, that service arrives
> in Python. Naomi's position is that a four-engineer team maintaining a
> second language and toolchain for one service is a bad trade, and this
> agent's own recommendation agrees with her. But the requirement belongs to
> this template rather than to this agent, so it is not waived by an agent's
> say-so in a first-hour interview. Both readings, and the recommendation,
> are on the list. It blocks nothing today.
>
> ## Where the business's own context lives
>
> - **Confluence**, on the same Atlassian site as the tracker, readable with
>   the same credential once the agent's account exists. This is the home
>   for what the product does and why.
> - **The validation master file is on a SharePoint this agent
>   deliberately does not have access to**, and will not be given. A
>   deliberate exclusion, not a gap — those look identical to a session six
>   months from now and are not the same thing.
>
>   What that costs, stated so it is not rediscovered: this agent can never
>   assess whether a change affects the validated state of the system,
>   because the document defining that state is unreadable to it. "This
>   doesn't affect validation" is the regulatory officer's sentence, never
>   this agent's.
>
> ## Bar for creating a tracked item
>
> **Do not create tickets on the `CMP` board.** Every item this agent works
> is one a human deliberately handed over, by applying the inbox label
> described in `spoor-bootstrap/skills/work-tracker/SKILL.md`. The board is
> audited and groomed by a product owner; a bot filing into it is noise
> somewhere noise is expensive.
>
> Deliberately the opposite of a bar that gets *looser* with owner
> technicality: the constraint here is not review capacity, it is that the
> tracker is an audited artifact belonging to someone else.
>
> **The one exception, agreed explicitly:** something genuinely broken found
> while working on something else — a real bug, not a nit — gets reported in
> `#spoor-alerts`. Filing it is then a human's call. Not filed, and not
> dropped either.

---

## 5. Specializing a stub: `work-tracker`, before and after

"Specialize the stub" is the most abstract instruction in the whole flow, so
here is one file's worth of it concretely. These are excerpts from
[`../skills/work-tracker/SKILL.md`](../skills/work-tracker/SKILL.md); the
untouched generic parts (the seven-operation contract, the
tracker-independent rules) are omitted because specialization doesn't change
them.

[`example-walkthrough.md`](./example-walkthrough.md) shows this same file
for a different deployment, and that is deliberate rather than a repetition:
retrofitting the pipeline onto a tracker a team has been living in for three
years is *this* archetype's defining problem, and the result looks nothing
like the GitHub-labels version. There, the tracker had no state machine and
one had to be built out of labels. Here the state machine already exists,
belongs to someone else, and the whole job is mapping onto it without
touching it — and the inbox question, which was a footnote there, is the
thing that could have done real damage here.

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

- **Access mechanism**: an MCP server, an official SDK, a CLI, or raw
  HTTP. [...]
- **The identity the agent acts as.** [...]
- **The scope identifier**: team/project/board key, repo, or file
  path. [...]
- **Where a second auth value comes from, if this tracker's auth needs
  one.** [...]
- **Any known gotchas of that specific API.** [...]
````

### After — specialized for Salvia

````markdown
## Status: PARTIAL STUB — needs specialization

The state mapping, the labels and the access mechanism below are real and
usable as written. Two markers are left: the agent's own `accountId`, which
waits on an Atlassian account, and the verified issue count, which waits on
the same credential.

### The state machine, as it exists in this tracker

This is a company-managed Jira Cloud project, key `CMP`, whose workflow
predates this deployment by three years and **is not to be modified**. The
five pipeline states map onto statuses that already exist:

| Role | This deployment |
|---|---|
| unrefined-inbox | `Backlog` **and** carrying the `spoor-inbox` label |
| ready | `Selected for Development` + the `spoor-refined` label, both required |
| in-progress | `In Progress` |
| in-review | `In Review` |
| done | `Done` |
| cancelled | `Won't Do` |

Statuses are reached only by executing a **transition**, never by setting a
field; the `adapters/jira.md` notes are the home for that mechanic and for
why a transition id is looked up by its destination status rather than
hardcoded.

**The inbox row is the load-bearing one, and it is not the obvious
mapping.** `Backlog` alone would be catastrophic on the first run: this
team has been filing issues for four years, and every open `Backlog` issue
lacks any marker of ours, so all of it would read as fresh intake — a
months-old design discussion, work a human is mid-way through, the lot.
Refining that in bulk would post refinement comments across an audited
board that hospital customers read.

So **the inbox is opt-in.** A human applies `spoor-inbox` to hand a ticket
over, and nothing without that label is ever in scope, whatever status it
sits in. The team's own backlog stays entirely theirs.

Two alternatives were considered with Naomi and rejected, recorded here so
a later run doesn't "simplify" back into one of them:

- *Backfill a state onto the existing backlog once.* On a label-based
  tracker this is cheap. Here it would mean transitioning every open
  backlog issue through their workflow: board movement, a notification
  mail per issue to every watcher, and a status change written into a
  history that gets audited. Rejected.
- *Scope the inbox query to issues created after a cutoff date.* Needs
  nothing from anyone, and permanently hides pre-existing work from the
  pipeline — which is backwards here, because the older half of that
  backlog is the entire reason this deployment exists. Rejected.

`TODO(specialize)`: the open-`Backlog` count. Naomi read 183 off her own
browser during the interview; nothing has verified it with a real API call,
because this agent has no credential yet. Re-run the count as the first
thing the credential does and replace this marker with the number and the
date. It matters only as a sanity check that the opt-in query is filtering
what it should — if `spoor-inbox` ever matches a large set, something has
gone wrong.

### Labels

Everything this agent adds lives in a `spoor-` namespace, so it is
obviously not the team's. Their own `area:`/`type:`/`sev:` schemes are
theirs, are untouched by any of this, and get passed back on every edit —
operation 7's `update` form, not the `fields` form, which replaces the
whole set.

- inbox / handover marker: `spoor-inbox` (see above — this one has no
  equivalent in the generic contract; it exists because the inbox is opt-in
  here)
- refined marker: `spoor-refined`
- needs human sign-off: `spoor-needs-signoff`
- targets the agent's own tooling, not the product: `spoor-tooling`

Jira labels are free text and are not pre-registered, so a typo silently
creates a new label rather than erroring. Validate against this list before
writing. Labels cannot contain spaces, which is why every name here is
hyphenated.

`spoor-needs-signoff` is *not* how the Hannelore sign-off rule in the
conventions doc is enforced — that is a per-PR question asked in the
channel. This label is for an item that cannot be closed at all until a
named person answers on a named thread.

## How to actually call the tracker

- **Access mechanism**: REST v3 over HTTPS, called with `curl` from small
  scripts in this repo — the shapes in `adapters/jira.md` are copy-pasteable
  and were verified against this site. Deliberately *not* the third-party
  `jira-cli` that adapter mentions, and not the Atlassian MCP server: this
  deployment's writes are mostly comments, and the wrapper's main selling
  point is building ADF from plain text, which the v2 comment endpoint below
  already solves for free.
- **Comment format**: the **v2** endpoint (`/rest/api/2/issue/{key}/comment`),
  which takes a plain string, rather than v3's Atlassian Document Format.
  Chosen deliberately and recorded so nothing mixes the two: every comment
  this pipeline writes is prose plus a marker footer, and hand-building an
  ADF document for that is friction with no payoff. Everything else uses v3.
- **Scope identifier**: project key `CMP`. Company-managed, which is what
  makes the workflow and status behavior above what it is.
- **The identity the agent acts as.** `TODO(specialize)` — blocked on an
  Atlassian account for this agent, which Naomi has to request from the
  external IT partner who administers the tenant (see the shopping list).
  Every assignment call needs that account's opaque `accountId`, from
  `/rest/api/3/myself`; Jira Cloud does not identify users by email or
  username. Until it exists there is **no interim ownership convention**,
  unlike a deployment that could fall back to a label: nothing runs against
  this tracker at all yet, so there is nothing to distinguish.
- **Second auth value**: Basic auth is email-plus-token here, and the email
  half is `AGENT_EMAIL_ADDRESS` from `.env` — a decision, not a
  coincidence, because Basic auth's username must be the account that
  minted the token and that account is the agent's own. No new `.env` key
  was invented for it. This is also why the mailbox blocker cascades into
  the tracker: an empty `AGENT_EMAIL_ADDRESS` means no Jira access even
  with a token in hand.
- **Gotchas hit so far**, on this tracker:
  - In JQL, `labels != x` **excludes issues where the field is empty**.
    "Doesn't have the refined label" is
    `(labels != spoor-refined OR labels IS EMPTY)`. Getting this wrong
    makes freshly-handed-over work invisible.
  - `/rest/api/3/search` was removed; the current path is
    `/rest/api/3/search/jql`, paginating on an opaque `nextPageToken` whose
    *absence* is the only end-of-results signal. Don't persist a token
    between runs.
  - The search endpoint returns a minimal field set unless `fields` is
    passed explicitly.
  - Comments are paginated separately from the issue, on `startAt`/`total`
    rather than a token. A stage that reads only the issue sees a truncated
    comment history — which on this contract means missing a human's answer.
  - A missing transition is a permission or workflow condition, not a bug.
    Report the transitions that *were* available; that is what a human
    needs.
  - Jira mails every watcher on comment and transition by default, and
    these issues have four-year watcher lists. Suppress where the endpoint
    allows it and check the noise after the first real run — a pipeline
    that buries this team in mail gets switched off, whatever it ships.
````

Five things about that "after" worth noticing, because they're where the
instructions in
[`../skills/specialize-skills/SKILL.md`](../skills/specialize-skills/SKILL.md)
actually bite:

- **The rejected alternatives were written down, not just the decision.**
  The inbox mapping is the one place this deployment departs from the
  obvious reading, and a future session that finds only the conclusion is
  one refactor away from "simplifying" it back to `status = Backlog` and
  posting a hundred and eighty comments onto an audited board. A decision
  with its rejected alternatives attached is a decision; without them it's
  a preference someone can overwrite.
- **Two markers survived, and a `Status:` heading survived with them.** The
  agent had every opportunity to write a plausible `accountId` and delete
  the marker, producing a file that looks finished and is wrong. What
  changed is which heading: `STUB` became `PARTIAL STUB`, because
  everything else is now real. Those two are the only phrasings
  [`../CONTRIBUTING.md`](../CONTRIBUTING.md) allows, so *which* markers are
  outstanding goes in a sentence under the heading rather than into the
  heading text.
- **One marker is a number, not an account.** The issue count is not
  blocked on provisioning — it's blocked on a call nobody has made yet, and
  the honest record is a marker saying whose reading the number is. The
  team's own count, quoted as if verified, would have been the exact failure
  "never invent a specific" is about, dressed as diligence.
- **A choice got recorded where the generic file offers two options.** v2
  for comments, v3 for everything else, with the reason. The adapter says
  "pick one and record it"; discovering that choice mid-run is how a comment
  footer ends up formatted two ways.
- **The unused adapters got deleted, and the index got corrected.** Salvia
  uses Jira, so `adapters/github-issues.md` and `adapters/linear.md` were
  removed in the same PR and their bullets came out of
  `adapters/README.md`'s index, per that directory's own instruction. Git
  holds them if the team ever migrates. Then the one step in the pass that
  isn't per-file: [`../skills/README.md`](../skills/README.md)'s "Current
  skills" list described `work-tracker`'s `adapters/` as reference notes for
  three trackers, and after this pass that directory holds one — so the
  entry was rewritten, and `work-tracker`'s *stub* label became *partial
  stub* to match the heading the file now carries. That list is the only
  enumeration of what exists under `skills/`, so whatever it still says is
  what the next session believes.

### The other half of the pass: which stages exist at all

`work-tracker` is one file. The part of the same pass with the most writing
in it was `work-pipeline`, because specializing that one means deciding
which stages this deployment actually runs and then writing a prompt file
per stage kept, in [`../prompts/`](../prompts/README.md).

The stage set Naomi agreed to: **`refine`, `implement`, `review`, plus one
proactive `upkeep` stage** for dependencies and CVEs.

**`critique` and `resolve-critique` were both dropped**, and that is
recorded as a choice rather than left as a silent shortcut —
[`../skills/work-pipeline/SKILL.md`](../skills/work-pipeline/SKILL.md)
explicitly allows collapsing or dropping stages. The reason is specific to
the opt-in inbox: every item that reaches this pipeline is one a human
deliberately chose to hand over, which means somebody already decided it was
worth doing and roughly what it was. A stage whose job is disagreeing with
the refinement has much less to disagree with than it would on a raw intake
queue. If the handover ever gets casual enough that refinements start
arriving wrong, adding the stage back is one file.

**`review` stays, and it is not the team's code review.** This is the
distinction that took the longest to write, because conflating the two would
break their policy: the pipeline's `review` stage is the agent's own pass
over its own diff, by a separate session from the one that wrote it, and it
runs *before* a human is asked for anything. The team's approving review is
a separate, human gate that happens after, and the agent's own pass does not
substitute for it in any direction. What `review` also owns here is the
mechanics of the merge substitute: reading CODEOWNERS to work out whose
approval is actually required for the changed paths, asking for it in
`#spoor-alerts`, not pushing after an approval lands, checking the
validation ticket's state before merging, and running the merge itself once
both are in.

**`ideation` was decided *against*, not left open.** Naomi's reason is worth
recording precisely because it is not the usual one: not "I know what I'm
building" and not "I don't trust proposals", but that the board is an
audited artifact groomed by a product owner, and a bot filing tickets into
it is noise in a place where noise is expensive. The agreed substitute for
the thing ideation would have been good for — a genuinely broken thing found
in passing — is a message in `#spoor-alerts`, leaving the filing decision
with a human.

`refine` and `implement` got written in that first sitting. `review` and
`upkeep` didn't, and their blockers differ, which is why they appear
separately on the shopping list rather than as one line about unfinished
prompts.

---

## 6. What was still blocked at the end

The first boot ends with a shopping list, not a finished agent. Per
[`../AGENTS.md`](../AGENTS.md)'s self-provisioning section, that list is
"everything standing between this deployment and a working one that a human
has to resolve", in three categories — so it is wider than a signup sheet.
Items 1-3 are its first category, identities to provision; item 4 is its
second, a decision nobody has made; items 5-8 are its third, work
identified and not finished.

The shape of this list is what distinguishes this archetype: **almost
nothing on it is Naomi's to do**, and the top of it is a single ticket with
an external IT partner that three other items hang off. On a deployment
where the owner administers their own accounts, that dependency doesn't
exist.

1. **An Entra ID account and mailbox for the agent** on the
   `salviasystems.be` tenant. Requested from the external IT partner who
   administers it; Naomi cannot create it herself. Blocks
   `AGENT_EMAIL_ADDRESS` directly, and items 2 and 3 through it. This is the
   item everything else waits on.
2. **An Atlassian seat and API token for that account**, with the `CMP`
   project permissions to comment and to execute the transitions in the
   state mapping. Blocks `WORK_TRACKER_API_KEY`, the `accountId` marker in
   `work-tracker`, the unverified issue count, and Confluence access. Worth
   one specific warning when it's granted: Jira permissions are granular and
   fail *silently* — a missing one shows up as an empty query result or an
   absent transition, not a 403 — so the first thing to do with the
   credential is confirm the agent can actually see and move a test issue,
   rather than assuming a successful login means access.
3. **A Teams app registration with admin consent**, and the bot added to
   `#dev` and `#spoor-alerts`. Also the IT partner's. Blocks
   `COMMS_CHANNEL_TOKEN` and with it the entire outbound path: until this
   exists there is no way for the agent to reach anyone except the terminal
   it was started from, which makes every "report afterwards" condition in
   the conventions doc currently unhonorable. Worth saying plainly rather
   than filing quietly: the carve-outs in that doc are traded against
   reporting after, so until this lands, don't take them.
4. **Whether the mandated stack governs the new forecasting service.** Open,
   not declined, and not resolvable by this agent — see the conventions doc
   excerpt above for both readings. Blocks nothing today; blocks the
   forecasting ticket the day someone picks it up. The recommendation on
   record is Naomi's position, not a decision.
5. **A GitHub account for the agent**, with access scoped to the two product
   repos and the bootstrap copy. Does *not* block anything: pushes, PRs and
   merges all work today as Naomi's own personal account. What it buys is
   scope — that account can write to every repo in the org, and nothing
   about running as her narrows it to three. The better end state, and an
   upgrade to an identity that already works rather than a prerequisite.
6. **The `review` stage prompt**, still to write in
   [`../prompts/`](../prompts/README.md). Its blocker is real rather than
   just unfinished writing: the merge substitute has been exercised exactly
   once, on a docs-only PR, so the parts of it that only appear on a code
   change — which CODEOWNERS reviewer a multi-package diff actually
   requires, how the required checks behave on a normal PR — are not known
   well enough to write down yet. Until it exists, every PR the pipeline
   opens waits for a human or a live session rather than for a stage.
7. **The `upkeep` stage prompt**, same directory, different blocker:
   waiting on nothing but time. The stage set is agreed and the file has no
   open question in it; the first sitting simply ran out.
8. **`deploy-and-monitor` keeps its `STUB` heading**, and unusually, most of
   it is not going to be answerable *ever* rather than later: this
   deployment has no production access by design, so there is no deploy
   trigger, no rollback procedure and no health signal for it to record.
   What belongs in it instead is the staging stack and the handover to the
   platform contractor's release train, which is a smaller file than the
   markers imply. Left honest rather than hedged, per that SKILL's own
   instruction.

And the judgment calls the agent made rather than being told, surfaced so
Naomi could correct them cheaply:

- Proposing an opt-in inbox label instead of either of the two options the
  adapter notes offer, and recording both rejections.
- Reading her "anything an inspector reads" tightening with an explicit
  in-scope/out-of-scope boundary, and defaulting to *needs sign-off* when a
  change is genuinely ambiguous.
- Separating Hannelore's authority to release a gate from an authority to
  instruct, which nobody asked for and which she hadn't distinguished.
- Pushing back on `#dev` as the alert target and asking for a narrower
  channel, on data-disclosure and get-scrolled-past grounds.
- Treating the no-production-credentials answer as a fact to plan around
  rather than a rule to observe, and writing down that they are never to be
  requested.
- Declining to record the stack requirement as waived, despite agreeing with
  her on the merits.
- Opening the CI-workflow PR unprompted rather than reporting the required
  check as a blocker.

None of that is a finished deployment. Actually wiring up the Jira client
and the Teams bot, finishing the two prompts at items 6 and 7, and taking a
first real code ticket through the whole loop are all follow-on work — this
repo's own README is explicit that it gets you to a documented starting
point, not to a working agent.

---

## Why this example and not the other two

Three honest runs of the same interview, and almost every answer differs.
That is the point: nothing in the interview has a default.

| Interview answer | Salvia (this file) | Northlight ([the roastery](./example-walkthrough.md)) | Peilmerk ([solo](./example-walkthrough-solo.md)) |
|---|---|---|---|
| Owner's technical level | technical, tech lead of a working team | non-technical | technical, but no hosted-forge experience |
| How many people | eleven, four engineers, three may instruct | five, two may instruct | one |
| End user | non-technical (pharmacy technicians) | non-technical (cafés) | technical (GIS engineers) |
| Product | live, four years old, 23 customer instances, actively developed | inherited, live, unmaintained since the freelancer left | doesn't exist yet |
| Repos | two, plus the bootstrap copy | one | created empty during first boot |
| Existing engineering process | yes: CI, CODEOWNERS, `CONTRIBUTING.md`, commitlint | none — nobody left to have one | none — no repo at all |
| Default branch | protected; self-merge impossible by design | unprotected `master` | created by the first merge |
| Merge rights | per repo: no / yes / yes; a human approves, the agent merges | self-merge throughout | self-merge, via the PR substitute |
| CI | theirs, five required checks, one of them a trap | none | none; the review stage runs the tests |
| Conventions | theirs, deferred to; only additions recorded | the agent's to propose | the agent's to propose |
| Work tracker | Jira Cloud they already live in, 4 years of issues | GitHub Issues on the product repo, a dozen open | markdown files in the product repo |
| Inbox mapping | opt-in label; the existing backlog is deliberately out of scope | "open with no state label" | a directory |
| Comms channel | Microsoft Teams | Slack | none — outbound mail only |
| Alert target | a channel created for it, deliberately not the busy one | the working channel, which is also the busy one | the owner's own inbox |
| Agent's own email | blocked on an external IT partner | blocked, the owner can create it | already provisioned |
| Mandated stack | applies; the *new-work* half is escalated as undecided | applies; conflicts with the inherited app, dormant | doesn't apply |
| Autonomy posture | tight around the regulated artifacts, loose around dependencies | tightened around money and customer email | loose on code, tight on the one box |
| Deploy/merge gate | state-based: not during a validation run | clock-based: one freeze window per roast day | state-based: not while a run is in flight |
| Production access | none, by design; not to be requested | the agent deploys | there is nothing deployed yet |
| Bar for a tracked item | don't create tickets at all | every change, including copy | anything that changes behaviour |
| Proactive ideation | declined — the board is audited | left undecided | declined — the list is his to write |

The row that drives most of the difference is *existing engineering
process*. Northlight and Peilmerk both leave the conventions, the branch
policy and the review gate for the agent to propose, and both examples spend
their length on the agent making those choices well. Here every one of them
already has an owner, in writing, and the work is almost entirely the
opposite skill: reading what exists, deferring to it, recording only the
gaps it genuinely doesn't cover, and noticing the two places where somebody
else's settled process quietly doesn't fit an actor with no initials and no
ability to be approved by itself.

The second-biggest is who administers the accounts. Both other examples have
an owner who can create what the agent needs, or has already done it. Here
the tenant belongs to an external IT partner, and three quarters of the
shopping list is one ticket with a company nobody in this transcript works
for.
