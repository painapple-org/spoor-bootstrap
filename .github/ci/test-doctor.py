#!/usr/bin/env python3
#
# Self-test for ../../spoor-doctor. Driven by the doctor-self-test job in
# ../workflows/ci.yml.
#
# A diagnostic tool that reports "healthy" on a broken deployment is worse
# than no tool at all: it converts a fixable problem into a documented
# absence of one. So nothing here trusts the doctor's own report. Every case
# below builds a complete, genuinely healthy fixture deployment, breaks
# exactly one thing about it in the way a real deployment breaks, and asserts
# the doctor names that specific check as FAILed (or, for the two
# empty-allowlist cases, that it correctly does *not*).
#
# The fixture is a real deployment, not a mock: a copy of this checkout, its
# own git repo pushing to a bare `origin` on disk, a second repo standing in
# for the product, a conventions doc, and a `.env` filled in the way
# first-boot setup fills it. Two of the fixture's services are real servers
# on localhost — an HTTP one answering the tracker's identity endpoint, and a
# TCP one standing in for the mail host — so the doctor's credential probes
# are exercised over an actual socket with an actual rejection path, rather
# than being skipped. Nothing here contacts the internet.
#
# Run from anywhere; it locates the repo root relative to its own path.

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCTOR = "spoor-doctor"

# What the fixture's tracker credential is, on the fixture's side of the
# wire. The HTTP stand-in below accepts exactly this pair and nothing else,
# which is what makes the rejected-credential case a real rejection.
FIXTURE_TRACKER_TOKEN = "fixture-tracker-token-9f2c"
FIXTURE_AGENT_EMAIL = "agent@fixture.test"

# Checks whose verdict depends on the machine the test runs on rather than on
# the fixture: whether this box has docker/uv/gh installed and a reachable
# docker daemon, and whether it happens to be on a mesh VPN. The doctor is
# right to report them; a CI runner is simply not the deployment host they
# describe, so the healthy-baseline case excludes them instead of pretending
# otherwise.
HOST_DEPENDENT = ("host-tooling-docker", "host-tooling-uv", "host-tooling-gh", "private-networking")

failures = []

def fail(case, message):
	failures.append(f"{case}: {message}")

# --- the fixture's two local servers ----------------------------------------

class TrackerHandler(BaseHTTPRequestHandler):
	"""Jira's identity endpoint, as much of it as the doctor's probe reads.

	Accepts HTTP Basic with the fixture's own email and token, 401s anything
	else — so a wrong credential in the fixture's `.env` is refused by a real
	server rather than by a stubbed return value."""

	def do_GET(self):
		if self.path != "/rest/api/3/myself":
			self.send_error(404)
			return
		expected = base64.b64encode(f"{FIXTURE_AGENT_EMAIL}:{FIXTURE_TRACKER_TOKEN}".encode()).decode()
		if self.headers.get("Authorization") != f"Basic {expected}":
			body = json.dumps({"errorMessages": ["Client must be authenticated"]}).encode()
			self.send_response(401)
			self.send_header("Content-Type", "application/json")
			self.send_header("Content-Length", str(len(body)))
			self.end_headers()
			self.wfile.write(body)
			return
		body = json.dumps({"accountId": "fixture-account", "emailAddress": FIXTURE_AGENT_EMAIL}).encode()
		self.send_response(200)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def log_message(self, *args):
		pass

def start_tracker_server():
	server = ThreadingHTTPServer(("127.0.0.1", 0), TrackerHandler)
	threading.Thread(target=server.serve_forever, daemon=True).start()
	return server, server.server_address[1]

def start_mail_server():
	"""A socket that accepts and says an SMTP-shaped hello. The doctor's
	COMMS_CHANNEL=none probe only asserts the host accepts a connection, so
	that is all this has to do."""
	listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	listener.bind(("127.0.0.1", 0))
	listener.listen(8)

	def serve():
		while True:
			try:
				connection, _ = listener.accept()
			except OSError:
				return
			with connection:
				try:
					connection.sendall(b"220 fixture-mail ESMTP\r\n")
				except OSError:
					pass

	threading.Thread(target=serve, daemon=True).start()
	return listener, listener.getsockname()[1]

# --- fixture construction ---------------------------------------------------

def git(*arguments, cwd):
	subprocess.run(
		["git", "-c", "user.email=fixture@fixture.test", "-c", "user.name=Fixture", *arguments],
		cwd=str(cwd),
		check=True,
		capture_output=True,
		text=True,
	)

def specialize_fixture(checkout):
	"""Turn the template's stubs into the shape a finished first boot leaves.

	The doctor is a post-onboarding tool, so its healthy baseline is a
	deployment that has actually been through STARTUP.md's specialization
	pass — not a fresh clone. Reproducing that means the three things the pass
	itself does: answer the markers, drop each file's `Status:` heading, and
	drop the matching stub labels from the skills index. Doing all three keeps
	the fixture consistent by the same rules check-skills-consistency.py
	enforces on this repo, which is what lets the healthy case assert that
	*nothing* fails."""
	for skill in sorted((checkout / "skills").glob("*/SKILL.md")):
		text = skill.read_text(encoding="utf-8")
		text = text.replace("TODO(specialize)", "specialized for this fixture")
		text = "\n".join(
			line for line in text.splitlines() if not line.lstrip("#").strip().startswith("Status:")
		)
		skill.write_text(text + "\n", encoding="utf-8")

	index = checkout / "skills" / "README.md"
	index_text = index.read_text(encoding="utf-8")
	for label in ("*partial stub.* ", "*stub.* ", "*partial stub.*", "*stub.*"):
		index_text = index_text.replace(label, "")
	index.write_text(index_text, encoding="utf-8")

	# work-pipeline being specialized means stages were chosen, so the
	# prompts those stages run with have to exist — that is the pairing the
	# doctor's stage-prompts check is about.
	(checkout / "prompts" / "implement.md").write_text(
		"# implement\n\nRead skills/work-pipeline/SKILL.md, then the conventions doc named by\n"
		"CONVENTIONS_DOC_PATH in .env. Claim the next eligible item, implement it, ship it\n"
		"through a PR per skills/git-pr-conventions/SKILL.md.\n",
		encoding="utf-8",
	)

def build_fixture(root, tracker_port, mail_port):
	"""A complete, healthy deployment on disk. Returns the checkout path."""
	checkout = root / "deployment"
	shutil.copytree(
		REPO_ROOT,
		checkout,
		symlinks=True,
		ignore=shutil.ignore_patterns(".git", ".env"),
	)
	specialize_fixture(checkout)

	# A bare repo on disk is a real, pushable `origin`: the doctor's dry-run
	# push against it is a genuine network-shaped operation with a genuine
	# refusal path, and it needs nothing outside this temp directory.
	origin = root / "origin.git"
	subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
	git("init", "-q", "-b", "main", cwd=checkout)
	git("add", "-A", cwd=checkout)
	git("commit", "-q", "-m", "fixture deployment", cwd=checkout)
	git("remote", "add", "origin", f"file://{origin}", cwd=checkout)

	product = root / "product"
	product_origin = root / "product-origin.git"
	product.mkdir()
	subprocess.run(["git", "init", "-q", "--bare", str(product_origin)], check=True)
	git("init", "-q", "-b", "main", cwd=product)
	(product / "CONVENTIONS.md").write_text("# Fixture conventions\n", encoding="utf-8")
	git("add", "-A", cwd=product)
	git("commit", "-q", "-m", "fixture product", cwd=product)
	git("remote", "add", "origin", f"file://{product_origin}", cwd=product)

	# A deployment that actually built an internal dashboard: a standalone
	# project outside the product repo, with its own history. The healthy
	# baseline includes one so the location checks are exercised against a
	# real directory rather than only against a blank value.
	dashboard = root / "dashboard"
	dashboard.mkdir()
	git("init", "-q", "-b", "main", cwd=dashboard)
	(dashboard / "streamlit_app.py").write_text("# fixture dashboard\n", encoding="utf-8")
	git("add", "-A", cwd=dashboard)
	git("commit", "-q", "-m", "fixture dashboard", cwd=dashboard)

	write_env(
		checkout,
		{
			"PRODUCT_REPO_PATH": str(product),
			"INTERNAL_DASHBOARD_PATH": str(dashboard),
			"CONVENTIONS_DOC_PATH": "CONVENTIONS.md",
			"WORK_TRACKER": "jira",
			"WORK_TRACKER_API_KEY": FIXTURE_TRACKER_TOKEN,
			"WORK_TRACKER_BASE_URL": f"http://127.0.0.1:{tracker_port}",
			"COMMS_CHANNEL": "none",
			"COMMS_CHANNEL_TOKEN": "fixture-mail-password",
			"COMMS_CHANNEL_ENDPOINT": f"127.0.0.1:{mail_port}",
			"COMMS_ALERT_TARGET": "owner@fixture.test",
			"COMMS_ALLOWLIST": "",
			"AGENT_EMAIL_ADDRESS": FIXTURE_AGENT_EMAIL,
			"OWNER_TECH_LEVEL": "non-technical",
			"END_USER_TYPE": "non-technical",
		},
	)
	return checkout

def write_env(checkout, values):
	path = checkout / ".env"
	path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
	path.chmod(0o600)

def read_env(checkout):
	values = {}
	for line in (checkout / ".env").read_text(encoding="utf-8").splitlines():
		if "=" in line and not line.startswith("#"):
			key, _, value = line.partition("=")
			values[key] = value
	return values

def edit_env(checkout, **changes):
	values = read_env(checkout)
	values.update(changes)
	write_env(checkout, values)

def run_doctor(checkout, offline):
	command = [sys.executable, str(checkout / DOCTOR)]
	if offline:
		command.append("--offline")
	command.append("--json")
	completed = subprocess.run(command, cwd=str(checkout), capture_output=True, text=True, timeout=300)
	try:
		report = json.loads(completed.stdout)
	except ValueError:
		raise AssertionError(
			f"{DOCTOR} did not emit JSON (exit {completed.returncode}):\n"
			f"{completed.stdout[-2000:]}\n{completed.stderr[-2000:]}"
		)
	return report, completed.returncode

def statuses(report):
	return {check["id"]: check["status"] for check in report["checks"]}

def message_for(report, check_id):
	for check in report["checks"]:
		if check["id"] == check_id:
			return check["message"]
	return ""

# --- the cases --------------------------------------------------------------
#
# Each entry: a name, a function that breaks one thing about the healthy
# fixture, the (check id, expected status) pairs asserted afterwards, and
# whether to run the doctor with --offline. Offline is used only where the
# break itself is about a network-independent fact and letting the probes run
# would make the case slower without proving anything more.

def case_healthy(checkout):
	pass

def case_env_missing(checkout):
	(checkout / ".env").unlink()

def case_env_world_readable(checkout):
	(checkout / ".env").chmod(0o644)

def case_env_committed(checkout):
	git("add", "-f", ".env", cwd=checkout)
	git("commit", "-q", "-m", "oops", cwd=checkout)

def case_required_blank(checkout):
	edit_env(checkout, WORK_TRACKER="")

def case_placeholder_value(checkout):
	edit_env(checkout, COMMS_CHANNEL_TOKEN="changeme")

def case_placeholder_angle_brackets(checkout):
	edit_env(checkout, COMMS_ALERT_TARGET="<the owner's email>")

def case_value_outside_oneof(checkout):
	edit_env(checkout, OWNER_TECH_LEVEL="yes")

def case_invented_key(checkout):
	with (checkout / ".env").open("a", encoding="utf-8") as handle:
		handle.write("MY_OWN_EXTRA_TOKEN=abc\n")

def case_key_absent_from_env(checkout):
	values = read_env(checkout)
	del values["AGENT_EMAIL_ADDRESS"]
	write_env(checkout, values)

def case_malformed_env_line(checkout):
	with (checkout / ".env").open("a", encoding="utf-8") as handle:
		handle.write("this line is not a key=value pair at all\n")

def case_unannotated_schema_key(checkout):
	path = checkout / ".env.example"
	path.write_text(
		path.read_text(encoding="utf-8").replace("# doctor: required\nAGENT_EMAIL_ADDRESS=", "AGENT_EMAIL_ADDRESS="),
		encoding="utf-8",
	)

def case_origin_still_upstream(checkout):
	git("remote", "set-url", "origin", "https://github.com/painapple-org/spoor-bootstrap.git", cwd=checkout)

def case_origin_missing(checkout):
	git("remote", "remove", "origin", cwd=checkout)

def case_origin_unpushable(checkout):
	git("remote", "set-url", "origin", f"file://{checkout.parent / 'nonexistent.git'}", cwd=checkout)

def case_installer_guard_unreadable(checkout):
	path = checkout / "install.sh"
	path.write_text(
		path.read_text(encoding="utf-8").replace('*"painapple-org/spoor-bootstrap"*', '"$SOMETHING_ELSE"'),
		encoding="utf-8",
	)

def case_allowlist_empty_on_verifying_channel(checkout):
	edit_env(checkout, COMMS_CHANNEL="telegram", COMMS_ALLOWLIST="")

def case_allowlist_empty_on_channel_none(checkout):
	edit_env(checkout, COMMS_CHANNEL="none", COMMS_ALLOWLIST="")

def case_mail_host_unreachable(checkout):
	# A port nothing is listening on: on COMMS_CHANNEL=none this is the whole
	# outbound escalation path, and it fails silently in exactly this shape.
	with socket.socket() as probe:
		probe.bind(("127.0.0.1", 0))
		dead_port = probe.getsockname()[1]
	edit_env(checkout, COMMS_CHANNEL_ENDPOINT=f"127.0.0.1:{dead_port}")

def case_tracker_credential_rejected(checkout):
	edit_env(checkout, WORK_TRACKER_API_KEY="a-token-the-tracker-never-issued")

def case_tracker_base_url_unreachable(checkout):
	edit_env(checkout, WORK_TRACKER_BASE_URL="http://127.0.0.1:1")

def case_conventions_doc_missing(checkout):
	edit_env(checkout, CONVENTIONS_DOC_PATH="docs/conventions-that-were-never-written.md")

def case_product_repo_missing(checkout):
	edit_env(checkout, PRODUCT_REPO_PATH=str(checkout.parent / "a-repo-nobody-cloned"))

def case_product_repo_without_origin(checkout):
	git("remote", "remove", "origin", cwd=Path(read_env(checkout)["PRODUCT_REPO_PATH"]))

def case_internal_dashboard_none(checkout):
	"""No dashboard is a healthy deployment, not a half-configured one: the
	SKILL says not to build one speculatively, so the check has to stay quiet
	rather than nagging about an empty value."""
	edit_env(checkout, INTERNAL_DASHBOARD_PATH="")

def case_internal_dashboard_path_stale(checkout):
	# The project was moved or deleted and this variable kept its old value.
	# Nothing else on the box names the dashboard, so this is the only place
	# the loss is visible at all.
	edit_env(checkout, INTERNAL_DASHBOARD_PATH=str(checkout.parent / "a-dashboard-that-was-moved"))

def case_internal_dashboard_inside_product(checkout):
	# The standalone-project rule broken in the way it actually gets broken:
	# the scaffold copied into the product repo instead of next to it.
	product = Path(read_env(checkout)["PRODUCT_REPO_PATH"])
	nested = product / "ops-dashboard"
	shutil.move(str(checkout.parent / "dashboard"), str(nested))
	edit_env(checkout, INTERNAL_DASHBOARD_PATH=str(nested))

def case_internal_dashboard_unversioned(checkout):
	# A copy with no history anywhere above it: a warning rather than a
	# failure, since it serves fine and only rolls back badly.
	loose = checkout.parent / "loose-dashboard"
	loose.mkdir()
	(loose / "streamlit_app.py").write_text("# fixture dashboard\n", encoding="utf-8")
	edit_env(checkout, INTERNAL_DASHBOARD_PATH=str(loose))

def case_pipeline_specialized_without_prompts(checkout):
	# The fixture is specialized, so stages were decided — and then the file
	# a trigger would name isn't there. A cron line pointing at it fails with
	# nothing to read, or worse, the stage never fires and nobody notices.
	(checkout / "prompts" / "implement.md").unlink()

def case_stage_prompt_with_placeholders(checkout):
	(checkout / "prompts" / "implement.md").write_text(
		"# implement\n\nThe tracker state to move the item to is <ready-state>, and the test "
		"command is <test command>.\n",
		encoding="utf-8",
	)

def case_stage_prompt_verbatim_template(checkout):
	shutil.copyfile(checkout / "prompts" / "STAGE_TEMPLATE.md", checkout / "prompts" / "refine.md")

def case_harness_symlink_flattened(checkout):
	# What a "Download ZIP" copy of the template produces: the symlink becomes
	# a plain file holding its target's path, and every skill silently
	# disappears from the harness's view.
	link = checkout / ".claude" / "skills"
	target = os.readlink(link)
	link.unlink()
	link.write_text(target, encoding="utf-8")

def restub(checkout, name):
	"""Put one skill back the way the template ships it — heading, marker and
	index label all agreeing, so check-skills-consistency.py is satisfied and
	only the deployment-state question is left for the doctor."""
	skill = checkout / "skills" / name / "SKILL.md"
	skill.write_text(
		skill.read_text(encoding="utf-8").replace(
			f"\n# {name}\n",
			f"\n# {name}\n\n## Status: STUB — needs specialization\n\n## `TODO(specialize)`\n\n"
			"Blocked on something the owner still has to provision.\n",
			1,
		),
		encoding="utf-8",
	)
	index = checkout / "skills" / "README.md"
	index.write_text(
		index.read_text(encoding="utf-8").replace(
			f"[`{name}`](./{name}/SKILL.md) — ",
			f"[`{name}`](./{name}/SKILL.md) — *stub.* ",
			1,
		),
		encoding="utf-8",
	)

def case_skill_left_unspecialized(checkout):
	"""One stub left behind must warn and must not fail: specialize-skills
	allows a marker to outlive the pass where it is genuinely blocked on
	something the owner has to provision."""
	restub(checkout, "work-tracker")

def case_specialization_never_ran(checkout):
	"""The half-onboarded deployment: `.env` fully answered, every skill the
	pipeline depends on still generic template text. Everything about it looks
	configured, and no stage knows this deployment's own states or labels."""
	for name in ("work-tracker", "comms-channel", "work-pipeline"):
		restub(checkout, name)

def case_skills_index_drift(checkout):
	# The doctor does not own these rules; it runs the CI script that does.
	# Proving the delegation works matters as much as the rules themselves.
	(checkout / "skills" / "a-skill-nobody-indexed").mkdir()
	(checkout / "skills" / "a-skill-nobody-indexed" / "SKILL.md").write_text(
		"---\nname: a-skill-nobody-indexed\ndescription: fixture\n---\n\n# fixture\n",
		encoding="utf-8",
	)

def case_specialization_deleted_a_linked_file(checkout):
	"""The breakage a real specialization pass produces.

	skills/work-tracker/adapters/README.md's own instruction has the whole
	adapters/ directory deleted when the owner's tracker is none of the three
	it covers, and then every link that pointed there dealt with in the same
	pass. Miss one and a tracked doc points at a file that is gone. This is
	the deletion, without the link sites being dealt with — which is what a
	pass that stopped halfway actually leaves behind."""
	shutil.rmtree(checkout / "skills" / "work-tracker" / "adapters")

CASES = [
	# The baseline asserts one PASS by name as well as the absence of
	# failures: the fixture has a real dashboard project, and a check that
	# silently skipped it would look identical here otherwise.
	("healthy fixture", case_healthy, [("internal-dashboard", "PASS")], False),
	(".env missing", case_env_missing, [("env-file", "FAIL")], True),
	(".env world-readable", case_env_world_readable, [("env-permissions", "FAIL")], True),
	(".env committed to git", case_env_committed, [("env-not-tracked", "FAIL")], True),
	("required field blank", case_required_blank, [("env-required", "FAIL")], True),
	("placeholder secret", case_placeholder_value, [("env-required", "FAIL")], True),
	("angle-bracket placeholder", case_placeholder_angle_brackets, [("env-required", "FAIL")], True),
	("value outside oneof=", case_value_outside_oneof, [("env-required", "FAIL")], True),
	("key invented in .env", case_invented_key, [("env-schema", "FAIL")], True),
	("schema key absent from .env", case_key_absent_from_env, [("env-schema", "FAIL")], True),
	("malformed .env line", case_malformed_env_line, [("env-schema", "FAIL")], True),
	("schema key with no annotation", case_unannotated_schema_key, [("env-schema-annotations", "FAIL")], True),
	("origin still upstream", case_origin_still_upstream, [("git-origin", "FAIL")], True),
	("origin missing", case_origin_missing, [("git-origin", "FAIL")], True),
	("origin not pushable", case_origin_unpushable, [("git-push-access", "FAIL")], False),
	("installer guard unreadable", case_installer_guard_unreadable, [("git-origin", "FAIL")], True),
	(
		"allowlist empty on a verifying channel",
		case_allowlist_empty_on_verifying_channel,
		[("comms-allowlist", "FAIL")],
		True,
	),
	(
		"allowlist empty on COMMS_CHANNEL=none",
		case_allowlist_empty_on_channel_none,
		[("comms-allowlist", "PASS")],
		True,
	),
	("mail host unreachable", case_mail_host_unreachable, [("comms-channel-auth", "FAIL")], False),
	("tracker credential rejected", case_tracker_credential_rejected, [("work-tracker-auth", "FAIL")], False),
	("tracker host unreachable", case_tracker_base_url_unreachable, [("work-tracker-auth", "FAIL")], False),
	("conventions doc missing", case_conventions_doc_missing, [("conventions-doc", "FAIL")], True),
	("product repo missing", case_product_repo_missing, [("product-repo", "FAIL")], True),
	("product repo has no origin", case_product_repo_without_origin, [("product-repo", "FAIL")], True),
	(
		"no internal dashboard at all",
		case_internal_dashboard_none,
		[("internal-dashboard", "SKIP")],
		True,
	),
	(
		"dashboard path points at nothing",
		case_internal_dashboard_path_stale,
		[("internal-dashboard", "FAIL")],
		True,
	),
	(
		"dashboard project inside the product repo",
		case_internal_dashboard_inside_product,
		[("internal-dashboard", "FAIL")],
		True,
	),
	(
		"dashboard project under no version control",
		case_internal_dashboard_unversioned,
		[("internal-dashboard", "WARN")],
		True,
	),
	(
		"pipeline specialized with no stage prompts",
		case_pipeline_specialized_without_prompts,
		[("stage-prompts", "FAIL")],
		True,
	),
	(
		"one skill deliberately left a stub",
		case_skill_left_unspecialized,
		[("skills-specialization", "WARN"), ("skills-consistency", "PASS")],
		True,
	),
	(
		"specialization pass never ran",
		case_specialization_never_ran,
		[("skills-specialization", "FAIL")],
		True,
	),
	("stage prompt still full of placeholders", case_stage_prompt_with_placeholders, [("stage-prompts", "FAIL")], True),
	("stage prompt is the verbatim template", case_stage_prompt_verbatim_template, [("stage-prompts", "FAIL")], True),
	("harness symlink flattened to a file", case_harness_symlink_flattened, [("harness-symlinks", "FAIL")], True),
	("skill missing from the skills index", case_skills_index_drift, [("skills-consistency", "FAIL")], True),
	(
		"specialization deleted a file other docs link to",
		case_specialization_deleted_a_linked_file,
		[("doc-links", "FAIL")],
		True,
	),
]

def main():
	tracker_server, tracker_port = start_tracker_server()
	mail_listener, mail_port = start_mail_server()
	try:
		for name, mutate, expectations, offline in CASES:
			with tempfile.TemporaryDirectory(prefix="spoor-doctor-test-") as directory:
				checkout = build_fixture(Path(directory), tracker_port, mail_port)
				mutate(checkout)
				report, exit_code = run_doctor(checkout, offline)
				observed = statuses(report)

				for check_id, expected in expectations:
					actual = observed.get(check_id)
					if actual != expected:
						fail(
							name,
							f"expected {check_id} to be {expected}, got {actual or 'no such check'}"
							f" — {message_for(report, check_id) or 'no message'}",
						)

				expects_failure = any(status == "FAIL" for _, status in expectations)
				if expects_failure and exit_code == 0:
					fail(name, "the doctor exited 0 despite reporting a failure")
				if not expects_failure:
					# Either the healthy baseline, or a case asserting the
					# doctor correctly stays quiet. Nothing about the fixture
					# is broken, so nothing outside the host-dependent checks
					# may fail.
					unexpected = [
						f"{check_id} ({message_for(report, check_id)})"
						for check_id, status in observed.items()
						if status == "FAIL" and check_id not in HOST_DEPENDENT
					]
					if unexpected:
						fail(name, "unexpected failure(s) on an unbroken fixture: " + "; ".join(unexpected))
	finally:
		tracker_server.shutdown()
		mail_listener.close()

	if failures:
		print(f"FAIL: {len(failures)} of {len(CASES)} spoor-doctor case(s) did not behave:\n", file=sys.stderr)
		for message in failures:
			print(f"  - {message}", file=sys.stderr)
		return 1

	caught = sum(1 for _, _, expectations, _ in CASES if any(status == "FAIL" for _, status in expectations))
	print(
		f"OK: {DOCTOR} behaved correctly on all {len(CASES)} cases — {caught} injected break(s), each "
		f"caught by name with a non-zero exit, and {len(CASES) - caught} case(s) it correctly stayed "
		"quiet about."
	)
	return 0

if __name__ == "__main__":
	sys.exit(main())
