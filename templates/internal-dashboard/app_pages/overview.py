"""Overview - the one screen that answers "is this box healthy right now".

Everything on it is measured at page load. Replace it with this deployment's
own first question; the shape to keep is a small number of large numbers, each
with its source named underneath.
"""

import pandas as pd
import streamlit as st

from dashboard import config, hostinfo, ui

st.title(config.TITLE)
st.caption(
	"Every number on this page was read off this host when the page loaded. "
	"Nothing here is generated, cached or estimated."
)

with st.container(border=True):
	st.subheader("Disk")

	try:
		usage = hostinfo.disk_usage(config.DISK_PATH)
	except OSError as exc:
		ui.unavailable(f"Disk usage of {config.DISK_PATH}", str(exc))
	else:
		with st.container(horizontal=True):
			st.metric("Total", f"{usage['TotalGiB']} GiB", border=True)
			st.metric("Used", f"{usage['UsedGiB']} GiB", f"{usage['UsedPct']}%", border=True, delta_color="off")
			st.metric("Free", f"{usage['FreeGiB']} GiB", border=True)
		st.progress(usage["UsedPct"] / 100)
		ui.source_note(f"`shutil.disk_usage` on `{config.DISK_PATH}`, inside this container")

with st.container(border=True):
	st.subheader("Containers")

	socket_path = config.docker_socket()
	if socket_path is None:
		st.info(
			"No container-runtime socket is configured, so this panel is off rather than empty. "
			"Set `DASHBOARD_DOCKER_SOCKET_PATH` and mount the socket read-only to turn it on.",
			icon=":material/info:",
		)
	elif not socket_path.exists():
		ui.unavailable(
			"Running containers",
			f"{socket_path} is not present in this container - it has to be bind-mounted in, read-only.",
		)
	else:
		try:
			df_containers = hostinfo.load_containers(socket_path)
		except (OSError, RuntimeError, ValueError) as exc:
			ui.unavailable("Running containers", str(exc))
		else:
			healthy = df_containers.Status.str.contains("healthy", case=False, na=False).sum()
			unhealthy = df_containers.Status.str.contains("unhealthy", case=False, na=False).sum()
			with st.container(horizontal=True):
				st.metric("Running", len(df_containers), border=True)
				st.metric("Reporting healthy", int(healthy - unhealthy), border=True)
				st.metric("Reporting unhealthy", int(unhealthy), border=True)
			ui.source_note(
				f"container-runtime API `/{hostinfo.DOCKER_API_VERSION}/containers/json` over `{socket_path}`. "
				"Health counts only include containers that define a healthcheck at all."
			)

with st.container(border=True):
	st.subheader("Shipping")

	if not config.REPO_PATHS:
		st.info(
			"No checkouts are configured, so this panel is off rather than empty. "
			"Set `DASHBOARD_REPO_PATHS` to a colon-separated list of git checkouts to turn it on.",
			icon=":material/info:",
		)
	else:
		df_commits, unreadable = hostinfo.load_commits(config.REPO_PATHS)
		window = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
		df_week = df_commits.loc[df_commits.Committed >= window] if not df_commits.empty else df_commits

		with st.container(horizontal=True):
			st.metric("Commits, last 7 days", len(df_week), border=True)
			st.metric("Checkouts read", len(config.REPO_PATHS) - len(unreadable), border=True)
			last = df_commits.Committed.max() if not df_commits.empty else None
			st.metric("Most recent commit", last.strftime("%d %b %H:%M") if last is not None else "—", border=True)

		ui.source_note("`git log` in each checkout in `DASHBOARD_REPO_PATHS`, times in UTC")

		for path, reason in unreadable.items():
			ui.unavailable(f"Checkout {path}", reason)
