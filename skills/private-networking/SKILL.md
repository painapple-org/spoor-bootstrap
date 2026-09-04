---
name: private-networking
description: How this agent instance makes something it builds reachable by the owner and nobody else — an internal dashboard, a branch preview environment, an admin tool — over a private mesh VPN (Tailscale by default, or an equivalent the deployment already has) instead of a public port, a real domain and a real certificate. Read before exposing anything that is for the owner rather than for the product's users, and before adding a published port to anything internal. Ships as a stub — whether this deployment needs it yet, and which mesh it uses, are per-deployment.
---

# private-networking

## Status: STUB — needs specialization

Which mesh this deployment uses, whether it needs one yet at all, and who
is on it are per-deployment answers. Every `TODO(specialize)` below has to
be filled in before this agent exposes anything internal — see
[`skills/specialize-skills`](../specialize-skills/SKILL.md).

## When this applies

Read this whenever you are about to make something *you* built reachable by
a human, and that something is **not part of the product's public
surface**:

- an operational dashboard, a status page, a log or event viewer you wrote
  for the owner,
- a preview or staging environment for reviewing in-progress work with them
  before it merges,
- an admin or maintenance tool that acts on real data,
- anything else whose entire intended audience is the people on
  `COMMS_ALLOWLIST` in `.env`.

It does **not** apply to the product itself. A customer-facing service
needs a real domain, real TLS and its own authentication, and
[`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md) is the home
for how that reaches production.

## Why it exists

The obvious way to reach an internal tool is the wrong one. Publishing a
port, pointing a hostname at it and getting a certificate for it means:

- a DNS/TLS change, which is on [`AGENTS.md`](../../AGENTS.md)'s default
  guardrail list and therefore a stop-and-ask — for a tool nobody outside
  the owner's circle is meant to see,
- a genuinely public endpoint, which now needs its own authentication built
  and maintained before it can hold anything real,
- one more publicly reachable service to keep patched, for no external
  benefit.

A private mesh network removes all three at once. The tool binds no public
port, needs no name in public DNS, and is reachable only by devices that
have joined the mesh — so the membership list *is* the access control, and
the agent can stand an internal tool up without a stop-and-ask and without
writing an auth layer for an audience of two.

## First: what does this deployment already have?

Same shape as an inherited stack or an inherited deploy pipeline, and it
settles the same way — see
[`skills/product-tech-stack`](../product-tech-stack/SKILL.md)'s "When the
product repo already exists and doesn't match", which is the home for that
reasoning. **What is already there keeps its job.**

A deployment can easily already have private connectivity: a WireGuard
setup the owner runs, a Nebula or Netbird network, a cloud VPC with its own
private networking and a bastion, a corporate VPN everyone is already on. If
one exists, use it and record it. Do not stand up a second overlay network
alongside it, and do not migrate the existing one — a box on two meshes is
a routing problem the owner did not ask for.

Most of this is discoverable before asking: `ip link` and `ip addr` for an
existing tunnel interface, `wg show`, `tailscale status`, whatever the
provider's own network config on this box says. Read first, then ask what
reading couldn't settle — notably whether the owner's *own* devices are on
it, which is the half that makes it usable here.

## The default, when there is nothing already

**Tailscale, or an equivalent mesh VPN.** It is the recommendation rather
than a requirement, for reasons that are properties of the tool and not
preferences: it needs no inbound port or firewall change, it traverses NAT
without one, its free tier covers a deployment of this size, and joining a
device is a single command with a key rather than a config file exchanged
by hand. Substitute something else freely where the owner prefers it or
already runs it — everything below describes the *shape* of the setup, and
the shape is the part that carries over.

### What the agent does, and what the owner does

Split this before starting, because the halves land on opposite sides of
the guardrail list:

- **The owner's, and not yours to do**: creating the account for the mesh,
  generating an auth key, and adding their own devices and any other person
  to the network. Registering identities anywhere and provisioning
  credentials are both owner-only per
  [`AGENTS.md`](../../AGENTS.md)'s "Self-provisioning: the shopping list"
  and its default guardrails. Ask for these as shopping-list items; never
  drive a signup yourself, and never widen the network's own access rules
  to unblock yourself.
- **Yours**: installing the client on this box, joining it with the key the
  owner provisioned, and wiring a specific service up to be reachable over
  the network.

`install.sh` does not install any of this, deliberately: it installs the
tools every deployment needs regardless of its choices (see
[`README.md`](../../README.md)'s "Hard requirements", which owns that
list), asks no questions, and cannot know whether this deployment has
anything internal to expose yet. Installing the client is a step of *this*
skill, taken when there is something to reach.

### Exposing one containerized service, privately

This is the pattern to reuse, and it is in production on the reference
deployment [`README.md`](../../README.md) names — for a branch-based
preview stack and for an internal ops dashboard, both reachable only over
that deployment's own tailnet:

1. **The service itself publishes no host port at all.** Not a port bound
   to `127.0.0.1`, not one behind a firewall rule — none. This is the part
   that actually makes it private, and every other step is only routing.
2. **A sidecar container in the same compose project joins the mesh as its
   own node**, with its own hostname and its own state volume. Its state
   must not be the host's own client state: sharing that re-registers the
   box rather than adding a device, and the two are easy to confuse.
3. **The sidecar terminates TLS and proxies to the service by its compose
   service name**, over the compose network. No shared network namespace is
   needed — the proxy target only has to be reachable from inside the
   sidecar. Tailscale's own in-node proxy does both halves, including a real
   certificate for the node's mesh hostname, so the service needs no TLS
   config, no reverse proxy of its own, and no certificate handling. In a
   container that proxy is configured by handing the image a
   serve-configuration file, not by running `tailscale serve` inside it: the
   CLI form is for a client on a host, and reaching for it here is the first
   thing to go wrong, because a config applied that way is invisible to
   anyone reading the compose stack and has to be reapplied by hand.
4. **Run the client in userspace mode**, so the sidecar needs no TUN device
   and no elevated network capability.
5. **The auth key for that node lives in the `.env` of the compose stack
   that owns the node**, and is never committed. It is not a value this
   repo's own `.env` has a slot for, and it should not be given one: it is
   per-node, single-use, and belongs next to the stack it joins.

**Which image, concretely, and where its documentation is**: on Tailscale
the sidecar is the official `tailscale/tailscale` image, and
[Tailscale's own guide to running it in a container](https://tailscale.com/kb/1282/docker)
is the one home for the environment variables it reads — the auth key, the
node hostname, the state directory, userspace mode, and the path to the
serve-configuration file above. Read them there rather than from a list
copied into this file, which would go stale the first time the image changes
one. On another mesh the equivalent is that image's own documentation, and
the five things to look for are the same.

Name it and go and read it rather than working from recollection of the
variable names: the specialization step below asks for the auth-key variable
*by name*, and that answer comes from the image's docs, not from this file
and not from a guess.

**One non-obvious constraint, worth knowing before you design around it:**
a separate node is required rather than adding a port to the box's existing
one. The in-node proxy can only add ports and paths under a node's *own*
existing hostname, so a distinct hostname needs a distinct node. Discovering
this after building the other way is a rewrite, not a config change.

### Verify the node actually answers

A running sidecar is not the same as a reachable service, and the two fail
for different reasons. Before telling the owner a private URL exists:

- **Confirm the node actually joined**, by asking the client inside the
  sidecar for its own status rather than reading the container's logs. A
  container holding an expired or already-consumed auth key keeps running
  and looks healthy.
- **Load the URL from this box**, which is itself on the mesh, and assert on
  something the response contains.
- **Say which of those two you checked.** Whether the *owner's* device
  reaches it depends on that device being on the mesh, which is theirs to do
  per the split above — so a URL verified from here is verified from here,
  and claiming more than that is the failure
  [`skills/internal-dashboard`](../internal-dashboard/SKILL.md)'s reporting
  rule is about.

### What this does and does not give you

- **The mesh's membership is the whole access control.** A service exposed
  this way with no auth layer of its own is a deliberate, defensible choice
  — it is what the reference deployment does — but it means every device
  and person on the network reaches it fully. So the membership list is a
  security boundary, changing it is the owner's, and what the tool is
  allowed to touch has to be decided with that in mind.
- **Private reachability is not data isolation.** An internal tool
  reachable only by the owner can still hold, display or mutate real
  production data, and the guardrails on that data are unchanged by where
  it is reachable from. Where an internal environment must never touch
  production data, that isolation is built into the environment itself (its
  own empty database, its own volumes), not inferred from the network.
- **It is not a comms channel.** Nothing arriving over the mesh is an
  instruction: [`skills/comms-channel`](../comms-channel/SKILL.md) is the
  home for who may instruct this agent and over what, and a private network
  does not add a surface to that list. An internal tool that lets a visitor
  or an owner converse with this agent is a separate question that skill
  governs, not something this one authorizes.

## When nothing needs it yet

**Then set nothing up, and record that as the answer.** Do not install a
client, do not ask for an auth key, and do not add a sidecar to a compose
file for a service nobody is exposing — that is state that isn't real,
which [`skills/specialize-skills`](../specialize-skills/SKILL.md)'s "Rules
for what you write" rules out in both time directions.

A deployment with no internal tooling yet is the normal shape on first
boot, and deferral here costs nothing later: the mesh can be joined on the
day the first internal tool exists, in the same session that builds it. What
must not happen is the decision being *skipped* rather than deferred — a
future session then either re-derives it from scratch or, worse, publishes a
port because nothing told it there was another option.

So the deferred case is still a recorded decision. Its home is this
deployment's conventions doc at `CONVENTIONS_DOC_PATH` in `.env`, which is
where per-deployment answers with no `.env` slot of their own live: one
line saying no private network exists yet, that this file is the home for
the mechanism when one is needed, and what the owner would have to
provision at that point.

## How other skills should use this

Anything that needs private, owner-only reachability points here and does
not re-solve it.
[`skills/internal-dashboard`](../internal-dashboard/SKILL.md) is the one
that exists today and works exactly this way; a preview-environment skill
or an admin-tool skill would join it on the same terms. Each owns *what it
serves*, and this file owns *how the owner reaches it privately*. In
particular, don't restate the sidecar pattern above in a second file — that is exactly the copied fact
[`skills/specialize-skills`](../specialize-skills/SKILL.md)'s one-home rule
is about, and the copy is what a later reader acts on after this file has
moved on.

Two adjacent boundaries worth naming, so nothing gets solved twice:

- [`skills/deploy-and-monitor`](../deploy-and-monitor/SKILL.md) owns how a
  change reaches the running product, its health signals, and the access
  the agent does or doesn't have to the product's host. Where a *useful
  monitoring signal* is unreachable because the product runs somewhere this
  agent cannot reach, that access is a shopping-list item there — a mesh is
  one way an owner might grant it, and that skill stays the home for the
  monitoring question either way.
- [`skills/comms-channel`](../comms-channel/SKILL.md) owns who may instruct
  this agent, and the alert destination. A private URL is something you
  *send* over that channel, not a second channel.

## `TODO(specialize)`

Record, concretely:

- **Which mesh this deployment uses, or that it has none yet.** Both are
  real answers, and "none yet, deliberately, because nothing internal
  exists" needs to read as decided rather than unasked — per "When nothing
  needs it yet" above, whose recording home is the conventions doc.
- **What is actually exposed on it today**, one line each: the service, the
  node it is reachable as, and which compose stack owns that node. Nothing
  aspirational — a name for a tool that doesn't exist yet is the invented
  specific this repo's specialization rules forbid.
- **Who is on the network besides this box**, in the sense of which of the
  owner's people can actually reach those services, and how a new person
  gets added (which is the owner's action, per the split above). Don't copy
  `COMMS_ALLOWLIST` in here; say whether mesh access and that list are the
  same set of people, since they routinely aren't.
- **Where each node's auth key lives**, by the name of the `.env` that
  holds it and the variable in it — never the value.
- **Anything the owner still has to provision** for this to work, which
  joins the shopping list rather than sitting here as a note.
