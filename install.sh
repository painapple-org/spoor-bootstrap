#!/usr/bin/env bash
#
# install.sh — pure OS-level bootstrap for a spoor-bootstrap instance:
# sanity-checks the skill symlinks, installs the three hard requirements
# (docker, uv, gh cli) plus the handful of apt packages they need to be
# fetchable at all, and checks the docker daemon is reachable — starting it
# where the box has systemd, and saying NOT VERIFIED where it has none.
# Nothing else.
#
# Scope, deliberately narrow: this script is purely mechanical OS/dependency
# setup. It asks no questions and writes no config — the first-boot
# interview, .env generation, and this deployment's conventions doc are all
# driven by the agent itself, per STARTUP.md, once this script hands off.
# The interview needs real back-and-forth judgment rather than a fixed
# `read -p` script, so STARTUP.md is its one home and this script has no
# say in it.
#
# Fails loudly on anything it can't handle: an unsupported OS, a failed
# install, or a missing prerequisite stops the script with a clear message
# rather than silently skipping the step.

set -euo pipefail

log() { printf '\n\033[1;32m==>\033[0m %s\n' "$1"; }
fail() { printf '\n\033[1;31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

# Records what an upstream installer script actually contained before it gets
# executed as root. This is an audit trail and nothing more: there is no pinned
# checksum to compare against, so nothing here can refuse a script — see
# README.md's "Before you run install.sh" for exactly what that pattern does
# and does not protect against.
log_downloaded_sha256() {
	local label="$1" path="$2"
	if command -v sha256sum >/dev/null 2>&1; then
		log "sha256 of the ${label} installer just downloaded: $(sha256sum "$path" | cut -d' ' -f1) (recorded, not verified against anything)"
	else
		log "NOT VERIFIED: sha256sum is not on PATH, so no record was made of what the ${label} installer contained before it ran."
	fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

# ID alone is the distro's own name, so an apt-based derivative (Linux Mint,
# Pop!_OS, Raspberry Pi OS, Devuan, ...) never matches it even though every
# step below would work there. ID_LIKE is precisely the field those distros
# use to declare which parent they behave like, so it is the fallback: match
# either. ID_LIKE is a space-separated list, hence the padded case match on
# both fields together rather than a string comparison.

OS_ID=""
OS_ID_LIKE=""
if [[ -r /etc/os-release ]]; then
	# shellcheck source=/dev/null
	OS_ID="$(. /etc/os-release && echo "${ID:-}")"
	# shellcheck source=/dev/null
	OS_ID_LIKE="$(. /etc/os-release && echo "${ID_LIKE:-}")"
fi

case " ${OS_ID} ${OS_ID_LIKE} " in
	*" ubuntu "* | *" debian "*) ;;
	*)
		fail "install.sh only knows how to set up an apt-based OS (Ubuntu/Debian, or a derivative declaring one of them in ID_LIKE) right now. /etc/os-release reports ID='${OS_ID:-unknown}' ID_LIKE='${OS_ID_LIKE:-none}'. Install docker, uv, and gh manually for your OS, then proceed straight to STARTUP.md, or send a PR that adds support for your OS."
		;;
esac

if ! command -v apt-get >/dev/null 2>&1; then
	fail "OS reports as ID='${OS_ID:-unknown}' ID_LIKE='${OS_ID_LIKE:-none}', which looks apt-based, but apt-get is not on PATH. Refusing to guess how to install packages here."
fi

# ---------------------------------------------------------------------------
# Skill symlinks sanity check (before anything gets installed)
# ---------------------------------------------------------------------------
#
# Checks that each harness-native skills path is still a symlink resolving
# to a directory, and fails loudly if not. See skills/README.md's "How
# harnesses discover these" for what these symlinks are and why a non-git
# copy is the one thing that breaks them.

for harness_skills_dir in .claude/skills .opencode/skills; do
	if [[ ! -L "$SCRIPT_DIR/$harness_skills_dir" ]] || [[ ! -d "$SCRIPT_DIR/$harness_skills_dir" ]]; then
		fail "${harness_skills_dir} is not a working symlink into skills/. If you got this repo via a ZIP download instead of 'git clone', symlinks don't survive that — re-clone with git instead."
	fi
done
log ".claude/skills and .opencode/skills resolve correctly."

# ---------------------------------------------------------------------------
# Privilege escalation
# ---------------------------------------------------------------------------
#
# Every install step below writes outside $HOME (apt packages, /etc/apt,
# /usr/local/bin), so this script needs root one way or another. Resolve how
# once, here, instead of hardcoding `sudo` in some steps and bare commands in
# others: as root there is nothing to escalate to (and a bare-metal/container
# root shell frequently has no sudo installed at all), while as a normal user
# sudo is required and its absence is a hard stop, not something to discover
# halfway through a partial install.

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
	command -v sudo >/dev/null 2>&1 \
		|| fail "This script needs root to install packages, but you are running as $(id -un) and sudo is not installed. Re-run it as root, or install sudo first."
	SUDO="sudo"
	# Prove sudo actually works before the first install step, so a missing
	# sudoers entry stops the script here instead of halfway through. `sudo -n`
	# first (passwordless or a cached timestamp), then a plain `sudo` which
	# prompts if there's a terminal to prompt on; `sudo -v` is deliberately not
	# used, since it insists on a password even for a NOPASSWD user.
	if ! sudo -n true 2>/dev/null; then
		sudo true \
			|| fail "sudo is installed but could not authenticate $(id -un) (no sudoers entry, or no terminal to ask for a password on). Re-run this script as root, or grant this user sudo access first."
	fi
fi

# ---------------------------------------------------------------------------
# apt prerequisites
# ---------------------------------------------------------------------------
#
# Every remaining step fetches something over HTTPS, and a minimal Ubuntu/
# Debian image (docker's `ubuntu:24.04`, a stripped VPS template) ships with
# neither curl nor a CA bundle. Install them up front rather than letting the
# first curl call die with "command not found" three steps in.

APT_PREREQS=()
command -v curl >/dev/null 2>&1 || APT_PREREQS+=("curl")
command -v git >/dev/null 2>&1 || APT_PREREQS+=("git")
[[ -e /etc/ssl/certs/ca-certificates.crt ]] || APT_PREREQS+=("ca-certificates")

if [[ ${#APT_PREREQS[@]} -gt 0 ]]; then
	log "Installing apt prerequisites: ${APT_PREREQS[*]}..."
	$SUDO apt-get update -y || fail "apt-get update failed."
	DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y "${APT_PREREQS[@]}" \
		|| fail "Failed to install apt prerequisites: ${APT_PREREQS[*]}."
	for prereq in curl git; do
		command -v "$prereq" >/dev/null 2>&1 \
			|| fail "apt reported success but '${prereq}' is still not on PATH."
	done
	log "apt prerequisites installed."
else
	log "apt prerequisites (curl, git, ca-certificates) already present; skipping."
fi

# ---------------------------------------------------------------------------
# origin must not still be upstream's URL
# ---------------------------------------------------------------------------
#
# This checkout is not a one-shot installer that gets thrown away: the agent
# keeps opening PRs against it for work items targeting its own tooling (see
# skills/git-pr-conventions and skills/work-tracker). That only works if
# `origin` is a repo the adopter controls — which shape of remote that is
# (a private repo of their own, a fork, or a plain git remote on a box they
# own with no hosting provider behind it) is README.md's "Path to a running
# instance" to own, not this script's. Cloning upstream directly leaves
# `origin` unpushable, and the failure would otherwise stay invisible until
# the agent's first push, long after setup.
#
# What this check is: a comparison of origin's URL against upstream's path,
# which is all this script can do here. It deliberately does not test write
# access — `gh` is installed unauthenticated below and this script runs as
# root under the documented `sudo` invocation, so any auth check here would
# resolve against the wrong account's config. STARTUP.md step 5 is where
# push and PR access to both repos gets verified for real, with a human
# present to fix it. Don't read a pass here as "the remote is writable".
#
# Runs after the apt prerequisites above rather than with the other
# pre-install checks: it shells out to git, and on an image minimal enough not
# to ship git, an earlier "command not found" here would make this guard
# silently skip itself.

# `git -c safe.directory` is passed per invocation, without writing to any git
# config: git refuses to read a repository owned by a different user than the
# one running it, which is exactly the case under `sudo ./install.sh` — a
# root-run git against a checkout owned by the human. Without the override the
# git call just errors, the check quietly passes over itself, and the guard is
# missing precisely when the documented invocation is used.
git_origin_error=""
if ! origin_url="$(git -c safe.directory="$SCRIPT_DIR" -C "$SCRIPT_DIR" remote get-url origin 2>&1)"; then
	git_origin_error="$origin_url"
	origin_url=""
fi

if [[ -n "$origin_url" ]]; then
	if [[ "$origin_url" == *"painapple-org/spoor-bootstrap"* ]]; then
		fail "origin still points at the upstream repo (${origin_url}), which you almost certainly cannot push to. Repoint this checkout at a remote you control with 'git remote set-url origin <your-repo-url>' and re-run this script. There is more than one supported shape of remote here, and the choice has real consequences — this checkout ends up holding operational detail about your deployment. Read the 'Path to a running instance' section in README.md, which owns that choice, before picking one."
	fi
	log "origin is ${origin_url} (not upstream's URL). This compared the URL only, not whether you can push to it — STARTUP.md step 5 verifies that."
else
	log "NOT VERIFIED: could not read an 'origin' remote for ${SCRIPT_DIR}, so the upstream-remote check above did not run (git said: ${git_origin_error:-no origin remote configured}). Check yourself that this checkout's origin is a repo you can push to before letting the agent open PRs against it."
fi

# ---------------------------------------------------------------------------
# docker
# ---------------------------------------------------------------------------

if command -v docker >/dev/null 2>&1; then
	log "docker already installed ($(docker --version)); skipping."
else
	# Downloaded to a file and then run as root, rather than piped into sh.
	# README.md's "Before you run install.sh" is the one home for what that
	# buys (a truncated transfer cannot half-execute) and what it does not
	# (nothing here verifies the payload), including the caveat that this is
	# Docker's convenience script rather than its production install path.
	log "Installing docker via get.docker.com..."
	get_docker="$(mktemp)"
	curl -fsSL https://get.docker.com -o "$get_docker" \
		|| fail "Failed to download the docker install script."
	log_downloaded_sha256 "docker" "$get_docker"
	$SUDO sh "$get_docker" || fail "docker install script exited non-zero."
	rm -f "$get_docker"
	command -v docker >/dev/null 2>&1 || fail "docker install ran but 'docker' is still not on PATH."
	log "docker installed ($(docker --version))."
fi

# The account that runs the agent has to reach the docker socket without sudo,
# which means being in the docker group. Checked on every run, not only after a
# fresh install: a box that already had docker installed can just as easily have
# an invoking user who was never added.
#
# The user in question is whoever invoked this script: SUDO_USER when it was
# escalated with sudo, otherwise the current user. A plain root shell has no
# invoking user to infer and root already reaches the socket, so this is skipped
# there — README.md's "Before you run install.sh" says what the human has to do
# by hand in that case for the account that will actually run the agent.
docker_group_user="${SUDO_USER:-}"
if [[ -z "$docker_group_user" && "$(id -u)" -ne 0 ]]; then
	docker_group_user="$(id -un)"
fi
if [[ -n "$docker_group_user" ]]; then
	if ! getent group docker >/dev/null 2>&1; then
		log "NOT VERIFIED: there is no 'docker' group on this box, so ${docker_group_user} could not be added to it. That's expected for a rootless docker install; otherwise confirm 'docker info' works as ${docker_group_user} before relying on this instance."
	elif [[ " $(id -nG "$docker_group_user") " == *" docker "* ]]; then
		log "${docker_group_user} is already in the docker group."
	else
		$SUDO usermod -aG docker "$docker_group_user" \
			|| fail "Could not add ${docker_group_user} to the docker group. Fix that (or add them manually with 'usermod -aG docker ${docker_group_user}') and re-run this script — without it, every docker command from that account needs sudo."
		log "Added ${docker_group_user} to the docker group (log out/in for it to take effect). Note what that grants: socket access to the docker daemon is root-equivalent access to this host. README.md's 'Before you run install.sh' is the one home for why, and for what to do instead if that is not acceptable here."
	fi
fi

# A docker binary on PATH says nothing about whether the daemon is actually
# running, and "installed but the daemon never came up" is exactly the kind of
# half-finished bootstrap that only surfaces later, at the first deploy. Check
# it here. On a box without systemd (a container, or an unusual init) there is
# nothing this script can start, so say that plainly instead of pretending the
# check passed.
if $SUDO docker info >/dev/null 2>&1; then
	log "docker daemon is reachable."
elif [[ -d /run/systemd/system ]]; then
	$SUDO systemctl enable --now docker.service \
		|| fail "The docker daemon is not reachable and 'systemctl enable --now docker.service' failed. Check 'systemctl status docker' and 'journalctl -u docker' before continuing — docker is a hard requirement here."
	$SUDO docker info >/dev/null 2>&1 \
		|| fail "Started docker.service, but 'docker info' still fails. Check 'journalctl -u docker'."
	log "docker daemon started via systemd and is reachable."
else
	log "NOT VERIFIED: docker is installed but its daemon is not reachable, and this box has no systemd to start it with (typical inside a container). Start dockerd with whatever init this host uses and confirm 'docker info' works before relying on this instance."
fi

# ---------------------------------------------------------------------------
# uv
# ---------------------------------------------------------------------------

if command -v uv >/dev/null 2>&1; then
	log "uv already installed ($(uv --version)); skipping."
else
	# Installed system-wide into UV_INSTALL_DIR rather than the installer's
	# default ~/.local/bin: with sudo, $HOME is root's, so the default would
	# hide uv from the account that actually runs the agent, and ~/.local/bin
	# is only on PATH for interactive login shells anyway — which a cron job
	# or a systemd unit is not. INSTALLER_NO_MODIFY_PATH keeps it from
	# editing shell profiles it doesn't need to touch.
	#
	# Downloaded to a file and then run, rather than piped into sh, for the
	# same reason as the docker installer above: a pipe hands sh whatever bytes
	# have arrived and it starts executing them, so a transfer that dies
	# partway can run a truncated script before curl's own failure is
	# observable at all. Downloading first makes a partial fetch a failed
	# download and nothing more — and nothing else. It does not verify the
	# payload; README.md owns that distinction.
	UV_INSTALL_DIR="/usr/local/bin"
	log "Installing uv into ${UV_INSTALL_DIR}..."
	get_uv="$(mktemp)"
	curl -LsSf https://astral.sh/uv/install.sh -o "$get_uv" \
		|| fail "Failed to download the uv install script."
	log_downloaded_sha256 "uv" "$get_uv"
	$SUDO env UV_INSTALL_DIR="$UV_INSTALL_DIR" INSTALLER_NO_MODIFY_PATH=1 sh "$get_uv" \
		|| fail "uv install script failed."
	rm -f "$get_uv"
	hash -r
	command -v uv >/dev/null 2>&1 \
		|| fail "uv install script ran but 'uv' is still not on PATH, despite being installed into ${UV_INSTALL_DIR}. Make sure ${UV_INSTALL_DIR} is on PATH, then re-run this script."
	log "uv installed ($(uv --version))."
fi

# ---------------------------------------------------------------------------
# gh cli
# ---------------------------------------------------------------------------
#
# Binary only: this script deliberately does not run `gh auth login` and does
# not check `gh auth status`. Three reasons, all of them structural rather
# than stylistic:
#
#   - Under the documented `sudo ./install.sh` invocation, both the login and
#     the status check would resolve against root's config, not that of the
#     account the agent actually runs as. A login here would land the token in
#     the wrong home directory, and a status check here would report on the
#     wrong account — a confidently wrong answer, which is worse than no
#     answer.
#   - Authenticating is a decision (which account, which protocol), not a
#     mechanical step, and this script asks no questions by design.
#   - The first-boot flow needs to verify a real push against the actual
#     product repo anyway, which this script has no knowledge of.
#
# So auth belongs to the agent, with the human present: STARTUP.md step 5,
# ahead of the first push in step 6.

if command -v gh >/dev/null 2>&1; then
	log "gh cli already installed ($(gh --version | sed -n 1p)); skipping."
else
	log "Installing gh cli via the official apt repo..."
	$SUDO mkdir -p -m 755 /etc/apt/keyrings \
		|| fail "Could not create /etc/apt/keyrings."
	keyring_tmp="$(mktemp)"
	curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o "$keyring_tmp" \
		|| fail "Failed to fetch the gh cli apt keyring."
	$SUDO install -m 644 "$keyring_tmp" /etc/apt/keyrings/githubcli-archive-keyring.gpg \
		|| fail "Failed to install the gh cli apt keyring into /etc/apt/keyrings."
	rm -f "$keyring_tmp"
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
		| $SUDO tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
		|| fail "Failed to write the gh cli apt source."
	$SUDO apt-get update -y || fail "apt-get update failed."
	DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y gh || fail "apt-get install gh failed."
	command -v gh >/dev/null 2>&1 || fail "gh install completed but 'gh' is still not on PATH."
	log "gh cli installed ($(gh --version | sed -n 1p))."
fi

log "All three hard requirements are present: docker, uv, gh."

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

cat <<SUMMARY

============================================================
 spoor-bootstrap: install summary
============================================================

Installed / verified:
  - docker: $(docker --version 2>/dev/null || echo "not found")
  - uv:     $(uv --version 2>/dev/null || echo "not found")
  - gh:     $(gh --version 2>/dev/null | sed -n 1p || echo "not found")

This script does not ask you anything and has not written a .env — that
all happens next, driven by the agent itself. Note that gh is installed
but NOT logged in: getting a git identity that can actually push is part
of the first-boot flow below, not of this script.

Next step:
  Run your chosen agentic harness (Claude Code, OpenCode, Codex CLI, or
  another) in this checkout and tell it to read STARTUP.md. It will run
  the first-boot interview, write .env, walk you through authenticating
  gh and verify a push works, generate this deployment's conventions doc
  through its first PR, and hand you the self-provisioning shopping list.

============================================================
SUMMARY
