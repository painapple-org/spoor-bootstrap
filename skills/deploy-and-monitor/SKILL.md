---
name: deploy-and-monitor
description: How a merged change actually reaches the running product, how it gets rolled back, whether the data is backed up and whether a restore has ever been verified, and how this agent instance knows the product is healthy. Read before merging something that has to deploy, before touching the running deployment, before touching a backup or a dump, or when investigating a failure. Ships as a stub — the environments, deploy mechanism, backups and health signals are per-deployment.
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
  attended one into production is the common pair.
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
  isn't.
- **How the data gets recovered, which is a different procedure.** See the
  backup section below. Conflating the two is how a bad hour becomes a bad
  week: rolling back a release is cheap and reversible, restoring a
  database is neither.

Two things that are true regardless of mechanism:

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
  guardrails" list, which is stop-and-ask for destroying data, deleting
  backups or volumes, and anything with no concrete rollback.
- **Where an alert goes.** One destination, per
  [`skills/comms-channel`](../comms-channel/SKILL.md).

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
