#!/usr/bin/env python3
#
# Self-test for ../../spoor-doctor-watch. Driven by the doctor-watch-self-test
# job in ../workflows/ci.yml.
#
# What this has to prove is narrower than what ../../.github/ci/test-doctor.py
# proves, and it is the half that is easy to get invisibly wrong. The doctor's
# own self-test already establishes that each check catches its own failure;
# nothing there says anything about the layer that decides *whether a human is
# told*. That layer has exactly two ways to fail, and both of them look fine
# from the outside:
#
#   - It stays quiet when something just broke, so the break is now documented
#     rather than reported.
#   - It shouts on every run of an already-known break, which trains whoever
#     reads it to filter the channel, at which point the next real alert is
#     filtered too.
#
# So every case below drives a real invocation of the watcher — no mocked
# internals, no imported functions — and asserts on what a human would
# actually have received: the alert commands that ran, with what kind and what
# body, and the process exit code.
#
# The scenario cases point the watcher at a *stub* doctor: a real executable at
# the path the watcher invokes, printing a `--json` document this script
# controls. That is what makes "healthy, then one thing breaks, then it stays
# broken, then it is fixed" expressible at all — driving the same sequence
# through the real doctor would mean breaking and repairing a real fixture
# deployment for each transition, which is the doctor self-test's job and not
# this one's. The last two cases close that gap from the other end by running
# the watcher against the real `./spoor-doctor` in this checkout.
#
# Run from anywhere; it locates the repo root relative to its own path.

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WATCH = REPO_ROOT / "spoor-doctor-watch"

failures = []

def fail(case, message):
	failures.append(f"{case}: {message}")

# A doctor stub whose whole behaviour is a plan file this script rewrites
# between runs. It prints its plan's stdout verbatim, so a case can hand the
# watcher a malformed document as easily as a healthy report.
DOCTOR_STUB = '''#!/usr/bin/env python3
import json, pathlib, sys
plan = json.loads((pathlib.Path(__file__).resolve().parent / "plan.json").read_text())
sys.stdout.write(plan["stdout"])
sys.exit(plan["exit_code"])
'''

# An alert command with the same contract as the real thing: the report on
# stdin, the kind as its one argument. It appends what it received to a log the
# case reads back, and refuses when a marker file exists, which is how the
# alerting-path-outage case gets a genuine non-zero exit rather than a stubbed
# return value.
ALERT_STUB = '''#!/usr/bin/env python3
import json, os, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
if (here / "refuse-alerts").exists():
	print("alert transport is down", file=sys.stderr)
	sys.exit(1)
with (here / "alerts.jsonl").open("a", encoding="utf-8") as log:
	log.write(json.dumps({"kind": sys.argv[1], "text": sys.stdin.read()}) + "\\n")
'''

class Fixture:
	"""One watcher deployment on disk: a stub doctor, a stub alert command, and
	a state directory the watcher owns."""

	def __init__(self, root, real_doctor=False):
		self.root = root
		self.state_dir = root / "state"
		self.repo_root = REPO_ROOT if real_doctor else root
		if not real_doctor:
			stub = root / "spoor-doctor"
			stub.write_text(DOCTOR_STUB, encoding="utf-8")
			stub.chmod(0o755)
		self.alert = root / "alert-command"
		self.alert.write_text(ALERT_STUB, encoding="utf-8")
		self.alert.chmod(0o755)

	def plan(self, statuses=None, exit_code=None, stdout=None):
		"""What the stub doctor will answer on the next run."""
		if stdout is None:
			checks = [
				{"id": check, "status": status, "message": f"{check} is {status} in this fixture"}
				for check, status in statuses.items()
			]
			counts = {
				status: sum(1 for value in statuses.values() if value == status)
				for status in ("PASS", "WARN", "FAIL", "SKIP")
			}
			failed = counts["FAIL"]
			stdout = json.dumps({
				"repo_root": str(self.root),
				"checks": checks,
				"counts": counts,
				"exit_code": 1 if failed else 0,
			})
			exit_code = (1 if failed else 0) if exit_code is None else exit_code
		(self.root / "plan.json").write_text(
			json.dumps({"stdout": stdout, "exit_code": exit_code or 0}), encoding="utf-8"
		)

	def run(self, alerting=True, extra=()):
		environment = dict(os.environ)
		environment.pop("DOCTOR_HEARTBEAT_URL", None)
		if alerting:
			environment["DOCTOR_ALERT_COMMAND"] = str(self.alert)
		else:
			environment.pop("DOCTOR_ALERT_COMMAND", None)
		command = [
			sys.executable, str(WATCH),
			"--repo-root", str(self.repo_root),
			"--state-dir", str(self.state_dir),
			*extra,
		]
		return subprocess.run(command, capture_output=True, text=True, env=environment, check=False)

	def alerts(self):
		path = self.root / "alerts.jsonl"
		if not path.is_file():
			return []
		return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

	def clear_alerts(self):
		(self.root / "alerts.jsonl").unlink(missing_ok=True)

	def refuse_alerts(self, refusing):
		marker = self.root / "refuse-alerts"
		if refusing:
			marker.write_text("", encoding="utf-8")
		else:
			marker.unlink(missing_ok=True)

	def recorded_statuses(self):
		path = self.state_dir / "checks.json"
		if not path.is_file():
			return None
		return json.loads(path.read_text(encoding="utf-8"))["statuses"]

HEALTHY = {"env-file": "PASS", "env-permissions": "PASS", "host-tooling-gh": "PASS", "doc-links": "WARN"}

def expect(case, condition, message):
	if not condition:
		fail(case, message)

def expect_alerts(case, fixture, expected_kinds, must_mention=(), must_not_mention=()):
	alerts = fixture.alerts()
	kinds = [alert["kind"] for alert in alerts]
	if kinds != list(expected_kinds):
		fail(case, f"expected alert kinds {list(expected_kinds)}, got {kinds}")
		return
	body = "\n".join(alert["text"] for alert in alerts)
	for needle in must_mention:
		if needle not in body:
			fail(case, f"the alert body does not mention {needle!r}:\n{body}")
	for needle in must_not_mention:
		if needle in body:
			fail(case, f"the alert body mentions {needle!r} and should not:\n{body}")

# --- the cases --------------------------------------------------------------

def case_scenario(root):
	"""The whole point of the script, in the order a real deployment lives it.

	Kept as one sequence rather than split into independent cases because the
	behaviour under test *is* the sequence: every assertion here is about what
	the previous run recorded."""
	case = "scenario"
	fixture = Fixture(root)

	# 1. First run, healthy. Nothing to report, and the state written is what
	# every later step diffs against.
	fixture.plan(HEALTHY)
	result = fixture.run()
	expect(case, result.returncode == 0, f"a healthy first run exited {result.returncode}, expected 0")
	expect_alerts(f"{case}/healthy-first-run", fixture, [])
	expect(
		case,
		fixture.recorded_statuses() == HEALTHY,
		f"the first run recorded {fixture.recorded_statuses()}, expected the doctor's own statuses",
	)
	expect(
		case,
		(fixture.state_dir / "last-run.json").is_file(),
		"no last-run.json was written, so nothing outside this script could notice it stopped running",
	)

	# 2. One check breaks. This is the alert the whole thing exists for.
	fixture.plan({**HEALTHY, "env-permissions": "FAIL"})
	result = fixture.run()
	expect(case, result.returncode == 1, f"a run with a failure exited {result.returncode}, expected 1")
	expect_alerts(
		f"{case}/new-failure", fixture, ["failure"],
		must_mention=["NEW FAILURE", "env-permissions", "env-permissions is FAIL in this fixture"],
	)

	# 3. The same break, still there. The suppression case: an identical alert
	# every hour is what turns the channel into weather.
	fixture.clear_alerts()
	result = fixture.run()
	expect(case, result.returncode == 1, f"a still-broken run exited {result.returncode}, expected 1")
	expect_alerts(f"{case}/known-failure-stays-quiet", fixture, [])
	expect(
		case,
		"STILL FAILING" in result.stdout,
		f"the report does not say the known failure is still failing:\n{result.stdout}",
	)

	# 4. A second, different check breaks while the first is still broken. News
	# about the new one, and the old one named as already reported rather than
	# re-announced.
	fixture.plan({**HEALTHY, "env-permissions": "FAIL", "host-tooling-gh": "FAIL"})
	result = fixture.run()
	expect_alerts(
		f"{case}/second-distinct-failure", fixture, ["failure"],
		must_mention=["NEW FAILURE  host-tooling-gh", "STILL FAILING (already reported)  env-permissions"],
		must_not_mention=["NEW FAILURE  env-permissions"],
	)

	# 5. A warning appears. Not a failure by the doctor's own exit code, so not
	# an alert either.
	fixture.clear_alerts()
	fixture.plan({**HEALTHY, "env-permissions": "FAIL", "host-tooling-gh": "FAIL", "env-file": "WARN"})
	fixture.run()
	expect_alerts(f"{case}/warning-is-not-a-failure", fixture, [])

	# 6. Everything is fixed. Exactly one recovery message, because a failure
	# alert with no closing message leaves the reader unsure it ever ended.
	fixture.plan(HEALTHY)
	result = fixture.run()
	expect(case, result.returncode == 0, f"a recovered run exited {result.returncode}, expected 0")
	expect_alerts(
		f"{case}/recovery", fixture, ["recovery"],
		must_mention=["RECOVERED  env-permissions", "RECOVERED  host-tooling-gh"],
	)

	# 7. Still fine. No second recovery message.
	fixture.clear_alerts()
	result = fixture.run()
	expect_alerts(f"{case}/recovery-happens-once", fixture, [])

def case_failing_check_becomes_skip(root):
	"""A FAIL that turns into a SKIP has stopped being answered, not been fixed."""
	case = "failing-check-becomes-skip"
	fixture = Fixture(root)
	fixture.plan({**HEALTHY, "comms-channel-token": "FAIL"})
	fixture.run()
	fixture.clear_alerts()

	fixture.plan({**HEALTHY, "comms-channel-token": "SKIP"})
	result = fixture.run()
	expect_alerts(
		case, fixture, ["unknown"],
		must_mention=["NO LONGER ANSWERED (was failing)  comms-channel-token"],
		must_not_mention=["RECOVERED"],
	)
	expect(case, result.returncode == 0, f"exited {result.returncode}; no check is FAILing, so 0 is right")

	# And it is news once, not every run.
	fixture.clear_alerts()
	fixture.run()
	expect_alerts(f"{case}/only-once", fixture, [])

def case_failing_check_disappears(root):
	"""Same again for a check that is gone from the report entirely."""
	case = "failing-check-disappears"
	fixture = Fixture(root)
	fixture.plan({**HEALTHY, "work-tracker-auth": "FAIL"})
	fixture.run()
	fixture.clear_alerts()

	fixture.plan(HEALTHY)
	fixture.run()
	expect_alerts(
		case, fixture, ["unknown"],
		must_mention=["NO LONGER ANSWERED (was failing)  work-tracker-auth"],
		must_not_mention=["RECOVERED"],
	)

def case_doctor_could_not_run(root):
	"""Exit 2 from the doctor is an unknown verdict, and it must not pass as fine."""
	case = "doctor-could-not-run"
	fixture = Fixture(root)
	fixture.plan(HEALTHY)
	fixture.run()
	fixture.clear_alerts()

	fixture.plan(stdout="spoor-doctor: /nope is not a directory\n", exit_code=2)
	result = fixture.run()
	expect(case, result.returncode == 2, f"exited {result.returncode}, expected 2 for an unknown verdict")
	expect_alerts(case, fixture, ["unknown"], must_mention=["NO VERDICT", "exited 2"])

	# Once, not every run — and the previous verdict survives, so the healthy
	# statuses are still what the next real run diffs against.
	fixture.clear_alerts()
	fixture.run()
	expect_alerts(f"{case}/only-once", fixture, [])
	expect(
		case,
		fixture.recorded_statuses() == HEALTHY,
		f"an unknown run overwrote the last real verdict with {fixture.recorded_statuses()}",
	)

def case_doctor_output_unparseable(root):
	"""Output that is not the JSON document promised is an unknown, not a pass."""
	case = "doctor-output-unparseable"
	fixture = Fixture(root)
	fixture.plan(stdout="PASS  env-file\nthis is the human report, not --json\n", exit_code=0)
	result = fixture.run()
	expect(case, result.returncode == 2, f"exited {result.returncode}, expected 2")
	expect_alerts(case, fixture, ["unknown"], must_mention=["NO VERDICT", "would not parse"])

def case_alert_delivery_failure(root):
	"""An undeliverable alert fails the run and records nothing.

	The recording half is the load-bearing one: if a failure were recorded as
	known while its alert never arrived, that break would be suppressed
	forever — the exact silence this script exists to prevent, produced by the
	thing meant to prevent it."""
	case = "alert-delivery-failure"
	fixture = Fixture(root)
	fixture.plan(HEALTHY)
	fixture.run()

	fixture.refuse_alerts(True)
	fixture.plan({**HEALTHY, "env-permissions": "FAIL"})
	result = fixture.run()
	expect(case, result.returncode == 2, f"exited {result.returncode}, expected 2 on a failed delivery")
	expect(
		case,
		"ALERT DELIVERY FAILED" in result.stderr,
		f"the failure was not reported loudly on stderr:\n{result.stderr}",
	)
	expect(
		case,
		fixture.recorded_statuses() == HEALTHY,
		f"the undelivered failure was recorded anyway ({fixture.recorded_statuses()}), which would "
		"suppress it forever",
	)

	# The alerting path comes back: the same break is still news.
	fixture.refuse_alerts(False)
	result = fixture.run()
	expect(case, result.returncode == 1, f"exited {result.returncode}, expected 1")
	expect_alerts(f"{case}/retried", fixture, ["failure"], must_mention=["NEW FAILURE  env-permissions"])

def case_no_alert_command(root):
	"""With nowhere to alert, a failure is still reported loudly and still fails."""
	case = "no-alert-command"
	fixture = Fixture(root)
	fixture.plan({**HEALTHY, "env-permissions": "FAIL"})
	result = fixture.run(alerting=False)
	expect(case, result.returncode == 1, f"exited {result.returncode}, expected 1")
	expect(
		case,
		"DOCTOR_ALERT_COMMAND is unset" in result.stderr and "reached nobody" in result.stderr,
		f"an unset alert command was not called out on stderr:\n{result.stderr}",
	)

def case_corrupt_state(root):
	"""A state file that will not parse is a first run again, and says so."""
	case = "corrupt-state"
	fixture = Fixture(root)
	fixture.plan({**HEALTHY, "env-permissions": "FAIL"})
	fixture.run()
	fixture.clear_alerts()
	(fixture.state_dir / "checks.json").write_text("{not json", encoding="utf-8")

	result = fixture.run()
	expect(case, "treating this as a first run" in result.stderr, f"no warning about the state file:\n{result.stderr}")
	expect_alerts(case, fixture, ["failure"], must_mention=["NEW FAILURE  env-permissions"])

def case_schedule_line(root):
	"""--schedule-line prints something pasteable, and installs nothing."""
	case = "schedule-line"
	fixture = Fixture(root)
	result = fixture.run(extra=["--schedule-line"])
	expect(case, result.returncode == 0, f"exited {result.returncode}, expected 0")
	for needle in (str(WATCH), str(fixture.repo_root), str(fixture.state_dir), "DOCTOR_ALERT_COMMAND"):
		expect(case, needle in result.stdout, f"the printed line omits {needle!r}:\n{result.stdout}")
	expect(
		case,
		not (fixture.state_dir / "checks.json").exists(),
		"--schedule-line ran a check; it is supposed to print and exit",
	)

def case_against_the_real_doctor(root):
	"""The one case that uses no stub: the real `./spoor-doctor`, in this checkout.

	Everything above proves the diffing. This proves the wiring — that the
	watcher invokes the real script, parses the real `--json` document, and
	agrees with its exit code. A CI checkout has no `.env`, so the doctor
	genuinely fails here, which is what makes the exit code and the
	suppression worth asserting rather than a tautology."""
	case = "against-the-real-doctor"
	fixture = Fixture(root, real_doctor=True)

	result = fixture.run(extra=["--offline"])
	expect(
		case,
		result.returncode == 1,
		f"exited {result.returncode}, expected 1 — a checkout with no .env has failing checks",
	)
	statuses = fixture.recorded_statuses()
	expect(case, statuses is not None, "no verdict was recorded from the real doctor")
	if statuses:
		for check in ("env-file", "harness-symlinks", "doc-links"):
			expect(case, check in statuses, f"the real doctor's {check} check is missing from {sorted(statuses)}")
		expect(
			case,
			statuses.get("env-file") == "FAIL",
			f"expected the real doctor to FAIL env-file in a checkout with no .env, got {statuses.get('env-file')}",
		)
	expect_alerts(case, fixture, ["failure"], must_mention=["NEW FAILURE  env-file"])

	# Second identical run against the real doctor: still no .env, still no
	# second alert.
	fixture.clear_alerts()
	result = fixture.run(extra=["--offline"])
	expect(case, result.returncode == 1, f"the second run exited {result.returncode}, expected 1")
	expect_alerts(f"{case}/known-failure-stays-quiet", fixture, [])

CASES = [
	case_scenario,
	case_failing_check_becomes_skip,
	case_failing_check_disappears,
	case_doctor_could_not_run,
	case_doctor_output_unparseable,
	case_alert_delivery_failure,
	case_no_alert_command,
	case_corrupt_state,
	case_schedule_line,
	case_against_the_real_doctor,
]

def main():
	if not WATCH.is_file():
		print(f"test-doctor-watch: {WATCH} does not exist", file=sys.stderr)
		return 2

	for case in CASES:
		with tempfile.TemporaryDirectory(prefix=f"watch-{case.__name__}-") as temporary:
			root = Path(temporary) / "fixture"
			root.mkdir()
			try:
				case(root)
			except Exception as error:  # a case that crashed proved nothing
				fail(case.__name__, f"the case itself raised {type(error).__name__}: {error}")
		print(f"ran {case.__name__}")

	if failures:
		print(f"\n{len(failures)} assertion(s) failed:\n", file=sys.stderr)
		for line in failures:
			print(f"  FAIL  {line}", file=sys.stderr)
		return 1
	print(f"\nAll {len(CASES)} cases passed: the watcher alerts on new news, once, and never on a known break.")
	return 0

if __name__ == "__main__":
	sys.exit(main())
