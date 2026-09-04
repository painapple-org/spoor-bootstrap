"""Entrypoint for the internal dashboard.

Three starter pages, each reading something genuinely live off this host, so
that a fresh copy of this template shows real state on the first run rather
than placeholder panels waiting to be filled in.

They are a starting point, not the page list. Replace them with the questions
this deployment's owner actually asks - `templates/internal-dashboard/README.md`
in the spoor-bootstrap repo is the home for how to do that, and
`skills/internal-dashboard/SKILL.md` for what makes a page worth having.
"""

import streamlit as st

from dashboard import config

st.set_page_config(
	page_title=config.TITLE,
	page_icon=":material/monitor_heart:",
	layout="wide",
)

page = st.navigation(
	{
		"": [
			st.Page("app_pages/overview.py", title="Overview", icon=":material/speed:", default=True),
		],
		"Host": [
			st.Page("app_pages/containers.py", title="Containers", icon=":material/deployed_code:"),
		],
		"Work": [
			st.Page("app_pages/shipping.py", title="Shipping", icon=":material/commit:"),
		],
	},
	position="sidebar",
)

with st.sidebar:
	st.caption("Everything on these pages is read live off this host.")

page.run()
