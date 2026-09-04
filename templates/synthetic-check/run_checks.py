#!/usr/bin/env python3
#
# The synthetic check runner. Scheduled, it drives every flow in `flows/`
# against the live product the same way a user would, proves the flow's real
# side effect actually happened, removes the test data it created, and alerts
# only when something failed.
#
# `skills/synthetic-monitoring/SKILL.md` is the home for which flows are worth
# a check, what counts as proof, and the rules about production data. This file
# is only the mechanism, and it is stdlib-only on purpose: a check that needs a
# dependency tree installed and patched is a check that eventually stops
# running for reasons that have nothing to do with the product.
#
# Exit codes, because a scheduler and a human both read them:
#   0  every flow passed
#   1  a flow failed (the product is broken, or its evidence source is)
#   2  the runner itself could not do its job - no target configured, a flow
#      module that won't import, an alert command that failed to run. This is
#      deliberately a different code from 1: it means the answer is unknown
#      rather than bad, and treating it as "product fine" is the silent
#      failure this whole pattern exists to prevent.

import importlib.util
import json
import os
import random
import shlex
import string
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FLOWS_DIR = Path(__file__).resolve().parent / "flows"

# A flow module does `from run_checks import CheckFailure`, and this file is
# `__main__` when run as a script - so without this alias Python imports a
# second, independent copy of it, and the CheckFailure a flow raises is not the
# class this file catches. The symptom would be every failing flow crashing the
# runner instead of being reported as a failure.
sys.modules.setdefault("run_checks", sys.modules[__name__])


class CheckFailure(Exception):
	"""A flow's own assertion failed: the product did not do what it promises.

	`step` names which part of the flow failed, and it is what an alert leads
	with - "signup: row-persisted" tells the owner where to look, where "signup
	failed" does not.
	"""

	def __init__(self, step, detail):
		super().__init__(f"{step}: {detail}")
		self.step = step
		self.detail = detail


class Context:
	"""What a flow is handed: where the product is, how to mark its test data,
	and an HTTP helper that cannot hang.

	Every value here comes from the environment rather than from a flow module,
	so the same flow file runs against a staging target and a production one
	without editing it.
	"""

	def __init__(self, run_id):
		self.run_id = run_id
		self.base_url = os.environ["SYNTHETIC_TARGET_BASE_URL"].rstrip("/")
		self.marker = os.environ.get("SYNTHETIC_TEST_MARKER", "synthetic")
		self.test_domain = os.environ.get("SYNTHETIC_TEST_EMAIL_DOMAIN", "synthetic.invalid")
		self.evidence_token = os.environ.get("SYNTHETIC_EVIDENCE_TOKEN", "")
		self.timeout = float(os.environ.get("SYNTHETIC_HTTP_TIMEOUT_SECONDS", "15"))

	def test_email(self, flow_name):
		"""A per-run address that is recognizable as synthetic by the product too.

		The marker is in the local part rather than only in the domain because
		the product's own exclusion rule has to be able to match it, and a
		product that stores addresses case-folded or strips a `+tag` still sees
		the prefix. Read the SKILL's data-pollution section before changing the
		shape of this: the product and this file have to agree on it.

		Lower-cased deliberately. Products routinely normalize an address on
		write, so a mixed-case identifier is stored as something the check then
		fails to find - and that miss is indistinguishable from the product
		having stored nothing, which is a real alert about a healthy product.
		Whatever identifier a flow builds, it has to survive the product's own
		normalization or the evidence step is checking the wrong string.
		"""
		return f"{self.marker}+{flow_name}-{self.run_id}@{self.test_domain}".lower()

	def request(self, method, path, params=None, body=None, headers=None, evidence=False):
		"""One HTTP call against the target, returning (status, parsed-or-text body).

		A non-2xx status is returned rather than raised: whether a 500 is a
		failure or the expected answer is the flow's judgment, not this
		helper's. What is never returned is a hang - `timeout` is always set,
		because a check that blocks forever produces no result and no alert,
		which reads exactly like a healthy product.

		Query values go through `params` rather than being formatted into
		`path`, because they are not safe to paste: a marked test address
		contains a `+`, which a server reading the query string decodes as a
		space, so an un-encoded evidence lookup silently searches for an
		address nobody has. That failure is indistinguishable from the product
		not having stored the row - a false alarm on every run.
		"""
		url = path if path.startswith("http") else f"{self.base_url}{path}"
		if params:
			url = f"{url}?{urllib.parse.urlencode(params)}"
		data = None
		request_headers = dict(headers or {})
		if body is not None:
			data = json.dumps(body).encode()
			request_headers["Content-Type"] = "application/json"
		# Marks the traffic at the request level as well as in the payload, so
		# the product's logs, rate limiters and analytics can all recognize it
		# without parsing a body.
		request_headers["X-Synthetic-Check"] = self.run_id
		if evidence and self.evidence_token:
			request_headers["X-Evidence-Token"] = self.evidence_token

		request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
		try:
			with urllib.request.urlopen(request, timeout=self.timeout) as response:
				return response.status, _parse(response.read())
		except urllib.error.HTTPError as error:
			return error.code, _parse(error.read())
		except (urllib.error.URLError, TimeoutError) as error:
			raise CheckFailure("reachable", f"{method} {url}: {error}") from error


def _parse(raw):
	text = raw.decode("utf-8", "replace")
	try:
		return json.loads(text)
	except ValueError:
		return text


def load_flows():
	"""Import every flow module, or fail loudly naming the one that wouldn't.

	A flow that cannot be imported is not skipped. Skipping it would drop a
	check from the run while the run still reported success, which is the one
	outcome worse than the check failing.
	"""
	selected = [name for name in os.environ.get("SYNTHETIC_FLOWS", "").split(",") if name]
	paths = sorted(p for p in FLOWS_DIR.glob("*.py") if not p.name.startswith("_"))
	if selected:
		by_stem = {p.stem: p for p in paths}
		missing = [name for name in selected if name not in by_stem]
		if missing:
			raise SystemExit(f"CONFIG: SYNTHETIC_FLOWS names no such flow file: {', '.join(missing)}")
		paths = [by_stem[name] for name in selected]

	flows = []
	for path in paths:
		spec = importlib.util.spec_from_file_location(f"synthetic_flow_{path.stem}", path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		for attribute in ("NAME", "trigger", "prove", "cleanup"):
			if not hasattr(module, attribute):
				raise SystemExit(f"CONFIG: {path.name} defines no {attribute}")
		flows.append(module)
	if not flows:
		raise SystemExit(f"CONFIG: no flow modules found in {FLOWS_DIR}")
	return flows


def run_flow(context, flow):
	"""Trigger, prove, then clean up - with cleanup attempted either way.

	Cleanup runs after a failed prove as well as a passing one, because a
	half-completed flow still left test data in the product. Its own failure is
	recorded as a failure of the run rather than logged and dropped: test data
	accumulating in production is the slow version of the pollution this
	pattern is supposed to avoid, and nobody notices it from the outside.
	"""
	started = time.monotonic()
	result = {"flow": flow.NAME, "status": "pass", "step": None, "detail": None, "evidence": []}
	receipt = None
	try:
		receipt = flow.trigger(context)
		# Appended one at a time rather than collected with list(), so a failure
		# part-way through `prove` keeps the evidence gathered before it. A
		# report that says only where the flow broke, having thrown away the
		# three things it had already confirmed, sends whoever reads it looking
		# in the wrong place: "the row is there, the notification isn't" is a
		# different investigation from "signup is broken".
		for evidence in flow.prove(context, receipt):
			result["evidence"].append(evidence)
	except CheckFailure as failure:
		result.update(status="fail", step=failure.step, detail=failure.detail)
	finally:
		result["seconds"] = round(time.monotonic() - started, 3)
		if receipt is not None:
			try:
				result["cleanup"] = flow.cleanup(context, receipt)
			except CheckFailure as failure:
				result["cleanup"] = f"FAILED - {failure}"
				if result["status"] == "pass":
					result.update(status="fail", step=f"cleanup/{failure.step}", detail=failure.detail)
		else:
			result["cleanup"] = "not attempted - the flow never got as far as creating anything"

	budget = getattr(flow, "MAX_SECONDS", None)
	if result["status"] == "pass" and budget is not None and result["seconds"] > budget:
		result.update(
			status="fail",
			step="within-time-budget",
			detail=f"flow took {result['seconds']}s, over its MAX_SECONDS of {budget}",
		)
	return result


def render(results, run_id):
	lines = [f"synthetic check run {run_id}"]
	for result in results:
		head = "PASS" if result["status"] == "pass" else "FAIL"
		lines.append(f"  [{head}] {result['flow']} ({result['seconds']}s)")
		for name, detail in result["evidence"]:
			lines.append(f"      proved {name}: {detail}")
		if result["status"] == "fail":
			lines.append(f"      failed at {result['step']}: {result['detail']}")
		lines.append(f"      cleanup: {result['cleanup']}")
	return "\n".join(lines)


def alert_state_path(state_dir, flow_name):
	return state_dir / f"alert-{flow_name}.json"


def notify(text, kind):
	"""Hand the report to whatever this deployment alerts through.

	The command is configuration, not code here, because the destination has
	exactly one home and it is not this file - see the SKILL's alerting
	section, which points at `skills/comms-channel`. `kind` is passed as the
	first argument so a recovery notice can be worded differently from a
	failure without this file knowing how either is phrased.
	"""
	command = os.environ.get("SYNTHETIC_ALERT_COMMAND", "").strip()
	if not command:
		print(f"[no SYNTHETIC_ALERT_COMMAND set; would have sent a '{kind}' alert]", file=sys.stderr)
		return
	argv = shlex.split(command) + [kind]
	completed = subprocess.run(argv, input=text, text=True, check=False)
	if completed.returncode != 0:
		# An alert that failed to send is an outage of the alerting path, and
		# the only thing left to do is make the run itself fail loudly rather
		# than exit 0 having told nobody.
		raise SystemExit(f"ALERT DELIVERY FAILED: {argv[0]} exited {completed.returncode}")


def handle_alerting(results, report, state_dir):
	"""Alert on a new or changed failure, and once on recovery. Nothing else.

	A check that re-sends an identical alert every run trains its reader to
	filter it, and a filtered alert is not coverage. So the signature of the
	current failure is compared against the last one alerted per flow: a
	changed signature is news, an identical one is not, and a flow that went
	from failing to passing is news exactly once.
	"""
	state_dir.mkdir(parents=True, exist_ok=True)
	for result in results:
		path = alert_state_path(state_dir, result["flow"])
		previous = json.loads(path.read_text()) if path.is_file() else {}
		# The step, not the detail: a detail carries this run's own identifiers
		# by construction (the test address, the row id), so comparing details
		# would make every run a new failure and defeat the suppression
		# entirely. The cost is deliberate and worth knowing - two different
		# causes failing at the same step alert once between them, and the
		# report attached to that first alert is where the specifics are.
		signature = result["step"] if result["status"] == "fail" else ""

		if result["status"] == "fail":
			if previous.get("signature") != signature:
				notify(report, "failure")
			path.write_text(json.dumps({"signature": signature, "at": _now()}))
		else:
			if previous.get("signature"):
				notify(report, "recovery")
			if path.is_file():
				path.unlink()


def heartbeat(state_dir, run_id, ok):
	"""Record that a run happened, and tell an external watcher it did.

	This is the answer to "who notices when the check itself stops running?",
	and it is not rhetorical: a crashed cron job, a rotated token or an
	uninstalled dependency all silence every check above without producing a
	single failure. Only a signal that fires on the *absence* of a beat catches
	that, so this pings on a successful run and stays quiet otherwise, leaving
	the watcher to alarm on the silence.
	"""
	(state_dir / "last-run.json").write_text(json.dumps({"run_id": run_id, "ok": ok, "at": _now()}))
	url = os.environ.get("SYNTHETIC_HEARTBEAT_URL", "").strip()
	if not url or not ok:
		return
	try:
		with urllib.request.urlopen(url, timeout=10) as response:
			response.read()
	except (urllib.error.URLError, TimeoutError) as error:
		print(f"WARNING: heartbeat ping to {url} failed: {error}", file=sys.stderr)


def _now():
	return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
	if not os.environ.get("SYNTHETIC_TARGET_BASE_URL"):
		raise SystemExit("CONFIG: SYNTHETIC_TARGET_BASE_URL is unset - there is nothing to check")

	# Lower case throughout, for the reason Context.test_email gives: the run id
	# ends up inside identifiers a product may normalize.
	run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + "".join(
		random.choices(string.ascii_lowercase + string.digits, k=4)
	)
	context = Context(run_id)
	results = [run_flow(context, flow) for flow in load_flows()]
	report = render(results, run_id)
	print(report)

	ok = all(result["status"] == "pass" for result in results)
	state_dir = Path(os.environ.get("SYNTHETIC_STATE_DIR", ".synthetic-state")).expanduser()
	handle_alerting(results, report, state_dir)
	heartbeat(state_dir, run_id, ok)
	return 0 if ok else 1


if __name__ == "__main__":
	try:
		sys.exit(main())
	except SystemExit as exit_request:
		# A string payload is one of this file's own CONFIG/ALERT failures: the
		# runner could not do its job, which is exit 2 and not exit 1.
		if isinstance(exit_request.code, str):
			print(exit_request.code, file=sys.stderr)
			sys.exit(2)
		raise
