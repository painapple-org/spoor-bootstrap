# templates/

Runnable starting points: real code a specializing agent copies out and
adapts, rather than prose describing what to build.

This directory exists because of a specific failure. A SKILL is instructions
an agent reads, not a library it imports —
[`skills/README.md`](../skills/README.md)'s "What belongs in a SKILL here" is
the home for that boundary, and it rules out putting an app in there. But for
some things a description is genuinely not enough: an agent handed nothing but
guidance rebuilds the same scaffold from a blank page on every deployment, and
gets a slightly different, slightly worse one each time. Where the scaffold is
the same regardless of the business, it belongs here once.

## What belongs here, and what doesn't

A template here is:

- **Real, running code** — it builds, it starts, and it ships its own script
  that proves both. A template nobody has executed is prose with a file
  extension.
- **Genuinely business-agnostic**, so the specialization step is filling in
  paths and replacing example content, not deleting somebody else's product.
- **Owned by exactly one SKILL**, which is the home for whether to use it at
  all and what makes a good version of the thing. The template's own README is
  the home for how to drive it, and neither restates the other.

It is not the place for anything a SKILL can say in a paragraph, and it is not
a snippet library. Each entry is a whole working thing or it doesn't belong.

## Current templates

This list is the one enumeration of what exists here.

- [`internal-dashboard/`](./internal-dashboard/README.md) — a mesh-only
  internal operations dashboard: three pages reading live disk, container and
  git state, a Dockerfile, a compose file pairing it with the mesh sidecar
  that is its only route in, and a verification script that asserts it serves
  rather than that it started. Owned by
  [`skills/internal-dashboard`](../skills/internal-dashboard/SKILL.md).
