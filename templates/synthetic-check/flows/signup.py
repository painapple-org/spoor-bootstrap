# One flow, and the worked example of the contract every flow in this
# directory implements. Copy this file, keep the four parts, and replace what
# they talk to.
#
# The four parts, and why each is separate:
#
#   NAME      what an alert leads with, so it is the flow's user-facing name
#             ("checkout", "signup"), not the module's.
#   trigger   does what a user does, through the same public interface a user
#             uses. Returns a receipt: whatever `prove` and `cleanup` need to
#             find the specific thing this run created.
#   prove     asserts the side effect exists, by reading it back from where it
#             actually landed. Yields (name, detail) pairs so a passing run
#             says what it proved rather than only that it passed - a check
#             whose passing output is the word "ok" cannot be reviewed.
#   cleanup   removes exactly this run's test data, then confirms it is gone.
#
# What makes this a real check rather than an uptime ping is entirely in
# `prove`: it never looks at the status code of the trigger and stops there.
# `skills/synthetic-monitoring/SKILL.md` is the home for that rule and for the
# fault-injection test that keeps a flow honest about it.

from run_checks import CheckFailure

NAME = "signup"

# A user-visible budget, not a machine one: a signup that works but takes this
# long is broken for the person doing it. Chosen for the toy product; a real
# flow's number comes from what its own users actually experience, and it
# belongs in this file next to the flow it governs rather than in a shared
# constant nothing reads.
MAX_SECONDS = 5.0


def trigger(context):
	email = context.test_email(NAME)

	# Read the analytics number *before* the flow runs, so `prove` can assert
	# the product excluded this signup from it. Test data reaching the
	# business's own numbers is the pollution failure that no amount of
	# after-the-fact cleanup catches, because a counter is read long before a
	# row is deleted.
	status, stats = context.request("GET", "/stats")
	if status != 200:
		raise CheckFailure("stats-readable", f"GET /stats answered {status}: {stats}")
	real_signups_before = stats["real_signups"]

	status, body = context.request(
		"POST", "/signup", body={"email": email, "name": f"Synthetic Check {context.run_id}"}
	)
	if status != 201:
		raise CheckFailure("submit-accepted", f"POST /signup answered {status}: {body}")

	return {"email": email, "real_signups_before": real_signups_before}


def prove(context, receipt):
	email = receipt["email"]

	status, body = context.request("GET", "/internal/signups", params={"email": email}, evidence=True)
	if status != 200:
		raise CheckFailure("row-persisted", f"evidence read answered {status}: {body}")
	rows = body["rows"]
	if not rows:
		# The failure the whole pattern exists to catch: the submit was
		# accepted, and nothing was stored.
		raise CheckFailure("row-persisted", f"POST /signup returned 201 but no row exists for {email}")
	if len(rows) > 1:
		raise CheckFailure("row-persisted", f"{len(rows)} rows exist for a single submission of {email}")
	row = rows[0]
	yield "row-persisted", f"signups row {row['id']} for {email}"

	if not row["is_synthetic"]:
		raise CheckFailure(
			"marked-as-synthetic",
			f"row {row['id']} is not flagged synthetic - the product no longer recognizes the marker, "
			"so this check's data is indistinguishable from a real user's",
		)
	yield "marked-as-synthetic", f"row {row['id']} carries the synthetic flag"

	status, body = context.request("GET", "/internal/outbox", params={"about": email}, evidence=True)
	if status != 200:
		raise CheckFailure("notification-sent", f"outbox read answered {status}: {body}")
	messages = body["messages"]
	if not messages:
		raise CheckFailure(
			"notification-sent",
			f"the row was written but no notification about {email} was sent - a signup nobody is told about",
		)
	yield "notification-sent", f"{len(messages)} notification(s) to {messages[0]['to']}"

	status, stats = context.request("GET", "/stats")
	if status != 200:
		raise CheckFailure("excluded-from-analytics", f"GET /stats answered {status}: {stats}")
	if stats["real_signups"] != receipt["real_signups_before"]:
		raise CheckFailure(
			"excluded-from-analytics",
			f"real_signups moved from {receipt['real_signups_before']} to {stats['real_signups']} - "
			"this check is being counted as a real user",
		)
	yield "excluded-from-analytics", f"real_signups stayed at {stats['real_signups']}"


def cleanup(context, receipt):
	email = receipt["email"]
	status, body = context.request("POST", "/internal/purge", body={"email": email}, evidence=True)
	if status != 200:
		raise CheckFailure("purge-accepted", f"purge answered {status}: {body}")

	# Confirmed, not assumed. A purge endpoint that answers 200 having deleted
	# nothing is the same class of lie as the 201 above, and it fails in the
	# direction of test data quietly accumulating in production.
	status, after = context.request("GET", "/internal/signups", params={"email": email}, evidence=True)
	if status != 200 or after["rows"]:
		raise CheckFailure("purge-verified", f"rows still exist for {email} after purge: {after}")
	return f"purged {body['deleted_rows']} row(s) for {email}, verified gone"
