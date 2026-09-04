"""Run every page headlessly and fail on any exception one raises.

Streamlit ships its own headless harness, `AppTest`, which executes a page
script in-process and collects both the widgets it produced and any exception
it raised. That is the check worth having here: this app is client-rendered, so
an HTTP request for a page returns the same shell whether the page rendered or
blew up on the first line, and a status code proves only that the process is
alive.

Not part of the runtime image. `verify.sh` mounts this file into a throwaway
container from the built image, so it runs against exactly the code, uid and
mounts the real container has - which is where a page that works from a
checkout tends to fail.
"""

import sys

from streamlit.testing.v1 import AppTest

PAGES = [
	"app_pages/overview.py",
	"app_pages/containers.py",
	"app_pages/shipping.py",
]

# Generous, because a cold start pays for the Streamlit import and every page
# takes real readings - a `git log` over several checkouts is not instant.
TIMEOUT_SECONDS = 120

failed = False

for page in PAGES:
	app = AppTest.from_file(page, default_timeout=TIMEOUT_SECONDS)
	app.run()

	if app.exception:
		failed = True
		print(f"FAIL {page}")
		for exception in app.exception:
			print(f"    {exception.value}")
		continue

	# A page that rendered nothing at all is a failure too: every page here
	# either shows a reading or says out loud that it could not take one, and
	# both of those produce elements.
	counts = {
		name: len(getattr(app, name))
		for name in ("metric", "dataframe", "caption", "markdown", "warning", "info", "success")
	}
	rendered = {name: count for name, count in counts.items() if count}

	if not rendered:
		failed = True
		print(f"FAIL {page} — ran without error but rendered no elements")
		continue

	summary = ", ".join(f"{count} {name}" for name, count in rendered.items())
	print(f"OK   {page} — title {app.title[0].value!r}: {summary}")

	# The gaps a page admitted to, printed rather than counted. A page that
	# renders only "could not be checked" panels is passing this script and
	# still telling the reader nothing, and that has to be visible here.
	for warning in app.warning:
		print(f"     gap: {warning.value.splitlines()[0]}")

sys.exit(1 if failed else 0)
