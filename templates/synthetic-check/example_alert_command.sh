#!/usr/bin/env bash
#
# The shape of a SYNTHETIC_ALERT_COMMAND, and the one `verify.sh` uses so it
# can assert that an alert was sent - and, just as importantly, that a passing
# run sends nothing.
#
# The contract the runner expects of whatever this variable names:
#
#   - the report arrives on stdin,
#   - the kind of alert ("failure" or "recovery") arrives as the last argument,
#   - a non-zero exit means the alert was not delivered, and the runner treats
#     that as a failure of its own rather than exiting 0 having told nobody.
#
# On a real deployment this is replaced by whatever sends to this deployment's
# single alert destination. What that destination is, who may be told what, and
# how a message to the owner should read are all `skills/comms-channel`'s, via
# `skills/synthetic-monitoring/SKILL.md`'s alerting section - deliberately not
# restated here, because a second answer to "where do alerts go" is how a
# deployment ends up with two.

set -euo pipefail

kind="${1:?the runner passes the alert kind as the last argument}"
destination="${SYNTHETIC_ALERT_LOG:?set SYNTHETIC_ALERT_LOG to a file path for this example}"

{
	printf 'kind=%s\n' "$kind"
	cat
	printf -- '---\n'
} >>"$destination"
