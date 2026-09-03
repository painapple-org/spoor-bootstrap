#!/usr/bin/env bash
#
# install.sh — pure OS-level bootstrap for a spoor-bootstrap instance:
# installs the three hard requirements (docker, uv, gh cli) and sanity-checks
# the skill symlinks. Nothing else.
#
# Scope, deliberately narrow: this script is purely mechanical OS/dependency
# setup. It asks no questions and writes no config — the first-boot
# interview, .env generation, and this deployment's conventions doc are all
# driven by the agent itself, per STARTUP.md, once this script hands off.
# That keeps the interview logic (which needs real back-and-forth judgment,
# not a fixed `read -p` script) in one place instead of split across a shell
# script and a doc.
#
# Fails loudly on anything it can't handle: an unsupported OS, a failed
# install, or a missing prerequisite stops the script with a clear message
# rather than silently skipping the step.

set -euo pipefail

log() { printf '\n\033[1;32m==>\033[0m %s\n' "$1"; }
fail() { printf '\n\033[1;31mERROR:\033[0m %s\n' "$1" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

OS_ID=""
if [[ -r /etc/os-release ]]; then
	# shellcheck source=/dev/null
	OS_ID="$(. /etc/os-release && echo "${ID:-}")"
fi

if [[ "$OS_ID" != "ubuntu" && "$OS_ID" != "debian" ]]; then
	fail "install.sh only knows how to set up an apt-based OS (Ubuntu/Debian) right now. Detected OS_ID='${OS_ID:-unknown}'. Install docker, uv, and gh manually for your OS, then proceed straight to STARTUP.md, or send a PR that adds support for your OS."
fi

if ! command -v apt-get >/dev/null 2>&1; then
	fail "OS reports as '${OS_ID}' but apt-get is not on PATH. Refusing to guess how to install packages here."
fi

# ---------------------------------------------------------------------------
# origin must be a repo you can push to
# ---------------------------------------------------------------------------
#
# This checkout is not a one-shot installer that gets thrown away: the agent
# keeps opening PRs against it for work items targeting its own tooling (see
# skills/git-pr-conventions and skills/work-tracker). That only works if
# `origin` is a fork or mirror the adopter controls. Cloning upstream
# directly leaves `origin` unpushable, and the failure would otherwise stay
# invisible until the agent's first push, long after setup.

if origin_url="$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null)"; then
	if [[ "$origin_url" == *"painapple-org/spoor-bootstrap"* ]]; then
		fail "origin still points at the upstream repo (${origin_url}), which you almost certainly cannot push to. Fork painapple-org/spoor-bootstrap on GitHub and clone your fork instead, or repoint this checkout with 'git remote set-url origin <your-repo-url>', then re-run this script. See the 'Path to a running instance' section in README.md."
	fi
	log "origin is ${origin_url} (not the upstream repo)."
fi

# ---------------------------------------------------------------------------
# docker
# ---------------------------------------------------------------------------

if command -v docker >/dev/null 2>&1; then
	log "docker already installed ($(docker --version)); skipping."
else
	log "Installing docker via get.docker.com..."
	curl -fsSL https://get.docker.com -o /tmp/get-docker.sh \
		|| fail "Failed to download the docker install script."
	sh /tmp/get-docker.sh || fail "docker install script exited non-zero."
	rm -f /tmp/get-docker.sh
	command -v docker >/dev/null 2>&1 || fail "docker install ran but 'docker' is still not on PATH."

	if [[ -n "${SUDO_USER:-}" ]]; then
		if usermod -aG docker "$SUDO_USER" 2>/dev/null; then
			log "Added ${SUDO_USER} to the docker group (log out/in for it to take effect)."
		else
			log "Could not add ${SUDO_USER} to the docker group automatically; add manually with 'usermod -aG docker ${SUDO_USER}' if you want to run docker without sudo."
		fi
	fi
	log "docker installed ($(docker --version))."
fi

# ---------------------------------------------------------------------------
# uv
# ---------------------------------------------------------------------------

if command -v uv >/dev/null 2>&1; then
	log "uv already installed ($(uv --version)); skipping."
else
	log "Installing uv..."
	curl -LsSf https://astral.sh/uv/install.sh | sh \
		|| fail "uv install script failed."
	export PATH="$HOME/.local/bin:$PATH"
	command -v uv >/dev/null 2>&1 \
		|| fail "uv install script ran but 'uv' is still not on PATH. It's usually installed to ~/.local/bin — make sure that's on PATH in your shell profile, then re-run this script."
	log "uv installed ($(uv --version))."
fi

# ---------------------------------------------------------------------------
# gh cli
# ---------------------------------------------------------------------------

if command -v gh >/dev/null 2>&1; then
	log "gh cli already installed ($(gh --version | head -n1)); skipping."
else
	log "Installing gh cli via the official apt repo..."
	sudo mkdir -p -m 755 /etc/apt/keyrings \
		|| fail "Could not create /etc/apt/keyrings."
	curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
		| sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null \
		|| fail "Failed to fetch/install the gh cli apt keyring."
	sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
		| sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
		|| fail "Failed to write the gh cli apt source."
	sudo apt-get update -y || fail "apt-get update failed."
	sudo apt-get install -y gh || fail "apt-get install gh failed."
	command -v gh >/dev/null 2>&1 || fail "gh install completed but 'gh' is still not on PATH."
	log "gh cli installed ($(gh --version | head -n1))."
fi

log "All three hard requirements are present: docker, uv, gh."

# ---------------------------------------------------------------------------
# Skill symlinks sanity check
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
# Summary
# ---------------------------------------------------------------------------

cat <<SUMMARY

============================================================
 spoor-bootstrap: install summary
============================================================

Installed / verified:
  - docker: $(docker --version 2>/dev/null || echo "not found")
  - uv:     $(uv --version 2>/dev/null || echo "not found")
  - gh:     $(gh --version 2>/dev/null | head -n1 || echo "not found")

This script does not ask you anything and has not written a .env — that
all happens next, driven by the agent itself.

Next step:
  Run your chosen agentic harness (Claude Code, OpenCode, Codex CLI, or
  another) in this checkout and tell it to read STARTUP.md. It will run
  the first-boot interview, write .env, generate this deployment's
  conventions doc, and hand you the self-provisioning shopping list.

============================================================
SUMMARY
