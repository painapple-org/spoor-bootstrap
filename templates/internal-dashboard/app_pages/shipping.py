"""Shipping - what got committed, across every checkout this dashboard can see.

This is the page that answers "was anything actually shipped this week"
in one view, which nothing else on a box gives you without three commands
and some mental arithmetic.
"""

import pandas as pd
import streamlit as st

from dashboard import config, hostinfo, ui

st.title("Shipping")
st.caption("`git log` across every configured checkout, newest first.")

if not config.REPO_PATHS:
	st.info(
		"No checkouts are configured. Set `DASHBOARD_REPO_PATHS` to a colon-separated "
		"list of git checkouts and mount each one into this container read-only.",
		icon=":material/info:",
	)
	st.stop()

df, unreadable = hostinfo.load_commits(config.REPO_PATHS)

for path, reason in unreadable.items():
	ui.unavailable(f"Checkout {path}", reason)

if df.empty:
	st.warning(
		"Every readable checkout has no commits in it. That is a real reading, not a failure - "
		"but on a host that has been worked on it usually means the mounts point somewhere else "
		"than the checkouts do.",
		icon=":material/warning:",
	)
	st.stop()

window_days = st.segmented_control(
	"Window",
	[7, 14, 30, 90],
	default=config.DEFAULT_WINDOW_DAYS,
	format_func=lambda days: f"{days} days",
)
window_days = window_days or config.DEFAULT_WINDOW_DAYS
cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=window_days)
df_window = df.loc[df.Committed >= cutoff]

with st.container(horizontal=True):
	st.metric("Commits", len(df_window), f"in {window_days} days", border=True, delta_color="off")
	st.metric("Checkouts", df_window.Repo.nunique(), border=True)
	st.metric("Authors", df_window.Author.nunique(), border=True)
	busiest = df_window.Repo.value_counts()
	st.metric("Busiest checkout", busiest.index[0] if len(busiest) else "—", border=True)

with st.container(border=True):
	st.subheader("Commits per day")
	df_daily = hostinfo.commits_per_day(df_window)
	if df_daily.empty:
		st.caption("No commits in this window.")
	else:
		st.bar_chart(df_daily, stack=True, height=300)
	ui.source_note(
		f"one bar per calendar day in UTC, stacked by checkout, over the last {window_days} days"
	)

with st.container(border=True):
	st.subheader("Commits")

	picked = st.pills("Checkout", sorted(df_window.Repo.unique()), selection_mode="multi", default=None)
	df_view = df_window.loc[df_window.Repo.isin(picked)] if picked else df_window

	st.dataframe(
		df_view,
		hide_index=True,
		column_config={
			"Repo": st.column_config.TextColumn("Checkout", width="small"),
			"Sha": st.column_config.TextColumn("Sha", width="small"),
			"Author": st.column_config.TextColumn("Author", width="small"),
			"Committed": st.column_config.DatetimeColumn("Committed", format="D MMM YYYY HH:mm"),
			"Subject": st.column_config.TextColumn("Subject", width="large"),
		},
	)

	read_paths = ", ".join(f"`{path}`" for path in config.REPO_PATHS if str(path) not in unreadable)
	ui.source_note(f"{len(df_view)} commits from {read_paths}. Times are commit dates in UTC.")
