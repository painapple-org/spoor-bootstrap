---
name: product-tech-stack
description: The required technology stack when the product being built is aimed at a non-technical end-user/client. Read this before choosing any framework, language, or infra piece in that situation — it is the one place this decision is recorded.
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
