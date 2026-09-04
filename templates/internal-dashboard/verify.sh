#!/usr/bin/env bash
#
# Prove this dashboard actually serves, rather than that its container started.
# Run it from a copy of this template, before telling the owner the dashboard
# is up, and again after any change to a page.
#
# Four assertions, in the order they fail most often:
#
#   1. the image builds,
#   2. the app answers its own health endpoint from inside the container,
#   3. a page request returns HTML that is actually this app's,
#   4. every page runs to completion headlessly, in the image, against real
#      readings - the enclosing git checkout and, where one exists, the host's
#      container-runtime socket.
#
# What it deliberately does not check is whether the mesh sidecar is up or
# whether the owner's device can reach the private URL. Those fail
# independently and are `skills/private-networking/SKILL.md`'s to verify - and
# the reporting rule in `skills/internal-dashboard/SKILL.md` is that the two
# get reported separately.
#
# No host port is published at any point, including here: the app is reached
# with `docker exec` from inside its own container. A verification step that
# publishes a port is the thing the whole no-published-port rule exists to
# prevent, and it has a way of surviving into production.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Scoped to this run so two of these in parallel, or a leftover from a crashed
# one, can't collide on a name.
tag="internal-dashboard-verify:$$"
container="internal-dashboard-verify-$$"

cleanup() {
	docker rm -f "$container" >/dev/null 2>&1 || true
	docker image rm -f "$tag" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Real inputs to point the pages at, discovered rather than configured, so this
# runs against a fresh copy of the template with nothing filled in yet. Each
# page that gets nothing renders its own "not configured" state, which is a
# real state and part of what is being verified.
run_args=(
	--env DASHBOARD_TITLE="Verification run"
	--env DASHBOARD_DISK_PATH=/
)

checkout="$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$checkout" ]]; then
	run_args+=(--volume "$checkout:/checkout:ro" --env DASHBOARD_REPO_PATHS=/checkout)
	echo "==> exercising the Shipping page against the checkout at $checkout"
else
	run_args+=(--env DASHBOARD_REPO_PATHS=)
	echo "==> no enclosing git checkout; the Shipping page will render its unconfigured state"
fi

socket=/var/run/docker.sock
if [[ -S "$socket" ]]; then
	run_args+=(--volume "$socket:$socket:ro" --env "DASHBOARD_DOCKER_SOCKET_PATH=$socket")
	echo "==> exercising the Containers page against $socket"
else
	run_args+=(--env DASHBOARD_DOCKER_SOCKET_PATH=)
	echo "==> no container-runtime socket; the Containers page will render its unconfigured state"
fi

echo "==> 1/4 building the image"
docker build --quiet --tag "$tag" . >/dev/null

echo "==> 2/4 starting the container and waiting for its health endpoint"
docker run --detach --name "$container" "${run_args[@]}" "$tag" >/dev/null

health="import urllib.request; assert urllib.request.urlopen('http://localhost:8501/_stcore/health').read() == b'ok'"
for _ in $(seq 1 60); do
	if docker exec "$container" python -c "$health" >/dev/null 2>&1; then
		break
	fi
	sleep 1
done

if ! docker exec "$container" python -c "$health" >/dev/null 2>&1; then
	echo "FAIL: health endpoint never returned ok. Container logs:" >&2
	docker logs "$container" >&2
	exit 1
fi
echo "    health endpoint returned ok"

echo "==> 3/4 asserting the app shell is served whole, not just the health ping"
# The health endpoint above answers before any app code has run, and this app
# is client-rendered, so its served HTML carries no page title or content to
# assert on - the title is set over the websocket once a page executes. What
# this step can prove is that the shell is a real, complete app shell: it
# names a script bundle, and that bundle is actually served rather than 404ing
# on a broken static path. Whether a page *renders* is step 4's, and nothing
# short of step 4 answers it.
# --interactive, because without it `docker exec` attaches no stdin and the
# heredoc below is silently discarded - a check that passes having run nothing.
docker exec --interactive "$container" python - <<'PY'
import re
import urllib.request

BASE = "http://localhost:8501"

html = urllib.request.urlopen(f"{BASE}/").read().decode("utf-8", "replace")
bundles = re.findall(r'src="\.?/?(static/js/[^"]+\.js)"', html)
if not bundles:
	raise SystemExit(f"FAIL: served HTML references no script bundle. First 500 bytes:\n{html[:500]}")

for bundle in bundles:
	response = urllib.request.urlopen(f"{BASE}/{bundle}")
	if response.status != 200:
		raise SystemExit(f"FAIL: {bundle} returned HTTP {response.status}")
	print(f"    {bundle} served, {len(response.read())} bytes")
PY

echo "==> 4/4 running every page headlessly, in the image"
docker run --rm "${run_args[@]}" \
	--volume "$script_dir/exercise_pages.py:/app/exercise_pages.py:ro" \
	"$tag" python exercise_pages.py

echo
echo "PASS: the app builds, serves, and every page renders."
echo "The mesh sidecar is a separate check - see skills/private-networking/SKILL.md."
