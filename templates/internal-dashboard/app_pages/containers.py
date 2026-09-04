"""Containers - what is actually running on this host, straight from the runtime API.

The interesting property of this page is not the table, it is that a missing
socket, a permission error and "genuinely nothing running" are three visibly
different outcomes here rather than one empty table.
"""

import streamlit as st

from dashboard import config, hostinfo, ui

st.title("Containers")
st.caption("Every container the runtime reports as running, read at page load.")

socket_path = config.docker_socket()

if socket_path is None:
	st.info(
		"No container-runtime socket is configured. Set `DASHBOARD_DOCKER_SOCKET_PATH` "
		"and mount that socket into this container read-only.",
		icon=":material/info:",
	)
	st.stop()

if not socket_path.exists():
	ui.unavailable(
		"Running containers",
		f"{socket_path} is not present inside this container.\n\n"
		"This is a mount problem, not a finding: nothing here can conclude that no "
		"containers are running.",
	)
	st.stop()

try:
	df = hostinfo.load_containers(socket_path)
except (OSError, RuntimeError, ValueError) as exc:
	ui.unavailable("Running containers", str(exc))
	st.stop()

if df.empty:
	st.success("The runtime is reachable and reports no running containers.", icon=":material/check:")
	ui.source_note(f"container-runtime API over `{socket_path}` - reachable, empty result")
	st.stop()

with st.container(horizontal=True):
	st.metric("Running", len(df), border=True)
	st.metric("Distinct images", df.Image.nunique(), border=True)
	st.metric("Publishing a host port", int(df.Ports.str.contains("->").sum()), border=True)

query = st.text_input("Filter by name or image", placeholder="e.g. postgres")
df_view = df
if query:
	mask = df.Name.str.contains(query, case=False, na=False) | df.Image.str.contains(query, case=False, na=False)
	df_view = df.loc[mask]

st.dataframe(
	df_view,
	hide_index=True,
	column_config={
		"Name": st.column_config.TextColumn("Name", width="medium"),
		"Image": st.column_config.TextColumn("Image", width="medium"),
		"State": st.column_config.TextColumn("State", width="small"),
		"Status": st.column_config.TextColumn("Status", width="medium"),
		"Ports": st.column_config.TextColumn("Ports", width="small"),
		"Created": st.column_config.DatetimeColumn("Created", format="D MMM YYYY HH:mm"),
	},
)

ui.source_note(
	f"container-runtime API `/{hostinfo.DOCKER_API_VERSION}/containers/json` over `{socket_path}`, "
	f"showing {len(df_view)} of {len(df)} rows. Times in UTC. "
	"`Ports` shows `host->container` where a host port is published, bare where it isn't."
)
