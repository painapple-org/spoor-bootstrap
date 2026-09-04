# templates/internal-dashboard

A runnable starter dashboard. Copy it out of this repo, point it at this
deployment's real paths, rename the pages to this deployment's real questions,
and it is an internal ops dashboard — reachable only over a private mesh, with
every number on it measured rather than made up.

It is a **starting point, not a product**. The pages that ship with it all
read genuinely live state, so a fresh copy shows something true on the first
run instead of placeholder panels. They are there to be replaced.

[`skills/internal-dashboard/SKILL.md`](../../skills/internal-dashboard/SKILL.md)
is the home for *whether to build one at all*, what makes a page worth having,
and the honesty and verification rules this scaffold implements. Read it
first; this file is only how to drive the scaffold.

## What's in it

| Path | What it is |
|---|---|
| `streamlit_app.py` | Entrypoint and the page list. |
| `dashboard/config.py` | Every setting, read from `DASHBOARD_*` environment variables. |
| `dashboard/hostinfo.py` | The live readings: disk, container runtime, `git log`. |
| `dashboard/ui.py` | `source_note` and `unavailable` — the two things every page must be able to say. |
| `app_pages/` | One file per page. Layout only; readings come from `dashboard/`. |
| `Dockerfile` | Python + uv, non-root, `git` installed because a page shells out to it. |
| `docker-compose.yml` | The app with no published port, plus the mesh sidecar that is the only route in. |
| `tailscale/serve.json` | The sidecar's proxy config. |
| `.env.example` | Every variable the compose file reads, with how to find each value. |
| `verify.sh` | Proves it serves. Build, health, app shell, then every page headlessly. |
| `exercise_pages.py` | The per-page headless check `verify.sh` step 4 runs. Not in the runtime image. |

The dependency list is deliberately tiny and lives in
[`pyproject.toml`](./pyproject.toml) — read it there. Everything else this app
does — the container runtime API over its unix socket, disk usage, git history
— is stdlib, so there is very little to keep patched and very little to read
before changing it.

## The starter pages

Each one is a real measurement, and each one is a worked example of a
different failure mode you will hit when you write your own:

- **Overview** — disk, container counts, commits in the last 7 days. The
  example of *a small number of large numbers, each with its source named
  underneath*.
- **Containers** — every running container, straight off the runtime's API
  over the read-only socket. The example of *distinguishing an absence from a
  failure*: a socket that isn't mounted, a permission error, and "genuinely
  nothing running" are three visibly different outcomes here rather than one
  empty table.
- **Shipping** — `git log` across every mounted checkout, per-day chart and a
  filterable table. The example of *one unreadable input not blanking the
  whole page, and not vanishing from it either*.

## Run it

```sh
./verify.sh
```

That is the whole first step, and it needs no configuration: it discovers the
enclosing git checkout and the host's container-runtime socket, builds the
image, and asserts on all four things listed in its own header. It publishes
no host port at any point.

To iterate on a page without Docker in the loop:

```sh
uv sync
DASHBOARD_REPO_PATHS=/path/to/a/checkout uv run streamlit run streamlit_app.py
```

## Specialize it

In this order, because each step makes the next one obvious.

1. **Copy the directory out of this repo** into its own git repo or its own
   directory next to the product, per the standalone-project rule in
   [`skills/internal-dashboard/SKILL.md`](../../skills/internal-dashboard/SKILL.md).
   It does not belong inside the product's repo, container set, or deploy
   pipeline. **Write where it landed into `INTERNAL_DASHBOARD_PATH` in the
   deployment's `.env` as part of this step** — that variable is the only
   record of where this project lives, and `spoor-doctor` reads it to check
   the location is still true. Note it is the deployment's own `.env`, not
   the one you copy in the next step: that one is this stack's, and every
   key in it is `DASHBOARD_*`.
2. **`cp .env.example .env` and fill it in.** Every variable has a comment
   saying where to get its value. `DASHBOARD_NAME` is the one that matters
   most: it becomes the container name, the mesh hostname, and the URL the
   owner types, so it carries this deployment's own service prefix.
3. **`uv lock`, commit the lockfile, and switch the `uv sync` in the
   `Dockerfile` to `uv sync --frozen --no-dev`.** The template ships no
   lockfile on purpose — versions resolved on the day it was written are stale
   state, not a starting point — but your copy wants one, so a rebuild can't
   pick up a different dependency tree. That lockfile is also what makes
   dependency-freshness tracking worth turning on: point your own repo's
   Dependabot config at this directory once it exists. Upstream deliberately
   does not track it, for reasons
   [`.github/dependabot.yml`](../../.github/dependabot.yml) records.
4. **Add a read-only bind mount to `docker-compose.yml` for every path in
   `DASHBOARD_REPO_PATHS`**, at the same path inside the container as on the
   host, so what a page prints as its source is a path that means something on
   the host too. Scope the mounts to individual directories rather than a home
   directory, so keys and credentials living nearby stay out of the container.
5. **Replace the pages.** Write the owner's actual questions, delete the
   starter pages that don't answer one of them, and keep using `source_note`
   and `unavailable` on every panel. A page showing a number with no source
   and no failure path is the one that eventually costs the whole surface its
   credibility.
6. **Run `./verify.sh` again**, and add each new page to `PAGES` in
   `exercise_pages.py` as you write it.
7. **Bring up the mesh sidecar** once the owner has provisioned an auth key,
   per
   [`skills/private-networking/SKILL.md`](../../skills/private-networking/SKILL.md).
   That is a separate verification from `verify.sh`, and it gets reported
   separately.

## Two things about the compose file worth knowing before you edit it

- **The compose *service* names stay `dashboard` and `dashboard-mesh`.**
  `DASHBOARD_NAME` renames the container and the mesh hostname, which are what
  a human sees, but `tailscale/serve.json` proxies to `http://dashboard:8501`
  by compose service name over the compose network. Rename the service and you
  have to rename it there too.
- **`${TS_CERT_DOMAIN}` in `tailscale/serve.json` is not a shell variable and
  is not something to fill in.** The sidecar image substitutes the node's own
  certificate domain into it at startup, which is what keeps this file free of
  a hardcoded tailnet name.

Why the compose file is shaped the way it is — no published port, a sidecar
joining the mesh as its own node with its own state volume, userspace mode,
the auth key living in this stack's own `.env` — is
[`skills/private-networking/SKILL.md`](../../skills/private-networking/SKILL.md)'s,
and is not restated here or in the compose file's own comments.
