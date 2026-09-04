---
name: product-tech-stack
description: The required technology stack when the product being built is aimed at a non-technical end-user/client, and how to handle an inherited product repo whose stack doesn't match it. Read this before choosing any framework, language, or infra piece in that situation — it is the one place this decision is recorded.
---

# product-tech-stack

## When this applies

Use this SKILL whenever the product you (the agent) are building or
operating is aimed at a **non-technical end-user or client** — i.e. the
human who owns this deployment told you, during the first-boot interview
in [`AGENTS.md`](../../AGENTS.md), that the end product is for a
non-technical audience. That answer is recorded as `END_USER_TYPE` in
`.env` — read it rather than re-asking or guessing.

If the product is aimed at a technical end-user (developers, technical
teams, internal tooling for technically fluent users), this SKILL does not
apply — choose your stack on its merits for that case, and record what you
chose in the deployment conventions doc at `CONVENTIONS_DOC_PATH` in `.env`.
That's its home in that case; this file stays the home only for the
non-negotiable list below, so nothing chosen on merits gets written in here.

## The requirement

When this SKILL applies, use this stack. Do not substitute pieces of it,
and do not decide a different stack "because it's simpler for this
product" — the whole point of stating it once here is that it isn't
re-litigated per deployment:

- **FastAPI** — the backend web framework.
- **SQLModel** — the ORM / data-modeling layer, sitting on top of the
  database.
- **FastMCP** — for exposing any MCP-compatible tool interface the product
  needs.
- **Alembic** — database migrations.
- **PostgreSQL** — the database.
- **Next.js** — the frontend framework.
- **Pydantic** — data validation/schemas.
- **pydantic-settings** — configuration/settings management.
- **Docker** and **docker-compose** — containerization and local/deploy
  orchestration.
- **uv** — Python dependency and environment management.

## When the product repo already exists and doesn't match

Common case, and it has a settled answer — don't re-derive one per
deployment. The product this agent inherits is often a live codebase
somebody else built, in a stack that is not the one above. That is a
conflict between two real things, not a mistake to correct on the spot:

1. **The existing application keeps its stack, and gets maintained in it.**
   Do not start a migration, and do not write new code inside it in a
   second stack — a half-migrated app is worse for a non-technical owner
   than either whole one, and it is exactly what this SKILL exists to
   prevent. Working competently in the stack that's there beats working
   ideologically in the one that isn't.
2. **The requirement above governs genuinely new work** — a new service, a
   new app, a rewrite the owner actually asked for.
3. **The conflict gets recorded, not silently resolved in either
   direction.** Write it into this deployment's conventions doc at
   `CONVENTIONS_DOC_PATH` as an open conflict: which pieces already match,
   which don't, and the reading agreed with the owner. Recording it is what
   keeps a later session from "discovering" the mismatch and starting the
   rewrite nobody sanctioned, or from quietly treating this SKILL as
   inapplicable because the first thing it met disagreed with it.
4. **A migration is a conversation with a cost attached.** Raise it,
   with what it would buy and what it would cost, and let the owner decide.
   Starting one unasked is a stop-and-ask violation under
   [`AGENTS.md`](../../AGENTS.md)'s "anything you cannot describe a concrete
   rollback for", whatever this SKILL says about the target stack.

Overlap is normal and worth naming explicitly in that record — an inherited
app frequently already uses Postgres, Docker or uv. Those pieces aren't in
conflict, and saying which ones already match keeps the record from reading
as a bigger gap than it is.

## Why this exists as a single opinionated SKILL

A non-technical end-user or client has no ability to evaluate or recover
from an idiosyncratic technology choice if the agent operating their
product picks something obscure, and no ability to hire around it either.
This stack is boring on purpose: every piece is mainstream, well-
documented, and has a large enough ecosystem that a future maintainer (AI
or human) can get unstuck without depending on this SKILL's author.

This is the **one place** the *product's* stack is stated. If you find this
list duplicated elsewhere in this repo or in a deployment built from it,
that's drift — point back here instead of copying the list again.

One thing that is deliberately not drift: `README.md`'s "Hard
requirements" also names Docker and uv, and `install.sh` installs them.
Those are a different claim — the tooling the *agent* needs present on its
own host to operate at all, whatever the product turns out to be, and
required even when this SKILL doesn't apply. This SKILL is the only home
for what the product is built in; that section is the only home for what
the operator's box needs. The overlap between them is real, not a copy.

## What this SKILL does not cover

This SKILL states a stack requirement, nothing more. It does not include:
scheduling/deployment mechanics, a work-tracker choice, a comms-channel
choice, or an email provider — those remain separate, per-deployment
decisions covered elsewhere (`AGENTS.md`, `STARTUP.md`'s first-boot
interview, `skills/README.md`).
