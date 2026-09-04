#!/usr/bin/env python3
#
# Checks the internal consistency of skills/ and the docs that index it, so a
# category of drift that until now only ever got caught by a human (or an
# agent) reading every file by eye fails CI instead. Driven by the
# skills-consistency job in ../workflows/ci.yml.
#
# Every rule below exists because it is a real bug in this repo's own terms,
# not a style preference:
#
#   1. A SKILL.md's `## Status:` heading is the file's own self-report of
#      whether it still needs specializing. specialize-skills tells the agent
#      to drop that heading once no TODO(specialize) markers remain, so a file
#      carrying markers with no heading, or a heading with no markers, is a
#      file lying about itself.
#   2. skills/README.md's "Current skills" list calls itself the one
#      enumeration of what exists under skills/. An entry with no directory, or
#      a directory with no entry, breaks that claim.
#   3. That list also labels each entry *stub* / *partial stub*, and says its
#      order must match specialize-skills' own numbered pass order. Both go
#      stale silently when a skill is specialized or added.
#   4. Cross-file references written as "STARTUP.md step N" or
#      "FILE.md's "Some Heading"" point at a specific place in another file.
#      Renumbering a step list or renaming a heading leaves every such
#      reference confidently wrong, and the links job can't see it: the link
#      itself still resolves, only the thing it says about the target is false.
#
# Nothing here is hardcoded to today's skill list — the skill set, the stub
# labels, the pass order and the reference targets are all read off disk.
#
# Run from anywhere; it locates the repo root relative to its own path.

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
SKILLS_INDEX = SKILLS_DIR / "README.md"
SPECIALIZE_SKILL = SKILLS_DIR / "specialize-skills" / "SKILL.md"

# Files that carry cross-references into other files' step lists and headings.
# skills/ is globbed rather than listed so a new skill is covered for free.
CROSSREF_ROOTS = ["STARTUP.md", "AGENTS.md", "CLAUDE.md", "README.md"]

failures = []

def fail(message):
	# Deduplicated: the same reference often appears more than once in one
	# file, and reporting it twice says nothing the first line didn't.
	if message not in failures:
		failures.append(message)

def flatten(text):
	"""Collapse newlines so a reference broken across a wrapped line still matches."""
	return re.sub(r"\s+", " ", text)

# A `TODO(specialize)` occurrence is only an actual unanswered gap when it
# introduces one: as a heading of its own, or immediately followed by the colon
# or em dash that starts the instruction. The same string also appears in prose
# that merely talks about the convention ("everything marked `TODO(specialize)`
# below", "for each `TODO(specialize)` marker"), most of all in
# specialize-skills itself, which documents the marker without carrying one.
# Treating those as gaps would make this check unpassable for the one file
# whose whole job is to explain them.
MARKER = r"`TODO\(specialize\)`"
ACTIONABLE_MARKER = re.compile(
	rf"(?:^#{{1,6}}\s*{MARKER}\s*$)|(?:{MARKER}\s*(?::|—))",
	re.MULTILINE,
)

STATUS_HEADING = re.compile(r"^#{1,6}\s*Status:\s*(.+?)\s*$", re.MULTILINE)

def status_value(text):
	"""The `## Status: X — ...` heading's claim, normalized, or None if absent."""
	match = STATUS_HEADING.search(text)
	if not match:
		return None
	return match.group(1).split("—")[0].split(" - ")[0].strip().lower()

def read(path):
	return path.read_text(encoding="utf-8")

# --- the skills on disk -----------------------------------------------------

skill_dirs = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
if not skill_dirs:
	fail(f"no skill directories found under {SKILLS_DIR.relative_to(REPO_ROOT)}")

skill_text = {}
for name in skill_dirs:
	skill_file = SKILLS_DIR / name / "SKILL.md"
	if not skill_file.is_file():
		fail(f"skills/{name}/ has no SKILL.md — every skill directory must define one")
		continue
	skill_text[name] = read(skill_file)

# --- 1. Status heading vs. the markers actually in the file -----------------

has_markers = {}
for name, text in skill_text.items():
	markers = ACTIONABLE_MARKER.findall(text)
	has_markers[name] = bool(markers)
	status = status_value(text)
	if markers and status is None:
		fail(
			f"skills/{name}/SKILL.md carries {len(markers)} TODO(specialize) marker(s) "
			"but has no `## Status:` heading saying so"
		)
	elif not markers and status is not None:
		fail(
			f"skills/{name}/SKILL.md has a `## Status: {status}` heading but no "
			"TODO(specialize) markers left — specialize-skills says to drop the heading "
			"once the file is finished"
		)

# --- 2 & 3. skills/README.md's "Current skills" index ------------------------

index_text = read(SKILLS_INDEX)
current_skills_section = re.search(
	r"^##\s*Current skills\s*$(.*?)(?=^##\s|\Z)", index_text, re.MULTILINE | re.DOTALL
)
if not current_skills_section:
	fail("skills/README.md has no '## Current skills' section to check the index against")
	indexed = []
else:
	# One entry per top-level bullet; an entry's identity is its first link,
	# which by this list's convention points at that skill's own SKILL.md.
	# Later links in the same bullet are cross-references to other skills.
	entries = re.findall(
		r"^- (.*?)(?=^- |\Z)", current_skills_section.group(1), re.MULTILINE | re.DOTALL
	)
	indexed = []
	for entry in entries:
		link = re.search(r"\]\(\./([^/)]+)/SKILL\.md\)", entry)
		if not link:
			fail(
				"skills/README.md 'Current skills' has an entry with no ./<skill>/SKILL.md "
				f"link: {flatten(entry)[:80]!r}"
			)
			continue
		flat = flatten(entry)
		label = None
		if re.search(r"\*partial stub\.?\*", flat, re.IGNORECASE):
			label = "partial stub"
		elif re.search(r"\*stub\.?\*", flat, re.IGNORECASE):
			label = "stub"
		indexed.append((link.group(1), label))

indexed_names = [name for name, _ in indexed]

for name in indexed_names:
	if name not in skill_dirs:
		fail(f"skills/README.md lists '{name}' but skills/{name}/ does not exist on disk")
for name in skill_dirs:
	if name not in indexed_names:
		fail(
			f"skills/{name}/ exists on disk but is not listed in skills/README.md's "
			"'Current skills' — that list is meant to be the one enumeration of this directory"
		)

duplicates = {n for n in indexed_names if indexed_names.count(n) > 1}
for name in sorted(duplicates):
	fail(f"skills/README.md lists '{name}' more than once in 'Current skills'")

# The index's own *stub* / *partial stub* labels have to agree with what the
# SKILL files say about themselves, which check 1 has already tied to the
# markers. Comparing to the Status heading rather than to the marker count
# keeps 'partial stub' meaningful — markers alone can't tell the two apart.
for name, label in indexed:
	if name not in skill_text:
		continue
	status = status_value(skill_text[name])
	if label != status:
		fail(
			f"skills/README.md labels '{name}' as "
			f"{('*' + label + '*') if label else 'finished (no stub label)'} but "
			f"skills/{name}/SKILL.md says "
			f"{('`Status: ' + status + '`') if status else 'nothing (no Status heading)'}"
		)

# --- 3. pass order, as specialize-skills defines it -------------------------

specialize_text = read(SPECIALIZE_SKILL)
pass_section = re.search(
	r"^##\s*The stubs to specialize\s*$(.*?)(?=^##\s|\Z)",
	specialize_text,
	re.MULTILINE | re.DOTALL,
)
if not pass_section:
	fail(
		"skills/specialize-skills/SKILL.md has no '## The stubs to specialize' section — "
		"that numbered list is where the pass order lives"
	)
	pass_order = []
else:
	numbered = re.findall(
		r"^(\d+)\.\s+\[`[^`]+`\]\(\.\./([^/)]+)/SKILL\.md\)",
		pass_section.group(1),
		re.MULTILINE,
	)
	seen_numbers = [int(n) for n, _ in numbered]
	if seen_numbers != list(range(1, len(seen_numbers) + 1)):
		fail(
			"skills/specialize-skills/SKILL.md's pass list is not numbered 1..N "
			f"contiguously: {seen_numbers}"
		)
	pass_order = [name for _, name in numbered]
	for name in pass_order:
		if name not in skill_dirs:
			fail(
				f"skills/specialize-skills/SKILL.md's pass list includes '{name}', "
				"which is not a directory under skills/"
			)

# A skill with unanswered markers has to be an item of the pass, or nothing
# will ever go and answer them.
for name in sorted(n for n, markers in has_markers.items() if markers):
	if name not in pass_order:
		fail(
			f"skills/{name}/SKILL.md still carries TODO(specialize) markers but is not an "
			"item in skills/specialize-skills/SKILL.md's 'The stubs to specialize' list"
		)

# The index carries finished skills too, and puts them where they read best
# rather than at their pass position, so only the stub entries' relative order
# is claimed to match the pass. That is exactly what skills/README.md promises
# ("The stubs below are listed in the order the specialization pass works
# through them"), so it is what gets checked.
index_stub_order = [n for n, label in indexed if label is not None]
expected = [n for n in pass_order if n in index_stub_order]
if index_stub_order != expected:
	fail(
		"skills/README.md's 'Current skills' lists the stubs in a different order than "
		"skills/specialize-skills/SKILL.md's pass list:\n"
		f"    README:            {index_stub_order}\n"
		f"    specialize-skills: {expected}"
	)

# --- 4. cross-references into another file's steps and headings -------------

crossref_files = [REPO_ROOT / name for name in CROSSREF_ROOTS if (REPO_ROOT / name).is_file()]
crossref_files += sorted(SKILLS_DIR.rglob("*.md"))

# "[`STARTUP.md`](../../STARTUP.md) step 5", "`STARTUP.md` step 5" — the file
# name, then at most a link target and a couple of characters of markdown, then
# the step number.
STEP_REF = re.compile(r"([A-Za-z0-9_./-]+\.md)`?\)?[^.]{0,3}?\bstep (\d+)\b")
# "[`README.md`](../../README.md)'s "Path to a running instance""
SECTION_REF = re.compile(r"([A-Za-z0-9_./-]+\.md)`?\)?'s \"([^\"]{3,80})\"")

TOP_LEVEL_STEP = re.compile(r"^(\d+)\.\s", re.MULTILINE)
HEADING = re.compile(r"^#{1,6}\s*(.+?)\s*$", re.MULTILINE)
BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)

def normalize_heading(value):
	"""Compare heading text ignoring markdown emphasis and backticks."""
	return re.sub(r"[`*_]", "", value).strip().lower()

def resolve(referrer, target):
	"""A reference names its target the way a link does — relative to the referring file."""
	for candidate in (referrer.parent / target, REPO_ROOT / target):
		resolved = candidate.resolve()
		if resolved.is_file():
			return resolved
	return None

target_cache = {}

def target_facts(path):
	"""The numbered steps, headings and bolded phrases a reference can name."""
	if path not in target_cache:
		text = read(path)
		# Bold spans are matched too because a reference sometimes names a
		# bolded bullet rather than a heading (AGENTS.md's guardrail list is
		# written that way), and the point of this check is a reference to
		# something that no longer exists — not a rule about what may be cited.
		target_cache[path] = (
			{int(n) for n in TOP_LEVEL_STEP.findall(text)},
			{normalize_heading(h) for h in HEADING.findall(text)},
			{normalize_heading(b) for b in BOLD.findall(flatten(text))},
		)
	return target_cache[path]

def names_something_real(section, headings, bolds):
	# A reference is allowed to cite a heading by its leading clause —
	# "AGENTS.md's "Default guardrails"" for a heading that continues
	# ": what you stop and ask about" — so a prefix match counts. A rename
	# still fails, which is the regression being guarded against.
	wanted = normalize_heading(section).rstrip(".,;:")
	if any(h == wanted or h.startswith(wanted) for h in headings):
		return True
	return any(b == wanted or b.startswith(wanted) for b in bolds)

for path in crossref_files:
	if path.is_symlink():
		continue
	text = flatten(read(path))
	here = path.relative_to(REPO_ROOT)

	for target, step in STEP_REF.findall(text):
		resolved = resolve(path, target)
		if resolved is None:
			fail(f"{here} refers to '{target} step {step}' but {target} does not exist")
			continue
		steps, _, _ = target_facts(resolved)
		if int(step) not in steps:
			fail(
				f"{here} refers to '{target} step {step}' but "
				f"{resolved.relative_to(REPO_ROOT)} has no top-level numbered item {step} "
				f"(it has {sorted(steps) if steps else 'no numbered list'})"
			)

	for target, section in SECTION_REF.findall(text):
		resolved = resolve(path, target)
		if resolved is None:
			fail(f"{here} refers to {target}'s \"{section}\" but {target} does not exist")
			continue
		_, headings, bolds = target_facts(resolved)
		if not names_something_real(section, headings, bolds):
			fail(
				f"{here} refers to {target}'s \"{section}\" but "
				f"{resolved.relative_to(REPO_ROOT)} has no heading or bolded phrase "
				"by that name"
			)

# --- result -----------------------------------------------------------------

if failures:
	print(f"FAIL: {len(failures)} skills-consistency problem(s):\n", file=sys.stderr)
	for message in failures:
		print(f"  - {message}", file=sys.stderr)
	sys.exit(1)

print(
	f"OK: {len(skill_dirs)} skill directories, all indexed in skills/README.md, "
	"stub labels and Status headings agree with their TODO(specialize) markers, "
	"index order matches the specialize-skills pass order, and every step/section "
	"cross-reference resolves."
)
