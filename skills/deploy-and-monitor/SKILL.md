---
name: deploy-and-monitor
description: How a merged change actually reaches the running product, and how this agent instance knows the product is healthy. Read before merging something that has to deploy, before touching the running deployment, or when investigating a failure. Ships as a stub — the deploy mechanism and health signals are per-deployment.
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

- **What triggers a deploy.** A push to the default branch via CI, a
  self-hosted runner, a webhook, a scheduled pull, or a command run by
  hand. Name the actual mechanism and where its config lives.
- **Which command deploys**, and from where. If a script owns this, name
  the script and let it be the one home for the procedure — don't restate
  its steps here.
- **Whose job deploying is.** If an automated pipeline handles it, a
  merging session's job ends at the merge: it must not also pull and deploy
  against the primary checkout, because that duplicates the pipeline and
  can race it on the same working tree.
- **How to roll back.** This is the safety net the whole autonomy model
  rests on, so it has to be a known, tested procedure, not an improvisation
  discovered during an outage.

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
  check it.

## Monitoring

`TODO(specialize)` — record:

- **The health signals that exist.** Container health checks, an HTTP
  health endpoint, disk/memory thresholds, log-based error detection,
  external uptime checks. List the ones this deployment actually has; don't
  list aspirational ones.
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

Rotating or revoking a credential is stop-and-ask by default, per
[`AGENTS.md`](../../AGENTS.md)'s "Default guardrails" list. Any deviation
this owner agreed to is recorded in the deployment conventions doc at
`CONVENTIONS_DOC_PATH` in `.env`; if that variable is unset, or the doc is
silent, the default applies.
