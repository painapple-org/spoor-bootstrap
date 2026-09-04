"""The two things every page on this dashboard has to be able to say.

Both exist so that the honesty rules in `skills/internal-dashboard/SKILL.md`
are something a page gets for free rather than something each page has to
remember:

- `source_note` shows the reader where a number came from, so a wrong number is
  debuggable rather than merely wrong.
- `unavailable` renders a reading that could not be taken *as* a reading that
  could not be taken - never as a zero, an empty table, or a negative finding.

Keep using them as pages are added. A page that shows a number with no source
and no failure path is the one that eventually costs the whole surface its
credibility.
"""

import streamlit as st


def source_note(description: str) -> None:
	"""Say where the panel above this line got its numbers.

	Name the path read, the command run, or the time window - the thing a
	reader would have to go and look at to check the number by hand.
	"""
	st.caption(f":material/database: {description}")


def unavailable(what: str, reason: str) -> None:
	"""Report a reading this process could not take, without implying a result.

	`what` names the check, `reason` is the actual error text. Nothing here
	guesses at what the answer would have been.
	"""
	st.warning(f"**{what}** could not be checked here.", icon=":material/help:")
	st.code(reason, language=None)
