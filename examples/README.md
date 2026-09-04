# examples/

Filled-in business profiles for [`../spoor-profile`](../spoor-profile), the
non-interactive path through the first-boot flow.
[`../docs/non-interactive-onboarding.md`](../docs/non-interactive-onboarding.md)
is the one home for what that path is and when to use it, and
[`../profile.example.toml`](../profile.example.toml) is the one home for the
format and what each field means. Neither is restated here.

**None of these is a default.** They are fictional businesses picked to differ
from each other on every axis that changes the flow's behaviour, the same way
the narrated walkthroughs — [`../docs/example-walkthrough.md`](../docs/example-walkthrough.md),
[`../docs/example-walkthrough-solo.md`](../docs/example-walkthrough-solo.md) and
[`../docs/example-walkthrough-existing-process.md`](../docs/example-walkthrough-existing-process.md)
— are. Each file's own header says which shape it exercises and why.

## Current profiles

- [`northlight.toml`](./northlight.toml) — the profile behind
  [`../docs/example-walkthrough.md`](../docs/example-walkthrough.md), and the
  one that is checked rather than read: `.github/ci/test-profile.py` asserts
  the `.env` generated from it matches the one that walkthrough shows the
  interview producing, key for key, reading the expected values out of the
  walkthrough itself. Existing unmaintained repo, GitHub Issues, Slack, a
  non-technical owner, paying customers, and every judgement field answered.
- [`kweekhuis.toml`](./kweekhuis.toml) — the same format with the judgement
  deliberately left out: no `[autonomy]` table at all, no pipeline stage set,
  no decision on the private network for the dashboard the owners asked for.
  Generates a conventions doc that is nine explicit `TODO(owner)` lines where
  those answers belong. Also the remote shape with no git hosting account: a
  bare repo on the box, so no PR mechanism at all.
- [`basalt-metrics.toml`](./basalt-metrics.toml) — one technical person, a
  technical end-user (so the mandated stack does not apply and the stack
  becomes a real decision, left unanswered), Jira Cloud, Discord, and a
  greenfield repo. Exercises the conditional `.env` fields from the other
  side: `WORK_TRACKER=jira` makes `WORK_TRACKER_BASE_URL` required.

## Adding one

Write the profile, put a header on it saying which shape it exercises that the
existing ones do not, and add it to the list above. `.github/ci/test-profile.py`
globs this directory, so a new profile is generated, doctored and asserted on in
CI without touching that script — which is the point of the profiles being data
rather than test code.
