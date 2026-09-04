---
name: deploy-and-monitor
description: How a merged change actually reaches the running product, how it gets rolled back, whether the data is backed up and whether a restore has ever been verified, and how this agent instance knows the product is healthy — including the common case where the product already has a CI/CD pipeline this agent did not build and must not duplicate. Read before merging something that has to deploy, before touching the running deployment, before touching a backup or a dump, or when investigating a failure. Ships as a stub — the environments, deploy mechanism, backups and health signals are per-deployment.
---

# deploy-and-monitor

## Status: STUB — needs specialization

`AGENTS.md` says this agent "deploys, monitors, and fixes what breaks", and
nothing in this repo yet says how. That gap is what this file marks. Every
`TODO(specialize)` below has to be filled in against the owner's real host
and product before this agent operates anything live — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

Docker is the one safe assumption: it's a hard requirement `install.sh`
installs, and the required stack for a non-technical end-user's
product includes it (see
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md)). That the
*daemon* is up is a weaker claim: `install.sh` verifies it and starts it
where the box has systemd, and on a box without systemd logs NOT VERIFIED
and continues. Compose is typically present too, since docker's own
installer brings it along, but nothing here guarantees it either. Run
`docker info` and `docker compose version` and check both before relying on
them. Everything else here is open.

Note what that assumption is *about*, because it is easy to carry one step
too far. `install.sh` sets up the box this agent operates from, so Docker
being present is a fact about **that** box and not about wherever the
product is deployed. A managed platform — a static host, a PaaS that builds
from a git push — routinely has no Docker, no shell, and no host to be on
at all, and on one of those every white-box command in this file is
unrunnable against the target rather than merely inconvenient. Settle which
shape the target is before reading any procedure here as executable, per
"What 'monitor' means when you don't have the host" below.

## First: does a deploy pipeline already exist?

Answer this before reading any further, because the rest of this file reads
naturally as instructions for *building* a deploy path, and on an inherited
product it usually isn't yours to build. A product that already has users
has been reaching production somehow for as long as it has had them, and
that mechanism is normally a CI/CD pipeline the team owns: a workflow file
in the repo, a self-hosted or hosted runner, a provider that builds on
push, a release script somebody runs. Assuming otherwise produces the two
worst outcomes available here — a second, competing deploy path, or a
pipeline re-triggered by an agent that didn't know what triggering it does.

The resolution has the same shape as an inherited stack, and is settled the
same way — see
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md)'s "When the
product repo already exists and doesn't match". **What is already there
keeps its job. You fill the gaps around it and defer to it everywhere
else.** Don't re-derive a different answer per deployment, and don't read
this file's `TODO(specialize)` prompts as a mandate to build what those
answers describe.

**Read before you ask, then ask what reading couldn't settle.** The
interview covers this — [`AGENTS.md`](../../AGENTS.md)'s first-boot
interview question about an existing product repo is where it's asked, and
that list is its home — but most of it is discoverable without spending the
owner's time: pipeline config in the repo (a `.github/workflows/`
directory, `.gitlab-ci.yml`, a `Jenkinsfile`, a provider config file), the
deploy-shaped job names in it, the provider's own run history and
deployment/environment records over its API, and the last few merges
compared against what shipped. What reading cannot settle is exactly what's
worth the owner's time:

- **Which of it is live, and which is abandoned.** A workflow file that
  hasn't run in a year and a workflow that runs on every merge are
  indistinguishable in the diff. The provider's run history answers it; ask
  only if it can't.
- **Whether a production deploy is automatic on merge or a deliberate human
  act.** This is the single most consequential answer in this section: it
  decides whether *your* merge is what ships to production. See "How this
  interacts with the merge gate" below.
- **Who is notified when a deploy fails today**, and whether that
  destination is one this agent can read. It usually isn't — see "What
  'monitor' means when you don't have the host".
- **What the pipeline does beyond deploying** — migrations, cache
  invalidation, a customer-facing notification, a paid-minutes budget.
  These are what make a casual re-run expensive rather than idempotent.

`TODO(specialize)` — record the answer plainly, including the negative one.
"There is an existing pipeline and this agent did not build it" and "there
is no automated deploy pipeline at all" are both real answers a reader needs
to know were *decided* rather than skipped. Name the file or provider
setting that owns the pipeline and let it stay the one home for its own
steps — don't restate them here, and don't copy its job names, branch
filters or environment names into this file, since it owns those and this
file goes stale the first time the team edits one. Any autonomy delta that
comes out of the conversation (may this agent re-run a failed deploy? may
it edit the pipeline config?) belongs in the deployment conventions doc at
`CONVENTIONS_DOC_PATH`, which is the home for autonomy, and only gets
pointed at from here.

### What your job is when one exists, and what it isn't

**Defer entirely, and don't duplicate:**

- **Building, testing, releasing and deploying.** The "Whose job deploying
  is" bullet below is the rule and this is its most common instance: your
  session's job ends at the merge. Don't add a second deploy path, don't
  run the deploy command by hand alongside the pipeline, and don't add a
  workflow that overlaps one that's already there.
- **Re-triggering anything.** A re-run is not a free retry: depending on
  what the pipeline does it can redeploy, re-run a migration, invalidate a
  cache, notify customers, or spend paid runner minutes. Deciding a failed
  production deploy should be retried is the team's call unless the
  conventions doc explicitly says it's yours, and the pipeline's own output
  is what distinguishes a transient infra failure from a real one — the "a
  green CI run is not proof a deploy happened" rule below already says to
  only retry on the former, and inheriting someone else's pipeline is where
  that restraint matters most.
- **Editing the pipeline config as a side effect of unrelated work.** It is
  revertable like any commit, but its blast radius is the team's entire
  delivery path, and a break in it blocks every human on the team, not just
  you. So it's a change agreed and shipped on its own, never a drive-by fix
  inside a product change.

**Yours, and worth doing precisely because the pipeline doesn't:**

- **Confirming the outcome of a deploy your own merge caused.** "A merged
  change that isn't running is not shipped" below survives an inherited
  pipeline completely intact — you just read the outcome rather than
  driving it.
- **Getting the failure signal to this deployment's comms channel.** This
  is very often a genuine gap rather than a duplication: an existing
  pipeline notifies whoever set it up, on a channel this agent has no
  access to, which means a failed deploy is invisible to it by default. A
  read-only watcher this agent runs — poll the provider's run history,
  alert on a failed or missing run — supplements without touching their
  pipeline. Changing the pipeline itself to notify this agent is the
  cleaner fix and is a change to *their* pipeline: propose it, don't just
  make it.
- **The gaps a deploy pipeline structurally doesn't cover**, which is most
  of the rest of this file: backups and whether a restore has ever been
  verified, health after the deploy has gone green, disk filling up. Check
  each is actually a gap first — a team with a mature pipeline often has a
  backup job too — but don't assume a pipeline's existence implies any of
  them.

Two responders on one box is the standing hazard here, not a one-off: the
"which of them this deployment already had before this agent existed"
bullet in the Monitoring section below is its home, and everything it says
about read-only signals and paused monitors applies to an inherited
pipeline the same way.

### How this interacts with the merge gate

[`skills/git-pr-conventions`](../git-pr-conventions/SKILL.md)'s shipping
loop merges once the change has been reviewed and its checks are green.
Where the team's existing CI *is* the required status check on the default
branch, **that is the gate already** — it is not something to reproduce.
Don't stand up a second verification, and don't reach for that skill's
run-the-tests-locally substitute, which exists specifically for a remote
with no hosted CI. Two consequences:

- **A red or pending required check blocks your merge even where the
  provider wouldn't enforce it.** That skill's "Required status checks"
  bullet is the home for the failure shapes here — a check that never runs
  for your changed paths, or one the agent cannot influence such as a
  human-gated environment approval. Read which checks are required and
  confirm they run for the kind of change you're shipping; don't work
  around one, and don't merge past a red one on the grounds that it looked
  unrelated.
- **Where the pipeline deploys on merge, merging is deploying.** The merge
  stops being the cheap, reversible act the shipping loop treats it as, and
  the rollback procedure recorded below — not the PR revert — is what
  actually undoes it. Know which of the two shapes this deployment is
  before merging anything that touches the running service.

## Deploying

`TODO(specialize)` — record, concretely:

- **How many environments there are, and what the gate between them is.**
  A single production app is one answer; a staging app that a change has to
  pass through first is another, and it changes what every other bullet
  here means. Where there is more than one, record what promotion to
  production is gated on — a clock (a freeze window, a business-hours ban),
  a state (a soak period green on a monitor, a manual smoke test), or a
  person's sign-off — and whose the gate is to waive. **Say so explicitly
  when there is only one environment**, rather than leaving it unstated: a
  reader who assumes a staging app that doesn't exist will treat an
  untested change as pre-soaked.
- **What triggers a deploy.** A push to the default branch via CI, a
  self-hosted runner, a webhook, a scheduled pull, or a command run by
  hand. Name the actual mechanism and where its config lives. With more
  than one environment there is usually more than one trigger, and they are
  rarely the same shape — an automatic one into staging and a deliberate,
  attended one into production is the common pair. **Where the mechanism
  predates this deployment, this bullet is a record of what you found, not
  a design decision** — see "First: does a deploy pipeline already exist?"
  above, and name the config that owns it rather than describing its steps.
- **Which command deploys**, and from where. If a script owns this, name
  the script and let it be the one home for the procedure — don't restate
  its steps here.
- **Whose job deploying is.** If an automated pipeline handles it, a
  merging session's job ends at the merge: it must not also pull and deploy
  against the primary checkout, because that duplicates the pipeline and
  can race it on the same working tree.
- **How to roll back the code.** This is the safety net the whole autonomy
  model rests on, so it has to be a known, tested procedure, not an
  improvisation discovered during an outage. Record what it does *not*
  cover while you're at it: a code rollback does not roll back a migration,
  which is why an additive migration can be routine while a subtractive one
  isn't. Two things make the difference between a recorded procedure and a
  tested one, and both belong in this answer:
  - **Run it once, for real, against the real target, during
    specialization** — deploy something trivial, roll it back, and record
    what happened. "Tested" otherwise has no owner, and a rollback path
    first exercised during an outage is an improvisation whatever the file
    says. Record the measured time from issuing the rollback to the old
    behavior being observably live, because that number is what an incident
    gets judged against, and an unmeasured one gets guessed at under
    pressure.
  - **Assert that the rollback was actually initiated before waiting on
    it.** A rollback that never started and a rollback still propagating
    look identical from the outside: both show the bad version still live.
    So a wait loop polling for the old behavior to return will happily
    produce minutes of plausible output for a rollback whose first command
    errored and did nothing — silence read as patience. Check the rollback's
    own precondition first (the revert commit exists, the redeploy was
    accepted, a new run appeared) and only then start waiting.
- **How the data gets recovered, which is a different procedure.** See the
  backup section below. Conflating the two is how a bad hour becomes a bad
  week: rolling back a release is cheap and reversible, restoring a
  database is neither.

Four things that are true regardless of mechanism:

- **A green CI run is not proof a deploy happened.** A deploy step can
  legitimately exit zero while reporting nothing to do. After merging
  something that should have changed the running service, predict what
  should have redeployed and compare that against what the run reports it
  actually did. Flag a genuine mismatch; only retry when the output clearly
  points at a transient infra failure.
- **A merged change that isn't running is not shipped.** Name the
  observable — the running service serving the new behavior, the job
  present in the schedule, the container restarted on the new image — and
  check it. **Where there is more than one environment, say which one you
  mean**: a change merged into a staging branch is shipped to *staging*
  when staging is observably running it, and not shipped to production at
  all until it has passed the promotion gate recorded above and the same
  observable is checked against production. Both halves are real, and
  reporting the first as though it were the second is the mistake this
  rule exists to prevent — "merged" is not one destination once there is
  more than one environment.
- **"Is the latest run green?" reads the run before yours.** Asked in the
  seconds after a push, a provider's latest-run or latest-build record is
  still the previous one: yours has not been created yet, or has not left
  its queued state. So the obvious post-merge check answers with the *prior*
  deploy's success and reports your own as fine — a false green that arrives
  exactly when someone is watching for it. Correlate on the revision you
  actually shipped, using whatever the provider exposes for it (the run's
  head SHA, the deployment's ref), rather than trusting whatever "latest"
  returns; and where a poll is the only option, require the record's own
  identity to have changed before reading its status at all.
- **A status field that never reaches a terminal failure state alerts
  nobody.** The rule above covers a deploy that reports success without
  doing anything; this is its mirror, and it is the quieter of the two. A
  provider's status can sit in a non-terminal value — `building`, `pending`,
  `in_progress` — indefinitely on a build that has already definitively
  failed, with its own error field left empty, so a monitor whose condition
  is "status equals failed" never fires and a dashboard reading the same
  field shows work still in progress. Two consequences for how the signal
  gets built: alert on **elapsed time in a non-terminal state** against what
  a normal deploy takes, not only on an explicit failure value; and prefer a
  signal that is guaranteed to reach a terminal state over a
  provider-specific status field that isn't, where the deployment has both.
  The **absence of a new success** is the most reliable form of this and the
  one to build on where nothing better exists — a deploy that should have
  produced a fresh success record and didn't is a failure however the
  provider chose to describe itself.

## Backups, and whether they actually restore

Nothing else in this repo asks this, and on a product that already has
users it is the most load-bearing unverified assumption on the box. The
guardrail lists cover *not deleting* a backup; they say nothing about
whether one exists or whether it works.

`TODO(specialize)` — record:

- **What is backed up, by what, to where, and how often.** Point at the
  cron line, unit or provider setting that owns the schedule and retention
  rather than copying the numbers here. If the honest answer is that
  nothing is backed up, that is the single most important thing in this
  file and it belongs on the shopping list, not in a hedge.
- **Whether the product holds any state of its own.** "Nothing is backed
  up because there is nothing stateful to back up" is a real answer for a
  stateless deploy — a static site, a service whose only durable data lives
  in a managed third-party system — and it is a different answer from the
  one in the bullet above, which is an unprotected product. Say which of
  the two it is explicitly, because they read identically as "no backups"
  and only one of them is a problem. Where it's genuinely the stateless
  case, the load-bearing thing is what remains: the source repository is
  then the only copy of the product, so whoever hosts it is the single
  point of failure, and the managed system holding the real data has its
  own retention and export story that is now this answer's substance
  rather than a footnote.
- **How a backup's success and failure are signalled.** A job that only
  logs locally is silent by nature: it fails the same way it succeeds. A
  heartbeat/push monitor that alarms on the *absence* of a signal is the
  right shape, and worth naming as such where one exists.
- **How a restore is verified, and when it last was.** A completed upload
  is not a verified backup: it proves the job ran, not that the dump is
  restorable. Verification means restoring into a throwaway target and
  asserting against the *restored* data — the expected tables exist and
  carry plausible row counts — because a restore that succeeds into an
  empty schema is exactly the failure a file-size check cannot see. Record
  whether this has ever actually been done. "Never" is common and is a real
  answer worth the owner hearing.
- **Where the restored copy is allowed to live, and what may be said about
  it.** A production dump is usually the most sensitive artifact this agent
  can touch, and copying it is a distinct risk from destroying it — which
  is all the default guardrails cover. If the owner needs it stricter (no
  dump on the agent's own disk, no row content in a message or a prompt,
  aggregates only), that tightening is theirs to state and the conventions
  doc at `CONVENTIONS_DOC_PATH` is its home; ask, rather than assuming the
  default is enough.
- **Whether restoring is ever something this agent may do unattended.**
  Verifying a restore into a throwaway target can reasonably be a
  carve-out. Restoring over live data is not one, and has no concrete
  rollback, so `AGENTS.md`'s default guardrails govern it.

## Monitoring

`TODO(specialize)` — record:

- **The health signals that exist.** Container health checks, an HTTP
  health endpoint, disk/memory thresholds, log-based error detection,
  external uptime checks. List the ones this deployment actually has; don't
  list aspirational ones. **List what conspicuously doesn't exist too**,
  where its absence changes behavior — no error tracking means an
  exception affecting one user produces no alert at all and surfaces only
  through a human, which is worth knowing as a fact rather than
  discovering.
- **Which of them this deployment already had before this agent existed,
  and who else they already alert.** On a live product the monitoring is
  usually the owner's, not the agent's, and that has three consequences the
  generic case doesn't have: an incident has two responders by default and
  they can end up operating on the same box at once; some signals are
  read-only to this agent (changing or *pausing* a monitor is an autonomy
  question, and a paused monitor is an invisible outage); and some signals
  may not reach this agent at all, because they alert a human's inbox it
  has no access to. Record which are readable, which are read-only, and
  which are invisible — an invisible signal is not coverage.
- **How to tell a live signal from an abandoned one.** A green dashboard
  and a monitor nobody has fed in months look identical at a glance. For
  each signal, record what answers "when did this last actually change
  state or receive a beat?", and treat a heartbeat that went green around
  the time someone last touched its job as evidence of nothing.
- **Where they run and how often.** Point at the host schedule config
  rather than inlining a cadence — see
  [`skills/README.md`](../README.md) on scheduling being out of a SKILL's
  scope.
- **What the agent is allowed to fix unattended.** Restarting an unhealthy
  container and clearing a filled disk of the agent's own artifacts are
  common carve-outs; deleting anything the owner might want is not. This is
  an autonomy question, so it belongs in the deployment conventions doc —
  read its path from `CONVENTIONS_DOC_PATH` in `.env` — and only gets
  *pointed at* from here. Anything that doc doesn't explicitly permit
  unattended falls back to [`AGENTS.md`](../../AGENTS.md)'s "Default
  guardrails" list, which is that list's one home — read it there rather
  than from a subset restated here.
- **Where an alert goes.** One destination, per
  [`skills/comms-channel`](../comms-channel/SKILL.md).

Every signal above answers a question about the *machinery* — a process is up,
a disk has room, a deploy produced a fresh success record. None of them
answers whether a person could still complete the thing the business exists
for, and that question fails silently: a health endpoint answers 200 with a
broken checkout behind it. Continuously re-proving the product's own
user-facing flows, by driving them the way a user does and checking the real
side effect happened, is
[`skills/synthetic-monitoring`](../synthetic-monitoring/SKILL.md)'s — which
flows are worth it, what counts as proof, and how it writes to production
without polluting it. A synthetic check is one more entry in the inventory
above, so record it there like any other signal; nothing about how to choose
or operate one is restated here.

The signals above are this file's, and stay this file's. Putting them on a
page for the owner to look at is a separate artifact with its own concerns
— see [`skills/internal-dashboard`](../internal-dashboard/SKILL.md), which
owns the dashboard's project shape and its honesty rules and points back
here rather than restating any signal. Note that a dashboard is *not*
itself a signal: it has no beat of its own, so it cannot tell you it has
stopped refreshing, which is precisely the live-versus-abandoned failure
the bullet above describes.

### What "monitor" means when you don't have the host

`AGENTS.md` says this agent monitors the product; nothing anywhere grants
it access to the machine the product runs on. `install.sh` sets up the box
the *agent* operates from — docker, `uv`, the `gh` binary, docker-group
membership on that box — and that is the whole of its reach. It never
touches the product's production host, which on an inherited product is
routinely a different machine, or a managed platform with no shell to have
access to at all. So don't write a monitoring procedure whose steps
silently assume SSH, `sudo` or systemd on the product host. Split the
signals by what they actually require:

- **Black-box, needs no access to the product host.** An HTTP request from
  this agent's own box against a health endpoint or a real user-facing URL,
  asserting on status and on something in the body rather than only on a
  connection succeeding. **When the question is whether a deploy landed,
  that assertion has to name the revision, not just valid content**: a
  platform that keeps serving the last good release through a failed build
  answers 200 with an entirely correct body, so every check short of
  "the thing I just shipped is present" passes while nothing shipped. Give
  the product a marker that changes per release — a build identifier in the
  response, a version field on the health endpoint — and assert on the value
  expected for the revision under test. Without one, this check cannot
  distinguish a successful deploy from a failed deploy of a healthy service,
  which is most of what it would be asked. The CI/CD provider's run and deployment history
  over its API (`gh run list` and the deployments/environments endpoints on
  a GitHub-shaped remote, the equivalent elsewhere) — which is what makes
  watching an inherited pipeline possible without touching it. An external
  uptime checker. An error tracker's API. The platform's own status page.
  These are available to a scheduled run with nothing but network and a
  token, and they are the honest floor of what "monitoring" means here.
- **White-box, needs to be on the product host.** `docker ps` / `docker
  logs` / container health status, `journalctl` or `systemctl`, log files,
  disk and memory thresholds. Real and much more informative — and
  available for free when the product runs on this same box, which is the
  single-box deployment this template's own defaults suit best. On any
  other shape each of these needs access somebody has to grant.

`TODO(specialize)` — record which of the two each signal is on this
deployment, and whether the product runs on this box or elsewhere. A
white-box check written down for a host this agent cannot reach is not
coverage, for the same reason the invisible-signal bullet above gives: it
reports nothing and looks like a plan. Where the useful signal needs access
that doesn't exist yet, that access is an item for the owner's
self-provisioning shopping list per [`AGENTS.md`](../../AGENTS.md) — asking
for it is the route, and helping yourself to it (adding your own key,
widening your own permissions) is on the default guardrail list, not a
workaround.

Where a black-box check is all there is, say what it cannot see rather than
letting a green result overstate itself: a health endpoint answering 200
says the process is up, not that a background job is running, that a queue
isn't backing up, or that one user's requests are failing.

## When something breaks

- **Investigate the root cause, not just the symptom** — from the first
  occurrence, not after the third. A symptom patch on a recurring failure
  buys nothing and hides the real defect.
- **Read the real logs before naming a cause.** A plausible explanation is
  not a verified one, and reporting a guess as a finding is worse than
  saying you don't know yet.
- **Never swallow an error and continue as though nothing happened.** No
  bare catch-and-proceed, no defensive default papering over a missing
  value, no fallback quietly substituting something plausible. And never
  hand a model an error string as though it were content — an unreadable
  input is omitted and reported, not rendered into a prompt for the model
  to read as fact.
- **A recurring breach deserves a structural fix**, not a repeated report
  of the same breach.
- **Check whether the platform is down** before doing surgery on your own
  system. A stuck CI run can be the provider's outage, not your bug.

## Secrets

Real credentials live only in `.env`, which is gitignored and disk-only.
Never put a real secret in a committed file, a code comment, a doc, a work
item, or a message. Reference the variable *name* when documenting
configuration, never the value.

`.env`'s mode is `0600`, and that is a standing invariant rather than a
one-time step at creation: gitignoring a file does nothing about every
other local account and service on the box being able to read it. Any run
that touches or notices that file checks the mode and narrows it back if it
has drifted — that's a permission taken away from nobody who should have
it, and it isn't a stop-and-ask.

Rotating or revoking a credential is stop-and-ask by default, per
[`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list. Any deviation
this owner agreed to is recorded in the deployment conventions doc at
`CONVENTIONS_DOC_PATH` in `.env`; if that variable is unset, or the doc is
silent, the default applies.
