---
name: internal-dashboard
description: How to build and privately expose an internal operations dashboard — a small standalone app, separate from the product, that puts this deployment's own real state on one page for the owner and the agent. Covers the standalone-project shape, private-by-network-identity exposure via a VPN sidecar, and the service-naming prefix convention. Read when the owner asks for a dashboard, a status page, or somewhere to see what this instance is doing. Ships as a stub for the stack choice, the VPN, and what the pages actually show.
---

# internal-dashboard

## Status: STUB — needs specialization

The shape below is real and generic: a standalone project, a private
exposure path, a naming convention. What cannot exist until a deployment
is configured is the stack, the VPN, the hostname, and — most of all —
which pages are worth building. Those are `TODO(specialize)` markers, per
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

## What this covers, and what it doesn't

This SKILL owns **the dashboard as an artifact**: how to structure the
project, how to expose it to exactly the right people, and what to name it.

It does **not** own the signals it displays. Which health signals exist,
which of them this agent can even reach, how a live signal is told from an
abandoned one, and where an alert goes are all
[`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md)'s, and that
file is their one home. A dashboard is a *surface* over those signals; it
does not get to redefine them, and it must not restate them either.

The distinction is worth holding onto because the two fail differently. A
missing signal is a blind spot. A dashboard nobody opens is merely unused —
and a dashboard that quietly stopped refreshing is worse than either,
because it looks like coverage. Which is exactly the "green dashboard,
monitor nobody has fed in months" problem `deploy-and-monitor`'s Monitoring
section already names.

## Do not build one speculatively

A dashboard is a satisfying thing to build and a common way to spend a day
producing something the owner never opens. Build one when there is a real
question that is currently answered by SSHing in and running three
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

Concretely, the shape that works:

- **Its own directory, its own dependency lockfile, its own git repo or
  subdirectory** — initialized as a standalone project, not added to an
  existing one.
- **Its own self-contained compose file**, describing only the dashboard
  and its exposure sidecar. Never edit the product's compose file to add a
  dashboard service to it.
- **Read-only access to everything it reads.** Mount the directories it
  needs read-only, scoped to the specific paths it reads rather than a
  whole home directory, so credentials and SSH keys that happen to live
  nearby stay out of the container. If it reads a container runtime socket
  to list running services, that mount is read-only too.
- **One writable location, if it writes at all**, on its own volume rather
  than inside a read-only mount.

### Its stack is not the product's stack

[`skills/product-tech-stack`](../product-tech-stack/SKILL.md) mandates a
specific stack, and it deliberately does not apply here. That requirement
is scoped to a product built for a **non-technical end-user**, for reasons
that file owns. An internal dashboard's entire audience is the owner and
this agent, both of whom are technical enough to read whatever it's written
in — so pick the stack that gets a useful page up fastest, and record the
choice.

Do not read this as licence to be exotic. The dashboard still gets
maintained by whoever inherits it.

`TODO(specialize)`: record the stack chosen for this deployment's
dashboard, and where its project lives. A single-file Python dashboard
framework, a small server-rendered app, or a static page regenerated on a
schedule are all reasonable and materially different choices. Name the one
picked and why — a later session that finds an undocumented choice tends to
relitigate it.

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
  so they are environment-specific and belong in `.gitignore`, not in the
  repo. The install command generally prints the exact ignore lines to add;
  use those rather than writing your own.
- **Reinstalling or re-syncing dependencies can break the symlink or drop
  the command's own entry point.** Re-run the install after a fresh
  dependency sync, and check the link still resolves.

`TODO(specialize)`: record whether the chosen stack ships such a skill, the
command that installs it, and the ignore lines it asks for. If it doesn't,
say so — that is a fact about the stack, not an omission.

## Private by network identity, not by a login page

An internal dashboard shows host internals to exactly two audiences and has
no reason to be reachable by anyone else. The exposure pattern to reach
for:

- **A VPN or overlay-network sidecar** in the same compose file, joining the
  private network as its own node and proxying to the app over the compose
  network by service name.
- **No published host port on the app at all.** Not bound to localhost,
  not firewalled — simply absent. If the only route in is the sidecar, then
  a misconfigured firewall cannot expose the dashboard, because there is
  nothing on the host to expose.
- **Network identity as the only access control.** Being on the private
  network *is* the authorization. This is why the previous point is not
  optional: the app itself has no auth layer, so a published port would be
  an open door, and adding a login page instead would mean maintaining
  session handling and credentials for an audience of two.
- **TLS terminated by the sidecar**, which typically handles certificates
  for its own network hostname automatically.
- **A single-use join key, read from an environment variable**, kept in the
  deployment's own uncommitted env file. The node's state persists in a
  volume afterwards, so the key is needed only to bring a fresh node up.
  Never commit it, and never write the value into a SKILL, a compose file
  or a doc — the variable name is what gets documented, per
  [`skills/README.md`](../README.md).

The sidecar needs a real key to come up, and that key generally cannot be
minted from the host: it comes from the network provider's admin console or
an API token the host may not have. **When you cannot obtain one, build and
run everything else, leave the sidecar defined but unstarted, and say
plainly that it is unstarted and why.** Do not report a private URL that
does not resolve.

`TODO(specialize)`: record which private-network product this deployment
uses, the hostname the dashboard answers on, the env var holding the join
key, and where a new key is minted. If this deployment has no private
network, that is the blocker to put on the owner's shopping list — do not
substitute a public port with a password over it.

## Name every service with this deployment's own prefix

An agent-owned service, its container, and its private-network hostname all
carry the same prefix, and it is the same prefix for every service this
agent owns. On a host that also runs the product, a bare `dashboard` or
`db` says nothing about who owns it or what may restart it; a prefixed name
answers both at a glance, and makes "everything this agent owns" a listable
set rather than institutional memory.

Apply it to all three — service name, container name, network hostname —
not just the one that happens to be visible. They drift apart otherwise,
and the hostname is the one people type.

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
  the one output worse than an admitted gap.

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
  narrower and the uid is different.
- **Write once, if it writes**, and read it back, so a volume whose
  ownership is wrong fails now rather than the first time the owner uses
  the page.

`TODO(specialize)`: record the concrete verification commands for this
deployment's stack, and whether the framework ships a headless test harness
worth using for the per-page check.
