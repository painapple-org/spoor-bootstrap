# Harness verification

This repo calls itself harness-agnostic. This file is the one home for how
much of that has actually been *checked*, against which harness, by doing
what — and for the harness-specific setup a deployment needs that nothing
in [`skills/`](../skills/README.md) is allowed to carry, per that
directory's "What belongs in a SKILL here".

Two things this file is deliberately not. It is not a compatibility
promise: a harness absent from the table below is untested, not
unsupported. And it is not a place to record what a harness *ought* to do
— every row is something that was run, with the command that ran it, so
the next reader can re-run it rather than trust it.

## What has been verified

| Harness | Instructions loaded | Skills discovered | Skills invocable | Full first-boot flow |
|---|---|---|---|---|
| Claude Code | yes | yes | yes | yes — every dry run of `STARTUP.md` so far |
| OpenCode | yes | yes | yes | partial, see below |
| Codex CLI | not run | not run | not run | not run |

"Instructions loaded" means [`AGENTS.md`](../AGENTS.md)'s content reaches
the model's system prompt. "Skills discovered" means all of
[`skills/`](../skills/README.md) is enumerated and advertised to the
model. "Skills invocable" means the harness can pull a whole `SKILL.md`'s
content in on demand.

### OpenCode

Verified 2026-09-04, against the version reported by `opencode --version`
at the time (1.18.28), installed from that release's
`opencode-linux-x64.tar.gz` on a box with no Node.js — which matters,
because [`install.sh`](../install.sh) doesn't install Node and an adopter
following it lands on exactly that box.

What was checked, and how:

- **All of `skills/` is discovered.** `opencode debug skill` enumerates
  every skill directory, reached through the symlinks described in
  [`skills/README.md`](../skills/README.md).
- **`AGENTS.md` reaches the system prompt, in full.** Checked by pointing
  OpenCode at a stand-in model server that records the request bodies it
  receives, then searching the assembled system prompt for distinctive
  strings from `AGENTS.md` — its own opening description of itself, its
  stop-and-ask list, its self-provisioning section. All present. The same
  capture shows every skill's name and description advertised to the
  model.
- **Skills are invocable.** OpenCode's `skill` tool was driven against
  two of the larger skills in this repo and returned each `SKILL.md`'s
  complete content.
- **`STARTUP.md`'s `.env` mechanics work.** The shell commands its
  `.env` step calls for — copying `.env.example`, `chmod 600`, and
  checking the resulting mode — ran through OpenCode's own shell tool
  and produced a correctly-moded `.env`.

Two things broke, both permission defaults rather than anything in this
repo's content. They are covered in "Harness setup a deployment needs"
below, because a deployment has to act on them.

What was *not* verified: no run used a real model. There were no
credentials for any provider on the box, and OpenCode's own bundled
zero-config model answered with a rate-limit error, so the agent loop was
driven by a scripted stand-in model server instead. That exercises the
harness's real plumbing — instruction assembly, tool schemas, the
permission engine, tool execution — and none of the model's judgement. So
"OpenCode can run this repo's first-boot flow" is not what was
established. What was established is narrower and still worth having:
nothing in the wiring stops it.

### Codex CLI

Not run. It ships a prebuilt Linux binary, so the no-Node.js box
`install.sh` produces is not the obstacle; the obstacle was having no
credentials for it.

One thing was changed on its behalf anyway, from its own published
documentation rather than from a run: Codex discovers skills under
`.agents/skills`, and does not read `.claude/skills`. Before that was
noticed this repo shipped no such path, so every skill here was invisible
to a harness the README names as supported. `.agents/skills` is now
committed alongside the other two, per
[`skills/README.md`](../skills/README.md). It is verified to the extent
that OpenCode discovers all of `skills/` through that path alone — but
nobody has watched Codex itself do it, and until someone has, this row of
the table stays "not run".

## Harness setup a deployment needs

A harness's own permission defaults are part of a deployment's setup, and
they are the owner's to change, not the agent's:
[`AGENTS.md`](../AGENTS.md) puts loosening a harness permission setting on
the stop-and-ask list, and an agent that cannot read `.env` cannot
authorize itself to. So this is a step before or during first boot, done
by the person who owns the box.

Under OpenCode, two of its defaults stop this repo's flow, and both were
observed as hard failures rather than reasoned about: in a
non-interactive run the harness auto-rejects the call, and the tool
returns an error to the agent.

- **Reading `.env` is gated.** OpenCode ships an `ask` rule on `.env`
  files (`.env.example` is exempt). Every skill in this repo resolves its
  configuration out of `.env`, so this is not a corner case.
- **Reading anything outside the checkout is gated.** OpenCode treats any
  path outside the project directory as needing approval.
  `PRODUCT_REPO_PATH` normally points outside this checkout — that is the
  whole shape of the thing — so this blocks the deployment's actual work,
  not just its setup.

Both are fixed by project-level OpenCode config, which was verified by
re-running the same two rejected reads with it in place and watching them
succeed:

```json
{
  "permission": {
    "read": { "*.env": "allow" },
    "external_directory": { "<the absolute PRODUCT_REPO_PATH>/*": "allow" }
  }
}
```

Grant the second one the specific path, not `*`. The point of the default
is that a stray absolute path outside the deployment's own directories
gets noticed, and that is worth keeping.

## A warning you should expect, and not fix

When two harness-native skill paths both resolve — and they always do,
since this repo commits all of them — OpenCode logs a
`duplicate skill name` warning per skill on startup. It scans more than
its own path, finds the same `SKILL.md` twice, and says so.

This is cosmetic, and it was checked rather than assumed: every skill is
still discovered, and its content still reaches the model, with the
warnings present. Deleting one of the symlinks does silence them, and is
the wrong trade — it would leave this repo's skills reachable only
through some *other* harness's directory name, which is the harness
coupling the symlinks exist to avoid. Each path stays because a harness
that reads only that path needs it.

## Adding a harness to the table

Run it, don't reason about it. The two mechanisms worth checking directly,
because they are where a harness differs and both fail silently, are
whether `AGENTS.md` reaches the system prompt and whether `skills/` is
discovered. Both are observable without a model: a harness's own debug
output, or a stand-in model server that records the request bodies the
harness sends it.

Then add a row, and say which parts you ran and which you didn't.
[`CONTRIBUTING.md`](../CONTRIBUTING.md) treats harness support as
welcome; a row here honestly marked half-verified is worth more than a
confident one.
