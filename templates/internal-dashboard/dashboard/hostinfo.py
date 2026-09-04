"""Live readings off the host this dashboard runs on.

Three sources, all of them real measurements taken at request time: the
filesystem, the container runtime's own API, and `git log` in whatever
checkouts are mounted in.

Two habits every reader in here follows, because the pages depend on them:

- **A failure raises.** Nothing returns a plausible zero or an empty frame to
  stand in for a reading that could not be taken. A page renders "could not be
  checked" from a caught exception it names on screen; it never renders a
  fabricated number.
- **An absence is distinguishable from a failure.** A repo with no commits
  yet, or a host with no containers running, is a real state and comes back
  empty. A socket that isn't mounted, or a path outside what this process can
  see, is a different thing and says so.

The container runtime is read over its unix socket with `http.client` rather
than by shelling out to a CLI, so the image needs no runtime client installed
- only the socket bind-mounted in, read-only.
"""

import http.client
import json
import shutil
import socket
import subprocess
from pathlib import Path

import pandas as pd

# Engine API version to address. Pinned rather than using the unversioned
# path so a daemon upgrade can't change the response shape underneath the
# parsing below.
DOCKER_API_VERSION = "v1.43"

COMMIT_COLUMNS = ["Repo", "Sha", "Author", "Committed", "Subject"]

CONTAINER_COLUMNS = ["Name", "Image", "State", "Status", "Ports", "Created"]


class _UnixHTTPConnection(http.client.HTTPConnection):
	"""HTTP over a unix domain socket, which http.client has no transport for."""

	def __init__(self, socket_path: str, timeout: int = 5):
		super().__init__("localhost", timeout=timeout)
		self._socket_path = socket_path

	def connect(self):
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.settimeout(self.timeout)
		sock.connect(self._socket_path)
		self.sock = sock


def docker_api_get(socket_path: Path, path: str):
	"""GET one container-runtime API path. Raises on any failure; callers surface it."""
	conn = _UnixHTTPConnection(str(socket_path))
	try:
		conn.request("GET", path)
		response = conn.getresponse()
		body = response.read()
	finally:
		conn.close()

	if response.status != 200:
		raise RuntimeError(f"container API {path} returned HTTP {response.status}: {body[:200]!r}")

	return json.loads(body)


def load_containers(socket_path: Path) -> pd.DataFrame:
	"""One row per running container. Empty frame means none are running."""
	payload = docker_api_get(socket_path, f"/{DOCKER_API_VERSION}/containers/json")

	rows = []
	for item in payload:
		names = item.get("Names") or []
		name = names[0].lstrip("/") if names else item.get("Id", "")[:12]

		ports = []
		for port in item.get("Ports") or []:
			public = port.get("PublicPort")
			private = port.get("PrivatePort")
			ports.append(f"{public}->{private}" if public else str(private))

		rows.append(
			{
				"Name": name,
				"Image": item.get("Image", ""),
				"State": item.get("State", ""),
				"Status": item.get("Status", ""),
				"Ports": ", ".join(sorted(set(ports))),
				"Created": pd.Timestamp(item.get("Created", 0), unit="s", tz="UTC"),
			}
		)

	df = pd.DataFrame(rows, columns=CONTAINER_COLUMNS)
	df = df.sort_values("Name")
	df = df.reset_index(drop=True)
	return df


def disk_usage(path: Path) -> dict[str, float]:
	"""Free space on the filesystem holding `path`. Raises if the path isn't visible."""
	usage = shutil.disk_usage(path)
	gib = 1024**3
	return {
		"TotalGiB": round(usage.total / gib, 1),
		"UsedGiB": round(usage.used / gib, 1),
		"FreeGiB": round(usage.free / gib, 1),
		"UsedPct": round(usage.used / usage.total * 100, 1),
	}


def git_log(repo_dir: Path, max_count: int = 500) -> pd.DataFrame:
	"""Commit history for one checkout.

	Raises if `repo_dir` isn't a readable git repo, so a mount that silently
	went missing shows up as a named failure rather than as "no commits".
	"""
	if not (repo_dir / ".git").exists():
		raise FileNotFoundError(f"{repo_dir} is not a git checkout visible to this process")

	# \x1f (unit separator) can't occur in any of these fields, unlike every
	# printable character a commit subject is free to contain.
	fmt = "%h%x1f%an%x1f%cI%x1f%s"
	result = subprocess.run(
		["git", "-C", str(repo_dir), "log", f"--max-count={max_count}", f"--pretty=format:{fmt}"],
		capture_output=True,
		text=True,
		timeout=30,
	)

	# A freshly-initialized repo with zero commits is a real, expected state,
	# not a failure - it reports as empty. Anything else still raises.
	if result.returncode != 0:
		if "does not have any commits yet" in result.stderr:
			return pd.DataFrame(columns=COMMIT_COLUMNS)
		raise RuntimeError(f"git log failed in {repo_dir}: {result.stderr.strip()[:300]}")

	rows = []
	for line in result.stdout.splitlines():
		fields = line.split("\x1f")
		if len(fields) != 4:
			continue
		rows.append(
			{
				"Repo": repo_dir.name,
				"Sha": fields[0],
				"Author": fields[1],
				"Committed": pd.to_datetime(fields[2], utc=True),
				"Subject": fields[3],
			}
		)

	return pd.DataFrame(rows, columns=COMMIT_COLUMNS)


def load_commits(repo_dirs: list[Path]) -> tuple[pd.DataFrame, dict[str, str]]:
	"""Commits across every configured checkout, newest first, plus per-repo failures.

	Returns the frame and a `{path: reason}` map of checkouts that could not be
	read. One unreadable mount must not blank the whole page, and it must not
	vanish from it either - the caller renders both halves.
	"""
	frames = []
	unreadable = {}

	for repo_dir in repo_dirs:
		try:
			frames.append(git_log(repo_dir))
		except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
			unreadable[str(repo_dir)] = str(exc)

	frames = [frame for frame in frames if not frame.empty]
	if not frames:
		return pd.DataFrame(columns=COMMIT_COLUMNS), unreadable

	df = pd.concat(frames, ignore_index=True)
	df = df.sort_values("Committed", ascending=False)
	df = df.reset_index(drop=True)
	return df, unreadable


def commits_per_day(df: pd.DataFrame) -> pd.DataFrame:
	"""Commit counts per day per repo, in the wide shape st.bar_chart stacks."""
	if df.empty:
		return pd.DataFrame()

	df = df.assign(Day=df.Committed.dt.tz_convert("UTC").dt.normalize())
	gcols = ["Day", "Repo"]
	df_daily = df.groupby(gcols).agg(Count=("Sha", "count"))
	df_daily = df_daily.reset_index()
	df_wide = df_daily.pivot(index="Day", columns="Repo", values="Count")
	df_wide = df_wide.fillna(0)
	df_wide = df_wide.sort_index()
	return df_wide
