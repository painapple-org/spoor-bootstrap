# templates/synthetic-check

A runnable synthetic check. Copy it out of this repo, replace the one example
flow with the product's own real user-facing flows, point it at the live
product, and schedule it — and it continuously re-proves that the flows a
business depends on still actually work, alerting only when one doesn't.

It ships with a **toy product to check**, so the thing can be run and watched
catching real breakage before it is ever pointed at anything that matters.
`./verify.sh` breaks that toy product ten different ways and asserts the check
notices each one. That is the whole reason this directory is code rather than a
paragraph: a synthetic check nobody has watched fail is indistinguishable from
one that always passes.

[`skills/synthetic-monitoring/SKILL.md`](../../skills/synthetic-monitoring/SKILL.md)
is the home for *which* flows deserve a check, what counts as proof of a side
effect, the production-data rules, and how often to run it. Read it first; this
file is only how to drive the scaffold.

## What's in it

| Path | What it is |
|---|---|
| `run_checks.py` | The runner: loads flows, runs each, reports, alerts, heartbeats. Stdlib only. |
| `flows/signup.py` | The one example flow, and the worked example of the four-part flow contract. |
| `example_alert_command.sh` | The shape of a `SYNTHETIC_ALERT_COMMAND`, and the one `verify.sh` asserts against. |
| `example_product/app.py` | A toy product with a signup flow, an evidence API, and injectable faults. |
| `verify.sh` | Ten cases proving the check catches each injected fault — and stays quiet when nothing is wrong. |

The runner's own configuration is every `SYNTHETIC_*` environment variable it
reads; `run_checks.py` is the one home for that list, and each is read where it
is used rather than being restated here.

## Run it

```sh
./verify.sh
```

That needs no configuration and no network: it stands up the toy product on a
loopback port, runs the checker against it, and asserts on the outcome of each
case. Its own header is the one home for what the ten cases are.

To watch a single run against the toy product by hand:

```sh
PRODUCT_STATE_DIR=/tmp/toy-product python3 example_product/app.py &
SYNTHETIC_TARGET_BASE_URL=http://127.0.0.1:8099 \
SYNTHETIC_EVIDENCE_TOKEN=toy-evidence-token \
	python3 run_checks.py
```

Add `PRODUCT_BREAK=side_effect` to the product's environment to watch the check
fail on a flow that answers 201 and stores nothing.

## The flow contract

One file per flow in `flows/`, each defining `NAME`, `trigger`, `prove`,
`cleanup` and optionally `MAX_SECONDS`. What each part is for, and why they are
separate, is in [`flows/signup.py`](./flows/signup.py)'s own header — it is the
template within the template, and it is meant to be copied.

The runner enforces two things about them that are easy to get wrong by hand: a
flow that cannot be imported fails the run rather than being skipped, and
`cleanup` runs even when `prove` failed.

## Specialize it

In this order, because each step makes the next one obvious.

1. **Copy the directory out of this repo**, into the deployment's own
   operational tooling — not into the product's repo, and not into its compose
   file. A check that ships and deploys with the product it watches goes down
   with it, and a broken deploy is exactly when it needs to be running.
2. **Delete `example_product/`, and delete `verify.sh`'s cases for it.** They
   are the proof that the runner works, not part of what you are running. What
   replaces them is the fault-injection test described in the SKILL's own
   section on it, run against the real product's staging environment.
3. **Write one flow, and only one, for the highest-value flow the product
   has** — the SKILL's flow-selection section is the home for how to pick it.
   Get that one honest, including its cleanup, before writing a second.
4. **Give the product what the flow needs to read its own side effect back.**
   This is usually the real work of adopting the pattern, and it is a change to
   the product: the evidence read in `example_product/app.py` and its purge
   endpoint are the shape, and the SKILL's evidence section is the home for
   what such an endpoint must and must not do.
5. **Point `SYNTHETIC_ALERT_COMMAND` at this deployment's real alert path**,
   replacing `example_alert_command.sh`, per that file's stated contract.
6. **Schedule it, and make its silence audible.** The cadence and the
   scheduling mechanism are the SKILL's and the host's respectively; the one
   thing that belongs here is that `SYNTHETIC_HEARTBEAT_URL` exists for the
   second half of it, because a check that has stopped running produces no
   failures at all.
