#!/usr/bin/env python3
#
# Test for ../../spoor-profile. Driven by the profile-generator job in
# ../workflows/ci.yml.
#
# The point of `spoor-profile` is that a business profile produces the same
# artifacts a live first-boot interview produces. That claim is only worth
# anything if something checks it, and there is exactly one place in this repo
# where the interview's output for a specific business is written down: the
# worked walkthroughs under ../../docs. So the load-bearing assertion here is
# an equivalence — the `.env` generated from ../../examples/northlight.toml
# has to match, key for key, the `.env`
# ../../docs/example-walkthrough.md shows the interview producing for the same
# business. The expected values are parsed out of that walkthrough rather than
# restated here, so the two cannot drift: a change to either side that breaks
# the equivalence fails this test instead of going unnoticed.
#
# Around that sit three other groups of case:
#
#   - **Every profile in ../../examples generates a valid deployment.** The
#     directory is globbed, not listed, so adding a profile gets it covered
#     for free. Each one is generated into a real fixture — a copy of this
#     checkout with its own git origin, plus a second repo standing in for the
#     product — and ../../spoor-doctor is then run against the result. A
#     generated deployment that the repo's own health check calls broken is a
#     broken generator, and nothing else in CI would notice.
#   - **The judgement boundary holds.** A profile that leaves a judgement field
#     out has to produce a `TODO(owner)` line naming it, and must *not* produce
#     a plausible answer or a settled deferral the profile contradicts. That
#     second half is a real failure mode with a real precedent: STARTUP.md's
#     conventions-doc step warns specifically against recording "nothing
#     internal exists yet, so nothing is set up" when the interview's
#     internal-tooling question came back yes.
#   - **An invalid profile is refused, loudly, having written nothing.** A
#     generator that silently drops a typo'd field, or accepts a secret, or
#     clobbers an existing `.env`, is worse than one that does not run.
#
# Nothing here contacts the network: the doctor is invoked with --offline, and
# every git remote is a bare repo in a temp directory.
#
# Run from anywhere; it locates the repo root relative to its own path.

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = "spoor-profile"
EXAMPLES = REPO_ROOT / "examples"
WALKTHROUGH = REPO_ROOT / "docs" / "example-walkthrough.md"
GOLDEN_PROFILE = EXAMPLES / "northlight.toml"

ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")

# Doctor checks whose verdict depends on the machine this runs on rather than
# on the generated deployment — whether the runner has docker/uv/gh and a
# reachable daemon, and whether it happens to be on a mesh VPN — plus the two
# that a correct first boot is *expected* to leave failing. Both of those are
# STARTUP.md's own documented end state rather than a generator bug: the secret
# fields are deliberately blank for the owner to paste in, and the
# specialization pass is the half of the flow this generator does not do.
HOST_DEPENDENT = ("host-tooling-docker", "host-tooling-uv", "host-tooling-gh", "private-networking")
EXPECTED_AFTER_GENERATION = ("env-required", "skills-specialization")

failures = []

def fail(case, message):
	failures.append(f"{case}: {message}")

# --- fixtures ---------------------------------------------------------------

def git(*arguments, cwd):
	subprocess.run(
		["git", *arguments],
		cwd=str(cwd),
		check=True,
		capture_output=True,
		text=True,
		env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_GLOBAL": "/dev/null"},
	)

def commit_all(repo, message):
	git("add", "-A", cwd=repo)
	git(
		"-c", "user.email=fixture@fixture.test",
		"-c", "user.name=Fixture",
		"commit", "-q", "-m", message,
		cwd=repo,
	)

def build_fixture(root, profile_path):
	"""A copy of this checkout with a git origin of its own, a repo standing in
	for the product, and the profile rewritten to point at it.

	The profiles name plausible production paths (`/home/spoor/...`), which do
	not exist on a runner. Rewriting `repo_path` in a copy of the profile is
	the one thing this test changes about the input: everything else — every
	answer, every deliberate blank — is exactly what ships in ../../examples."""
	checkout = root / "checkout"
	shutil.copytree(REPO_ROOT, checkout, symlinks=True, ignore=shutil.ignore_patterns(".git", ".env"))

	product = root / "product"
	product.mkdir()
	(product / "README.md").write_text("fixture product repo\n", encoding="utf-8")
	git("init", "-q", "-b", "main", ".", cwd=product)
	commit_all(product, "initial")
	git("init", "-q", "--bare", str(root / "product-origin.git"), cwd=root)
	git("remote", "add", "origin", str(root / "product-origin.git"), cwd=product)

	git("init", "-q", "-b", "main", ".", cwd=checkout)
	commit_all(checkout, "fixture checkout")
	git("init", "-q", "--bare", str(root / "checkout-origin.git"), cwd=root)
	git("remote", "add", "origin", str(root / "checkout-origin.git"), cwd=checkout)

	profile = root / "profile.toml"
	profile.write_text(
		re.sub(
			r'^repo_path = ".*"$',
			f'repo_path = "{product}"',
			profile_path.read_text(encoding="utf-8"),
			flags=re.MULTILINE,
		),
		encoding="utf-8",
	)
	return checkout, product, profile

def run_generator(checkout, *arguments):
	completed = subprocess.run(
		[sys.executable, str(checkout / GENERATOR), *arguments],
		cwd=str(checkout),
		capture_output=True,
		text=True,
		timeout=120,
	)
	return completed.returncode, completed.stdout + completed.stderr

def run_doctor(checkout):
	completed = subprocess.run(
		[sys.executable, str(checkout / "spoor-doctor"), "--offline", "--json"],
		cwd=str(checkout),
		capture_output=True,
		text=True,
		timeout=300,
	)
	try:
		return json.loads(completed.stdout), completed.returncode
	except ValueError:
		return None, completed.returncode

def conventions_doc_path(checkout, product):
	"""Where the generated conventions doc is, resolved the way the doctor
	resolves it: absolute as given, otherwise relative to PRODUCT_REPO_PATH.

	Not a glob over the product repo: that repo has a README.md in it as well,
	and directory order decides which one a glob returns — which passed locally
	and failed in a container, for no reason connected to the generator."""
	values = env_pairs((checkout / ".env").read_text(encoding="utf-8"))
	doc = Path(values.get("CONVENTIONS_DOC_PATH", ""))
	return doc if doc.is_absolute() else product / doc

def env_pairs(text):
	values = {}
	for raw in text.splitlines():
		line = raw.strip()
		if not line or line.startswith("#"):
			continue
		matched = ENV_LINE.match(line)
		if matched:
			values[matched.group(1)] = matched.group(2).strip()
	return values

def declared_keys(checkout):
	"""The keys .env.example declares, read the same way the doctor reads them."""
	return [
		matched.group(1)
		for matched in (
			ENV_LINE.match(line.strip())
			for line in (checkout / ".env.example").read_text(encoding="utf-8").splitlines()
		)
		if matched
	]

# --- case: every shipped profile generates a deployment the doctor accepts ---

def check_generated_deployment(name, checkout, product, profile):
	code, output = run_generator(checkout, str(profile))
	if code != 0:
		fail(name, f"generator exited {code}:\n{output}")
		return False

	env_path = checkout / ".env"
	if not env_path.is_file():
		fail(name, f"generator exited 0 but wrote no .env. Its report:\n{output}")
		return False

	mode = stat.S_IMODE(env_path.stat().st_mode)
	if mode != 0o600:
		fail(name, f".env was written mode {mode:04o}, not 0600")

	values = env_pairs(env_path.read_text(encoding="utf-8"))
	expected_keys = declared_keys(checkout)
	if sorted(values) != sorted(expected_keys):
		fail(
			name,
			"generated .env keys do not match .env.example: missing "
			f"{sorted(set(expected_keys) - set(values))}, invented "
			f"{sorted(set(values) - set(expected_keys))}",
		)

	for key in ("WORK_TRACKER_API_KEY", "COMMS_CHANNEL_TOKEN"):
		if values.get(key):
			fail(name, f"{key} holds a value; the generator must never write a secret")

	doc_path = conventions_doc_path(checkout, product)
	if not doc_path.is_file():
		fail(name, f"no conventions doc at {doc_path}")

	report, _ = run_doctor(checkout)
	if report is None:
		fail(name, "spoor-doctor produced no parseable JSON against the generated deployment")
		return True

	observed = {check["id"]: check["status"] for check in report["checks"]}
	unexpected = [
		f"{check['id']} ({check['message']})"
		for check in report["checks"]
		if check["status"] == "FAIL"
		and check["id"] not in HOST_DEPENDENT
		and check["id"] not in EXPECTED_AFTER_GENERATION
	]
	if unexpected:
		fail(name, "spoor-doctor failed the generated deployment: " + "; ".join(unexpected))

	for check_id in ("env-file", "env-permissions", "env-schema", "conventions-doc", "product-repo"):
		if observed.get(check_id) != "PASS":
			fail(name, f"expected {check_id} to PASS on the generated deployment, got {observed.get(check_id)}")

	# The one FAIL a correct first boot ends on, per STARTUP.md's own note: the
	# required-value check, on exactly the fields left blank on purpose. Any
	# *other* field in that failure is the generator's bug, which is the whole
	# reason this asserts the message rather than the status.
	required = next((c for c in report["checks"] if c["id"] == "env-required"), None)
	if required and required["status"] == "FAIL":
		message = required["message"]
		blank = {key for key, value in values.items() if not value}
		# Only the empty-but-required problems are expected. A placeholder, a
		# value outside a `oneof=`, or an unparseable spec would all also land
		# in this one message, and each of those is a generator bug — so the
		# problems are counted as well as matched, and a problem shaped any
		# other way is reported rather than passed over.
		empty = set(re.findall(r"\b([A-Z][A-Z0-9_]*) is empty but required\b", message))
		declared_count = int(re.match(r"(\d+) problem\(s\)", message).group(1))
		if not empty <= blank:
			fail(
				name,
				"env-required named field(s) as unanswered that are not blank in the generated "
				f".env: {sorted(empty - blank)} — {message}",
			)
		if len(empty) != declared_count:
			fail(
				name,
				f"env-required reported {declared_count} problem(s) but only {len(empty)} of them "
				f"are empty-but-required; the rest are generator bugs — {message}",
			)
	return True

# --- case: the generated .env matches the narrated interview's own ----------

def walkthrough_env():
	"""The `.env` docs/example-walkthrough.md shows the interview producing.

	Parsed out of the walkthrough rather than restated here: that file is the
	one home for what the interview produced for that business, and a copy of
	it in this script would be exactly the drift the equivalence is meant to
	catch."""
	blocks = [
		block for block in re.findall(r"```sh\n(.*?)```", WALKTHROUGH.read_text(encoding="utf-8"), re.S)
		if "PRODUCT_REPO_PATH=" in block
	]
	if len(blocks) != 1:
		return None, f"expected exactly one .env block in {WALKTHROUGH.name}, found {len(blocks)}"
	return env_pairs(blocks[0]), None

def check_matches_walkthrough(name, checkout, product):
	expected, problem = walkthrough_env()
	if problem:
		fail(name, problem)
		return
	generated = env_pairs((checkout / ".env").read_text(encoding="utf-8"))
	# The fixture rewrote this one, and only this one, to a path that exists.
	generated["PRODUCT_REPO_PATH"] = expected.get("PRODUCT_REPO_PATH", "")

	differing = [
		f"{key}: walkthrough says {expected[key]!r}, generator wrote {generated.get(key)!r}"
		for key in expected
		if expected[key] != generated.get(key)
	]
	if differing:
		fail(name, "generated .env diverges from the narrated interview's:\n    " + "\n    ".join(differing))
	if set(generated) != set(expected):
		fail(
			name,
			f"key sets differ: only in walkthrough {sorted(set(expected) - set(generated))}, "
			f"only in generated {sorted(set(generated) - set(expected))}",
		)

# --- case: the judgement boundary -------------------------------------------

def check_judgement_boundary(name, checkout, product, profile):
	"""kweekhuis.toml omits every autonomy field and asks for a dashboard.

	Two things have to be true of the doc it generates: a TODO(owner) line per
	omitted judgement field, and no settled deferral about private networking —
	that profile's own internal-tooling answer contradicts one."""
	doc = conventions_doc_path(checkout, product)
	if not doc.is_file():
		fail(name, f"no conventions doc at {doc} to inspect")
		return
	text = doc.read_text(encoding="utf-8")

	if "TODO(owner)" not in text:
		fail(name, "a profile with no [autonomy] table produced a doc with no TODO(owner) line")
	for phrase in (
		"what this deployment adds to the stop-and-ask list",
		"which named carve-outs may run unattended",
		"when this agent may not ship at all",
		"which private network anything internal is reached over",
	):
		if phrase not in text:
			fail(name, f"expected a TODO(owner) naming {phrase!r}; it is absent")

	if "nothing internal exists yet" in text:
		fail(
			name,
			"the doc records the settled 'nothing internal exists yet' deferral even though this "
			"profile asks for a dashboard — the exact thing STARTUP.md's conventions-doc step "
			"warns against",
		)

	_, output = run_generator(checkout, str(profile), "--json")
	try:
		deferred = json.loads(output)["report"]["deferred"]
	except (ValueError, KeyError):
		fail(name, "--json produced no parseable report")
		return
	if len(deferred) < 5:
		fail(name, f"only {len(deferred)} judgement call(s) reported as deferred; expected the whole table")

def check_no_invented_stack(name, checkout, product):
	"""basalt-metrics.toml has a technical end-user and no stack answer.

	That is the case where product-tech-stack does not apply, so a generator
	willing to guess would have nothing stopping it. The doc must say the
	decision is missing rather than make one."""
	doc = conventions_doc_path(checkout, product)
	if not doc.is_file():
		fail(name, f"no conventions doc at {doc} to inspect")
		return
	text = doc.read_text(encoding="utf-8")
	if "the product's stack is unrecorded" not in text:
		fail(name, "the unanswered stack decision is not reported as a TODO(owner)")
	if "**Stack:**" in text:
		fail(name, "the doc records a stack the profile never stated")

# --- case: an invalid profile is refused, having written nothing ------------

REFUSALS = [
	(
		"unknown field",
		lambda text: text.replace("[git]\n", "[git]\nbranch_prefix = \"spoor/\"\n"),
		"unknown field",
	),
	(
		"missing required field",
		lambda text: re.sub(r'^alert_target = .*$', "", text, flags=re.MULTILINE),
		"[comms].alert_target is required",
	),
	(
		"a secret named in the profile",
		lambda text: text.replace("[comms]\n", "[comms]\nCOMMS_CHANNEL_TOKEN = \"xoxb-real-token\"\n"),
		"names a secret",
	),
	(
		"a placeholder instead of an answer",
		lambda text: re.sub(r'^alert_target = .*$', 'alert_target = "TODO"', text, flags=re.MULTILINE),
		"placeholder",
	),
	(
		"a person who may instruct with no verified identity",
		lambda text: re.sub(r'^channel_identity = .*$', "", text, count=1, flags=re.MULTILINE),
		"channel_identity is required",
	),
	(
		"a deliberate exclusion with no reason",
		lambda text: re.sub(r'^excluded_because = .*$', "", text, count=1, flags=re.MULTILINE),
		"excluded_because is required",
	),
	(
		"a schema version this generator does not write",
		lambda text: text.replace("schema_version = 1", "schema_version = 99"),
		"schema_version",
	),
]

def check_refusals(root):
	source = GOLDEN_PROFILE.read_text(encoding="utf-8")
	for name, mutate, expected_phrase in REFUSALS:
		with tempfile.TemporaryDirectory(prefix="spoor-profile-refuse-", dir=root) as directory:
			checkout, _, profile = build_fixture(Path(directory), GOLDEN_PROFILE)
			profile.write_text(mutate(source), encoding="utf-8")
			code, output = run_generator(checkout, str(profile))
			case = f"refuses: {name}"
			if code == 0:
				fail(case, f"generator exited 0 on an invalid profile:\n{output}")
			if expected_phrase not in output:
				fail(case, f"the refusal never mentions {expected_phrase!r}:\n{output}")
			if (checkout / ".env").exists():
				fail(case, "an invalid profile still produced a .env")

def check_does_not_clobber(root):
	"""An existing `.env` keeps its contents and gets its mode narrowed.

	STARTUP.md step 4 is explicit about both halves for the interview, and the
	mode half is the one that is easy to get wrong: leaving the contents alone
	does not mean leaving the mode alone."""
	case = "leaves an existing .env alone but narrows its mode"
	with tempfile.TemporaryDirectory(prefix="spoor-profile-existing-", dir=root) as directory:
		checkout, _, profile = build_fixture(Path(directory), GOLDEN_PROFILE)
		env_path = checkout / ".env"
		env_path.write_text("PRODUCT_REPO_PATH=/somewhere/a/human/typed\n", encoding="utf-8")
		env_path.chmod(0o644)

		code, output = run_generator(checkout, str(profile))
		if code != 0:
			fail(case, f"generator exited {code} rather than reporting the existing file:\n{output}")
		if env_path.read_text(encoding="utf-8") != "PRODUCT_REPO_PATH=/somewhere/a/human/typed\n":
			fail(case, "the existing .env's contents were overwritten")
		mode = stat.S_IMODE(env_path.stat().st_mode)
		if mode != 0o600:
			fail(case, f"the existing .env was left mode {mode:04o}; it should be narrowed to 0600")
		if "already existed" not in output:
			fail(case, f"the report never says the file was left alone:\n{output}")

def check_dry_run_writes_nothing(root):
	case = "--dry-run writes nothing"
	with tempfile.TemporaryDirectory(prefix="spoor-profile-dry-", dir=root) as directory:
		checkout, product, profile = build_fixture(Path(directory), GOLDEN_PROFILE)
		code, output = run_generator(checkout, str(profile), "--dry-run")
		if code != 0:
			fail(case, f"generator exited {code}:\n{output}")
		if (checkout / ".env").exists():
			fail(case, "--dry-run created a .env")
		if list(product.glob("AGENTS.md")):
			fail(case, "--dry-run created the conventions doc")

# --- driver -----------------------------------------------------------------

def main():
	profiles = sorted(EXAMPLES.glob("*.toml"))
	if not profiles:
		print(f"FAIL: no profiles found in {EXAMPLES.relative_to(REPO_ROOT)}", file=sys.stderr)
		return 1
	if GOLDEN_PROFILE not in profiles:
		print(f"FAIL: {GOLDEN_PROFILE.name} is missing, and it is the one checked against the "
		      f"narrated walkthrough", file=sys.stderr)
		return 1

	with tempfile.TemporaryDirectory(prefix="spoor-profile-test-") as outer:
		for profile_path in profiles:
			name = profile_path.stem
			with tempfile.TemporaryDirectory(prefix=f"{name}-", dir=outer) as directory:
				checkout, product, profile = build_fixture(Path(directory), profile_path)
				if not check_generated_deployment(name, checkout, product, profile):
					continue
				if profile_path == GOLDEN_PROFILE:
					check_matches_walkthrough(f"{name}: matches the narrated interview", checkout, product)
				if name == "kweekhuis":
					check_judgement_boundary(f"{name}: judgement boundary", checkout, product, profile)
				if name == "basalt-metrics":
					check_no_invented_stack(f"{name}: no invented stack", checkout, product)

		check_refusals(Path(outer))
		check_does_not_clobber(Path(outer))
		check_dry_run_writes_nothing(Path(outer))

	if failures:
		print(f"FAIL: {len(failures)} spoor-profile problem(s):\n", file=sys.stderr)
		for message in failures:
			print(f"  - {message}", file=sys.stderr)
		return 1

	print(
		f"OK: {len(profiles)} shipped profile(s) each generated a .env and a conventions doc "
		f"spoor-doctor accepts, the profile behind {WALKTHROUGH.name} reproduced that "
		f"walkthrough's own .env key for key, the judgement boundary held on a profile that leaves "
		f"it open, and {len(REFUSALS)} invalid profile(s) were each refused without writing anything."
	)
	return 0

if __name__ == "__main__":
	sys.exit(main())
