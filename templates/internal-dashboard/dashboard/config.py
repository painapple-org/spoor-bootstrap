"""Every path and setting this dashboard reads, in one place.

All of it comes from the environment with a `DASHBOARD_` prefix, so the same
image runs unchanged against real host paths from a checkout and against the
read-only bind-mounts it gets in the container. Nothing here reaches for a
default that would quietly point at the wrong thing: a path that isn't
mounted resolves to a path that doesn't exist, and the pages report that as
"could not be checked" rather than as a negative finding.

Deliberately stdlib-only. A settings library is a fine choice once this
dashboard has enough configuration to earn one; two dozen lines of os.environ
is not the place to start.
"""

import os
from pathlib import Path


def _text(name: str, default: str) -> str:
	return os.environ.get(f"DASHBOARD_{name}", default)


def _int(name: str, default: int) -> int:
	return int(_text(name, str(default)))


def _path_list(name: str, default: str) -> list[Path]:
	"""A colon-separated path list, the same shape PATH itself uses."""
	return [Path(part) for part in _text(name, default).split(":") if part.strip()]


# Shown in the browser tab and the page header. The one place this
# deployment's own name for the dashboard is written down.
TITLE = _text("TITLE", "Internal dashboard")

# Filesystem to report free space on. Inside the container this is the
# container's own root by default, which is a real answer but rarely the
# interesting one - point it at a mounted host path to measure that instead.
DISK_PATH = Path(_text("DISK_PATH", "/"))

# Container runtime socket, read-only, for the "what is running" page. Unset
# it (to an empty value) on a host with no container runtime and that page
# says so instead of erroring.
DOCKER_SOCKET_PATH = _text("DOCKER_SOCKET_PATH", "/var/run/docker.sock")

# Git checkouts the shipping-history page reads `git log` from.
REPO_PATHS = _path_list("REPO_PATHS", "")

# How far back the shipping-history page looks by default.
DEFAULT_WINDOW_DAYS = _int("DEFAULT_WINDOW_DAYS", 30)


def docker_socket() -> Path | None:
	return Path(DOCKER_SOCKET_PATH) if DOCKER_SOCKET_PATH.strip() else None
