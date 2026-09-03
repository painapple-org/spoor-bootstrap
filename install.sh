#!/usr/bin/env bash
#
# install.sh — sets up the three hard requirements for a spoor-bootstrap
# instance (docker, uv, gh cli) and runs the first-run interview that
# records how this deployment wants to work.
#
# Scope, deliberately narrow: this script installs infrastructure tooling
# and asks questions. It does not install or configure anything
# app-specific (no email client, no work-tracker SDK, no comms-channel
# library) — those are per-deployment choices, documented as pointers
# below, not scripted here.
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
	fail "install.sh only knows how to set up an apt-based OS (Ubuntu/Debian) right now. Detected OS_ID='${OS_ID:-unknown}'. Install docker, uv, and gh manually for your OS, then re-run this script's interview section, or send a PR that adds support for your OS."
fi

if ! command -v apt-get >/dev/null 2>&1; then
	fail "OS reports as '${OS_ID}' but apt-get is not on PATH. Refusing to guess how to install packages here."
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
		usermod -aG docker "$SUDO_USER" 2>/dev/null \
			&& log "Added ${SUDO_USER} to the docker group (log out/in for it to take effect)." \
			|| log "Could not add ${SUDO_USER} to the docker group automatically; add manually with 'usermod -aG docker ${SUDO_USER}' if you want to run docker without sudo."
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
# .claude/skills and .opencode/skills are each a single whole-folder
# symlink committed straight into git, pointing back at the canonical
# skills/ directory — git tracks and clones symlinks natively on
# Linux/macOS, so a normal `git clone` needs no extra step here. This only
# guards against the one way that silently breaks: a GitHub "Download
# ZIP" (or any non-git copy) turns each symlink into a plain text file
# containing its target path, which is invisible in an `ls` but leaves
# the harness reading nothing.

for harness_skills_dir in .claude/skills .opencode/skills; do
	if [[ ! -L "$SCRIPT_DIR/$harness_skills_dir" ]] || [[ ! -d "$SCRIPT_DIR/$harness_skills_dir" ]]; then
		fail "${harness_skills_dir} is not a working symlink into skills/. If you got this repo via a ZIP download instead of 'git clone', symlinks don't survive that — re-clone with git instead."
	fi
done
log ".claude/skills and .opencode/skills resolve correctly."

# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------

log "Now a short interview about how this deployment should work."
echo "Nothing below is scripted behavior — it just records your answers so"
echo "whichever agentic harness you run next (see AGENTS.md) knows how to act."
echo

read -r -p "Your own technical experience level (e.g. 'experienced developer', 'non-technical'): " OWNER_TECH_LEVEL
read -r -p "Who is the end product for — a technical or a non-technical end-user? [technical/non-technical]: " END_USER_TYPE
read -r -p "Which work tracker do you want to use (e.g. Linear, GitHub Issues, Jira, plain markdown files)?: " WORK_TRACKER
read -r -p "Which real-time comms channel do you want the agent reachable on (e.g. Telegram, Slack, Discord, none yet)?: " COMMS_CHANNEL

if [[ "$END_USER_TYPE" == "non-technical" || "$END_USER_TYPE" == "Non-technical" ]]; then
	echo
	log "Noted: building for a non-technical end-user."
	echo "Your agent's first read after this interview should be:"
	echo "  ${SCRIPT_DIR}/skills/product-tech-stack/SKILL.md"
	echo "That file states the required stack once — it isn't repeated here."
fi

# ---------------------------------------------------------------------------
# Write .env
# ---------------------------------------------------------------------------

ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"

if [[ -f "$ENV_FILE" ]]; then
	log ".env already exists at ${ENV_FILE}; leaving it untouched. Edit it by hand to update these answers."
else
	[[ -f "$ENV_EXAMPLE" ]] || fail ".env.example is missing from ${SCRIPT_DIR}; can't generate .env without it."
	cp "$ENV_EXAMPLE" "$ENV_FILE"
	{
		echo ""
		echo "# --- recorded by install.sh's interview ---"
		echo "OWNER_TECH_LEVEL=\"${OWNER_TECH_LEVEL}\""
		echo "END_USER_TYPE=\"${END_USER_TYPE}\""
		echo "WORK_TRACKER=\"${WORK_TRACKER}\""
		echo "COMMS_CHANNEL=\"${COMMS_CHANNEL}\""
	} >> "$ENV_FILE"
	log "Wrote interview answers to ${ENV_FILE}."
fi

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

Recorded in .env:
  - Your technical level: ${OWNER_TECH_LEVEL}
  - End-user type:        ${END_USER_TYPE}
  - Work tracker:         ${WORK_TRACKER}
  - Comms channel:        ${COMMS_CHANNEL}

What this script did NOT do (by design — these are per-deployment
choices, not something install.sh scripts for you):
  - No work-tracker integration was installed or configured. Wire up
    "${WORK_TRACKER}" yourself, or point your agent at docs for it.
  - No comms-channel bot/library was installed. Set up "${COMMS_CHANNEL}"
    yourself (bot token, webhook, etc.) and hand the credential to your
    agent via .env.
  - No email provider was configured. Whether you use Gmail, Outlook, a
    self-hosted Nextcloud mail MCP, or something else is your call —
    document the choice and provision an account for your agent's own
    address (see AGENTS.md's self-provisioning section), there's no
    installer for this here.

Next steps:
  1. Read AGENTS.md for what your agent does with all of this.
  2. Read STARTUP.md and paste its prompt into your chosen harness to
     kick off the first-boot interview there (this script only handled
     infrastructure + the interview above, not the agent's own
     conversation loop).
  3. Provision the self-provisioning shopping list your agent gives you
     once the interview inside your harness is done.

============================================================
SUMMARY
