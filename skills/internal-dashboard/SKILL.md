---
name: internal-dashboard
description: How to build an internal operations dashboard — a small standalone app, separate from the product, that puts this deployment's own real state on one page for the owner and the agent. Ships with a runnable scaffold in templates/internal-dashboard/ to copy and specialize rather than a shape to rebuild from scratch. Covers when one is worth building at all, the standalone-project shape, the service-naming prefix convention, the rule that a page shows real state or says out loud that it doesn't, and how to verify one actually serves. Read when the owner asks for a dashboard, a status page, or somewhere to see what this instance is doing. Ships as a stub for what the pages actually show.
---

# internal-dashboard

## Status: STUB — needs specialization

The scaffold and the rules below are real and generic: a running starter
app, a standalone-project shape, a naming convention, an honesty rule, a
verification script. What cannot exist until a deployment is configured is
**which pages are worth building** — and whether this deployment wants a
dashboard at all. Those are `TODO(specialize)` markers, per
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

## Start from the scaffold, not from a blank page

There is a real, running starter dashboard in this repo:
[`templates/internal-dashboard/`](../../templates/internal-dashboard/README.md).
Copy that directory and specialize it. Do not design one from this file's
prose — every deployment that does gets a slightly different, slightly
worse version of the same scaffold, and the parts that are identical
everywhere (the container shape, the no-published-port compose file, the
provenance and failure-reporting helpers, the verification script) are
already written and already verified there.

What it gives you on the first run, with no configuration: a handful of
pages, each reading something genuinely live off the host — the filesystem,
the container runtime, git history. Real readings, so you are editing
something that works rather than filling in placeholders. Its entrypoint is
the one home for which pages those are; go and look rather than working
from a list copied into here, since replacing them is the first thing you
are meant to do.

That directory's own README is the home for how to drive it — what each
file is, the ordered specialization steps, how to run it locally. **This
file stays the home for the judgement**: whether to build one, what makes a
page worth having, and the honesty rules the scaffold implements. Read this
one for the why, that one for the how, and don't copy either into the
other.

The scaffold is a starting point, not a constraint. Its pages exist to be
replaced, and its stack is a default rather than a requirement — see "Its
stack is not the product's stack" below.

## What this covers, and what it doesn't

This SKILL owns **the dashboard as an artifact**: whether to build one, how
to structure the project, what to name it, and how to tell whether it
works. It owns *what it serves*.

Two neighbours own the rest of it, and this file deliberately restates
neither:

- **How the owner reaches it privately** is
  [`skills/private-networking`](../private-networking/SKILL.md)'s, entirely.
  A dashboard is exactly the case that file opens with, and its
  "Exposing one containerized service, privately" section is the one home
  for the sidecar pattern, the no-published-port rule, the userspace-mode
  detail, and the owner/agent split on auth keys and mesh membership. Go
  and read it before exposing anything; don't re-derive an exposure plan
  here, and don't copy its steps into a dashboard's own docs.
- **The signals it displays** are
  [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s. Which
  health signals exist, which this agent can even reach, how a live one is
  told from an abandoned one, and where an alert goes all live there. A
  dashboard is a *surface* over those signals; it does not get to redefine
  them.

The signal/surface split is worth holding onto because the two fail
differently. A missing signal is a blind spot. A dashboard nobody opens is
merely unused — and a dashboard that quietly stopped refreshing is worse
than either, because it looks like coverage while being none.

## Do not build one speculatively

A dashboard is a satisfying thing to build and a common way to spend a day
producing something the owner never opens. Build one when there is a real
question that is currently answered by logging into a box and running three
commands, and the owner has said they want to stop doing that.

[`skills/work-pipeline`](../work-pipeline/SKILL.md)'s "Proactive work"
section states the general form of this rule — an unused thing running on a
schedule is worse than no thing — and it applies here with full force.

`TODO(specialize)`: record whether this deployment wants an internal
dashboard at all, and the specific questions it exists to answer. If the
answer is no, say so and why; "no internal dashboard, the owner reads the
comms channel and that is enough" is a real, complete answer. Do not build
one to have built one.

## It is a separate project, not part of the product

An operations dashboard is the agent's own tooling. It is not a feature of
the product, and it does not belong inside the product's repo, its
container set, or its deploy pipeline. Keeping it separate buys three
things: it can't break the product when it breaks, its dependency tree
stays out of the product's lockfile, and its access to host internals never
becomes reachable from the product's public surface.

Concretely, the shape that works — and the shape the scaffold above already
has, so copying it out rather than adding it to something is the whole of
this step:

- **Its own directory, its own dependency lockfile, its own git repo or
  subdirectory** — initialized as a standalone project, not added to an
  existing one. **Record where you put it in `INTERNAL_DASHBOARD_PATH` in
  `.env`, in the same change that creates it.** That variable is this
  project's one home; without it the deployment has two things with their
  own history on disk and a name for only one of them, and a later session
  looking for the dashboard has nothing to resolve. Its own comment in
  `.env.example` is the home for what a blank there means and for why the
  key isn't `DASHBOARD_*`.
- **Its own self-contained compose file**, describing only the dashboard
  and the sidecar that exposes it. Never edit the product's compose file to
  add a dashboard service to it.
- **Read-only access to everything it reads.** Mount the directories it
  needs read-only, scoped to the specific paths it reads rather than a
  whole home directory, so credentials and keys that happen to live nearby
  stay out of the container. If it reads a container runtime socket to list
  running services, that mount is read-only too.
- **One writable location, if it writes at all**, on its own volume rather
  than inside a read-only mount. Container runtimes typically stamp a fresh
  volume with the ownership the image has on that path, so a container
  running as a non-root user needs that ownership set at build time or its
  first write fails.

### Its stack is not the product's stack

[`skills/product-tech-stack`](../product-tech-stack/SKILL.md) mandates a
specific stack, and it deliberately does not apply here. That requirement
is scoped to a product built for a **non-technical end-user**, for reasons
that file owns. An internal dashboard's entire audience is the owner and
this agent, both of whom are technical enough to read whatever it's written
in — so what matters is getting a useful page up fastest, not conforming to
the product's stack.

**The scaffold's stack is the default answer, and it is already recorded.**
It is a Python dashboard framework with two dependencies, and its stack is
declared in the one place that owns it:
[`templates/internal-dashboard/pyproject.toml`](../../templates/internal-dashboard/pyproject.toml).
Read it there rather than from a list copied into this file. Taking the
default costs one decision and zero writing, which is the point of it being
a default.

Deviating is allowed and occasionally right — a deployment whose owner
already runs a metrics stack with dashboards in it should put the pages
there instead of standing up a second surface. What is not allowed is
deviating silently: a stack chosen on merits gets recorded in this
deployment's conventions doc at `CONVENTIONS_DOC_PATH` in `.env`, with why,
because a later session that finds an undocumented choice tends to
relitigate it.

Do not read this as licence to be exotic. The dashboard still gets
maintained by whoever inherits it.

### If the framework ships its own agent skill, install it

Some frameworks now ship a skill document describing how to build well in
them, and expose a command that symlinks it into the harness skill
directories. Where that exists, run it: it is first-party guidance for the
exact version installed, which beats a model's recollection of an older
API.

This is one specific tool's convention rather than something universal —
most frameworks have nothing of the kind, and its absence is not a reason
to pick a different one. Two things to know when it does exist:

- **The installed files are usually symlinks into the virtual environment**,
  so they are environment-specific and belong in the project's ignore file,
  not in the repo. The install command generally prints the exact ignore
  lines to add; use those rather than writing your own.
- **Reinstalling or re-syncing dependencies can break the symlink or drop
  the command's own entry point.** Re-run the install after a fresh
  dependency sync, and check the link still resolves.

`TODO(specialize)`: record whether the chosen stack ships such a skill, the
command that installs it, and the ignore lines it asks for. If it doesn't,
say so — that is a fact about the stack, not an omission.

## Name every service with this deployment's own prefix

An agent-owned service, its container, and the hostname it answers on all
carry the same prefix, and it is the same prefix for every service this
agent owns. On a host that also runs the product, a bare `dashboard` or
`db` says nothing about who owns it or what may restart it; a prefixed name
answers both at a glance, and makes "everything this agent owns" a listable
set rather than institutional memory.

Apply it to all three — service name, container name, network hostname —
not just the one that happens to be visible. They drift apart otherwise,
and the hostname is the one people type.

The scaffold reduces this to one value in its own `.env`, applied to all
three from there, so the drift this rule guards against isn't possible in a
copy of it. Its `.env.example` names the variable.

`TODO(specialize)`: record this deployment's prefix and where it applies.
It is usually the agent's own name.

## What the pages actually show

The one rule that matters more than the page list: **a page shows real
state, or it says out loud that it doesn't.** Never generate plausible
stand-in data and render it as though it were measured. A dashboard's
entire value is that its numbers are true, and a single fabricated panel
costs the whole surface its credibility — permanently, because a reader who
has been fooled once has no way to tell which panel to trust next time. A
page with a prototype section labelled as a prototype is honest and useful.
An unlabelled one is a liability.

Two related habits, both cheap:

- **Show the reader what a number was derived from**, so a wrong number is
  debuggable rather than merely wrong: the path read, the command run, the
  time window.
- **Distinguish "this is absent" from "this could not be checked."** A
  check the dashboard could not perform — a path outside what the container
  can see, an API it has no token for — must not be reported as a negative
  finding. Collapsing the two produces a confidently wrong answer, which is
  the one output worse than an admitted gap. Note that this bites hardest
  in exactly the setup this file recommends: a container sees a few
  read-only mounts, not the host, so anything checking whether a referenced
  file still exists has to know which roots it can actually see.

**The scaffold gives both habits a function to call**, so a page gets them
by using the helpers rather than by remembering the rules: one that prints
what a panel's numbers were derived from, one that renders a reading that
could not be taken without implying a result. Their module docstring is the
home for what each is for. Keep calling them on every panel you add — a
page showing a number with no source and no failure path is the one that
eventually costs the whole surface its credibility, and it looks identical
to a good one until then.

Its starter pages are also each a worked example of one of these
failure modes surviving contact with a container, which is why they read
live state rather than a fixture: an absence told apart from a failure, one
unreadable input not blanking a whole page, a panel that names its own
source. Read them before writing your own, and delete the ones that don't
answer a real question here.

`TODO(specialize)`: record the pages this deployment's dashboard has and
the real source behind each one. Derive them from the owner's actual
questions gathered above, not from this list. Candidates that tend to be
genuinely useful, given they read something real:

- **What is running right now** — services, health status, uptime, disk.
- **What the agent has been doing** — commit or deploy history across the
  repos it works in, which is a real answer to "was anything shipped this
  week" that nothing else on the host gives in one view.
- **What the agent knows** — a browsable view of its own accumulated notes
  or memory, if this deployment keeps any.
- **What has gone stale** — a maintenance view flagging content whose
  timestamps are old or whose references no longer resolve. Cheap to build
  and the kind of thing nobody does by hand.
- **Work-item state**, read through
  [`skills/work-tracker`](../work-tracker/SKILL.md)'s operation contract
  rather than by querying a tracker's API directly from a page.

Scheduling anything the dashboard displays — a periodic refresh, a nightly
recomputation — is out of a SKILL's scope, per
[`skills/README.md`](../README.md). Point at the host schedule config.

## Verify it actually serves, not that it started

A started container is not a working dashboard. Before reporting one as
live:

- **Make a real request against it** and assert on something in the
  response, not only on the status code. A healthy-looking shell page
  proves the process is up, which for a client-rendered app says nothing
  about whether any page renders.
- **Exercise each page**, in the container, against the paths it will
  actually read at runtime. A page that works from a checkout and fails in
  the container is the normal outcome, not an unlikely one — the mounts are
  narrower and the user is different.
- **Write once, if it writes**, and read it back, so a volume whose
  ownership is wrong fails now rather than the first time the owner uses
  the page.

**The scaffold ships this as a script**, so on the default stack there is
nothing to write: `verify.sh` in
[`templates/internal-dashboard/`](../../templates/internal-dashboard/README.md)
runs the checks above and fails on each. Its own header is the home for
what it asserts and in what order. Run it before reporting a dashboard as
live, and again after any change to a page — and add each page you write to
the list it exercises, or the per-page check silently stops covering the
pages that matter.

Two properties of it worth carrying to any other stack: it publishes no
host port to do the checking (a verification step that publishes one is
exactly what the no-published-port rule exists to prevent, and it has a way
of surviving into production), and its per-page check runs the framework's
own headless harness inside the built image rather than requesting each URL
— because for a client-rendered app an HTTP request returns the same shell
whether the page rendered or blew up on its first line.

**Report the exposure honestly and separately from the app.** The two fail
independently: the app can be running and verified while the private
network side is blocked on something only the owner can provision, which
[`skills/private-networking`](../private-networking/SKILL.md)'s owner/agent
split makes a routine outcome rather than an unlucky one. When that
happens, say the app is up, say the sidecar is defined but not started, and
say what the owner has to provide. Never report a private URL you have not
actually loaded.

`TODO(specialize)`: only if this deployment's dashboard is **not** on the
scaffold's stack — record the concrete verification commands for the stack
it is on, and whether that framework ships a headless test harness worth
using for the per-page check. On the default stack, delete this marker: the
answer is the script above, and restating what it does here would be a copy
that goes stale the first time it changes.
