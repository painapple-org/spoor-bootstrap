#!/usr/bin/env bash
#
# Prove the check catches a broken product, not that the check runs.
#
# This is the same standard the check itself is held to, applied one level up:
# a synthetic check that has only ever been watched passing is unverified, for
# exactly the reason a green deploy is not a shipped one. So every case below
# breaks one specific thing about the example product and asserts the runner
# fails, at the named step, with an alert sent - plus the two cases that are
# about the runner's own restraint rather than its detection: a passing run
# leaves no test data behind and sends nothing at all.
#
# Ten cases, each a real failure mode of this pattern:
#
#   1  healthy                 passes, cleans up after itself, alerts nobody
#   2  200-that-lies           accepted submit, no row
#   3  half-working flow       row written, nobody notified
#   4  data pollution          the check's own signup counted as a real user
#   5  too slow to be usable   works, over its own time budget
#   6  outright error          the flow 500s
#   7  unreachable target      nothing listening at all
#   8  repeat suppression      an unchanged failure alerts once, not every run
#   9  recovery notice         a fixed flow says so, exactly once
#   10 unconfigured runner     no target: exit 2, not a false green
#
# Needs python3 and curl, nothing else - no Docker, no dependency install. A
# check runs from wherever the scheduler is, so its verification is kept
# runnable in the same place.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Scoped to this run so two of these in parallel, or the leftovers of a crashed
# one, cannot collide on a path or a port.
work="$(mktemp -d "/tmp/synthetic-check-verify-$$-XXXXXX")"
product_pid=""
product_url=""
failures=0
# The slow-flow case needs three numbers ordered: the flow's own MAX_SECONDS in
# flows/signup.py, then this, then the checker's HTTP timeout below. Injected
# slowness under the budget proves nothing, and slowness over the timeout gets
# reported as an unreachable target instead of a slow one.
slow_seconds=6
case_number=0

cleanup() {
	if [[ -n "$product_pid" ]]; then
		kill "$product_pid" 2>/dev/null || true
		wait "$product_pid" 2>/dev/null || true
	fi
	rm -rf "$work"
}
trap cleanup EXIT

free_port() {
	python3 - <<'PY'
import socket

with socket.socket() as probe:
	probe.bind(("127.0.0.1", 0))
	print(probe.getsockname()[1])
PY
}

# Starts the example product with one fault injected, on its own port and its
# own state directory, and does not return until it actually answers. Sets
# `product_url` rather than printing it: a command substitution would put the
# launch in a subshell, where `$!` is the subshell's own idea of the background
# job and the parent is left with no pid to kill - so every case would leak a
# server and later cases would be checking an earlier case's product.
start_product() {
	local break_mode="$1" state_dir="$2" port waited=0
	port="$(free_port)"
	PRODUCT_BREAK="$break_mode" \
	PRODUCT_PORT="$port" \
	PRODUCT_STATE_DIR="$state_dir" \
	PRODUCT_SLOW_SECONDS="$slow_seconds" \
		python3 example_product/app.py >>"$work/product.log" 2>&1 &
	product_pid=$!
	product_url="http://127.0.0.1:$port"

	until curl -fsS --max-time 2 "$product_url/health" >/dev/null 2>&1; do
		waited=$((waited + 1))
		if [[ $waited -gt 50 ]]; then
			echo "FAIL: example product never answered /health. Log:" >&2
			cat "$work/product.log" >&2
			exit 1
		fi
		sleep 0.2
	done
}

stop_product() {
	if [[ -n "$product_pid" ]]; then
		kill "$product_pid" 2>/dev/null || true
		wait "$product_pid" 2>/dev/null || true
		product_pid=""
	fi
}

# Runs the checker against a target and records its exit code and output.
run_checks() {
	local base_url="$1" state_dir="$2" alert_log="$3" exit_code=0
	SYNTHETIC_TARGET_BASE_URL="$base_url" \
	SYNTHETIC_EVIDENCE_TOKEN=toy-evidence-token \
	SYNTHETIC_STATE_DIR="$state_dir" \
	SYNTHETIC_ALERT_LOG="$alert_log" \
	SYNTHETIC_ALERT_COMMAND="$script_dir/example_alert_command.sh" \
	SYNTHETIC_HTTP_TIMEOUT_SECONDS=10 \
		python3 run_checks.py >"$work/run.out" 2>"$work/run.err" || exit_code=$?
	printf '%s\n' "$exit_code" >"$work/run.code"
	cat "$work/run.out" "$work/run.err" >"$work/run.all"
}

announce() {
	case_number=$((case_number + 1))
	printf '\n==> case %s: %s\n' "$case_number" "$1"
}

check() {
	local what="$1" ok="$2"
	if [[ "$ok" == "yes" ]]; then
		printf '    ok: %s\n' "$what"
	else
		printf '    FAIL: %s\n' "$what" >&2
		failures=$((failures + 1))
	fi
}

expect_exit() {
	local want="$1" got
	got="$(cat "$work/run.code")"
	if [[ "$got" == "$want" ]]; then
		check "exited $want" yes
	else
		check "exited $want (got $got). Output:" no
		sed 's/^/        /' "$work/run.all" >&2
	fi
}

expect_output() {
	local needle="$1"
	if grep -qF -- "$needle" "$work/run.all"; then
		check "report says '$needle'" yes
	else
		check "report says '$needle'. Output:" no
		sed 's/^/        /' "$work/run.all" >&2
	fi
}

expect_no_output() {
	local needle="$1"
	if grep -qF -- "$needle" "$work/run.all"; then
		check "report does not say '$needle'" no
	else
		check "report does not say '$needle'" yes
	fi
}

# Counts alerts of one kind in the example alert command's log.
expect_alerts() {
	local kind="$1" want="$2" log="$3" got=0
	if [[ -f "$log" ]]; then
		got="$(grep -c "^kind=$kind\$" "$log" || true)"
	fi
	if [[ "$got" == "$want" ]]; then
		check "sent $want '$kind' alert(s)" yes
	else
		check "sent $want '$kind' alert(s), sent $got" no
	fi
}

# Reads the product's own database directly: the assertion is about what is
# left in production after a run, so it deliberately does not go through the
# product's API, which could report whatever it liked.
expect_rows_left() {
	local state_dir="$1" want="$2" got
	got="$(python3 - "$state_dir/product.db" <<'PY'
import sqlite3
import sys

with sqlite3.connect(sys.argv[1]) as connection:
	print(connection.execute("SELECT COUNT(*) FROM signups").fetchone()[0])
PY
)"
	if [[ "$got" == "$want" ]]; then
		check "$want row(s) left in the product's database" yes
	else
		check "$want row(s) left in the product's database, found $got" no
	fi
}

# --- 1: a healthy product ---------------------------------------------------

announce "a healthy product passes, cleans up after itself, and alerts nobody"
state="$work/state-1"
start_product none "$work/product-1"
run_checks "$product_url" "$state" "$work/alerts-1.log"
expect_exit 0
expect_output "[PASS] signup"
expect_output "proved row-persisted"
expect_output "proved notification-sent"
expect_output "proved excluded-from-analytics"
expect_output "verified gone"
expect_alerts failure 0 "$work/alerts-1.log"
expect_rows_left "$work/product-1" 0
if [[ -f "$state/last-run.json" ]]; then
	check "recorded a heartbeat for the run" yes
else
	check "recorded a heartbeat for the run" no
fi
stop_product

# --- 2: the 200 that lies ---------------------------------------------------

announce "an accepted submit with no row behind it fails at row-persisted"
start_product side_effect "$work/product-2"
run_checks "$product_url" "$work/state-2" "$work/alerts-2.log"
expect_exit 1
expect_output "failed at row-persisted"
expect_output "returned 201 but no row exists"
expect_alerts failure 1 "$work/alerts-2.log"
stop_product

# --- 3: the half-working flow -----------------------------------------------

announce "a stored signup nobody is notified about fails at notification-sent"
start_product notification "$work/product-3"
run_checks "$product_url" "$work/state-3" "$work/alerts-3.log"
expect_exit 1
expect_output "failed at notification-sent"
expect_output "proved row-persisted"
# Cleanup has to happen on the failing path too, or a broken flow slowly fills
# production with the checker's own rows.
expect_output "verified gone"
expect_rows_left "$work/product-3" 0
stop_product

# --- 4: data pollution ------------------------------------------------------

announce "the check's own signup counted as a real user fails at excluded-from-analytics"
start_product pollution "$work/product-4"
run_checks "$product_url" "$work/state-4" "$work/alerts-4.log"
expect_exit 1
expect_output "failed at excluded-from-analytics"
expect_output "being counted as a real user"
stop_product

# --- 5: works, but not usably -----------------------------------------------

announce "a flow slower than its own budget fails at within-time-budget"
start_product slow "$work/product-5"
run_checks "$product_url" "$work/state-5" "$work/alerts-5.log"
expect_exit 1
expect_output "failed at within-time-budget"
stop_product

# --- 6: an outright error ---------------------------------------------------

announce "a 500 from the flow fails at submit-accepted"
start_product error "$work/product-6"
run_checks "$product_url" "$work/state-6" "$work/alerts-6.log"
expect_exit 1
expect_output "failed at submit-accepted"
stop_product

# --- 7: nothing listening ---------------------------------------------------

announce "an unreachable target fails at reachable rather than hanging"
run_checks "http://127.0.0.1:$(free_port)" "$work/state-7" "$work/alerts-7.log"
expect_exit 1
expect_output "failed at reachable"

# --- 8 & 9: repeat suppression, then a recovery notice ----------------------

announce "an unchanged failure alerts once, not once per run"
state="$work/state-8"
alerts="$work/alerts-8.log"
start_product side_effect "$work/product-8"
run_checks "$product_url" "$state" "$alerts"
expect_exit 1
run_checks "$product_url" "$state" "$alerts"
expect_exit 1
expect_alerts failure 1 "$alerts"
stop_product

announce "the same flow, once fixed, sends exactly one recovery notice"
start_product none "$work/product-9"
run_checks "$product_url" "$state" "$alerts"
expect_exit 0
expect_alerts recovery 1 "$alerts"
run_checks "$product_url" "$state" "$alerts"
expect_exit 0
expect_alerts recovery 1 "$alerts"
stop_product

# --- 10: the runner's own misconfiguration ----------------------------------

announce "a runner with no target exits 2, not 0 and not 1"
exit_code=0
env -u SYNTHETIC_TARGET_BASE_URL python3 run_checks.py >"$work/run.out" 2>"$work/run.err" || exit_code=$?
printf '%s\n' "$exit_code" >"$work/run.code"
cat "$work/run.out" "$work/run.err" >"$work/run.all"
expect_exit 2
expect_output "SYNTHETIC_TARGET_BASE_URL is unset"
expect_no_output "[PASS]"

# --- result -----------------------------------------------------------------

echo
if [[ $failures -gt 0 ]]; then
	echo "FAIL: $failures assertion(s) failed across $case_number cases." >&2
	exit 1
fi
echo "PASS: $case_number cases. The check catches every injected fault, alerts once per"
echo "distinct failure, notices a recovery, and leaves no test data behind when it passes."
