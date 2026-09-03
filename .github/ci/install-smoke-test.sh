#!/usr/bin/env bash
#
# Runs install.sh for real, inside a throwaway fresh-Ubuntu container, and
# asserts the outcome — so a change that breaks the bootstrap on a genuinely
# bare box fails CI instead of merely shellcheck-ing clean. Driven by the
# install-execution job in ../workflows/ci.yml, which mounts the checkout at
# $SMOKE_SRC. Do not run this on a machine you care about: it installs
# docker, uv and gh system-wide and creates a passwordless-sudo account.
#
# One invocation per privilege shape install.sh supports:
#   root       - a plain root shell with no sudo installed at all, which is
#                the bare-container/bare-VPS case
#   sudo-user  - an unprivileged account with passwordless sudo, which is
#                what install.sh's $SUDO escalation path exists for
#
# Asserted: install.sh exits 0, and docker, uv and gh are all on PATH and
# actually runnable in the same shell it ran in — not merely that nothing
# crashed. The docker *daemon* being up is deliberately not asserted: a
# container has no systemd for install.sh to start it with, so what runs
# here is install.sh's own no-systemd branch, which reports NOT VERIFIED and
# continues by design. That is the same verification boundary a human gets
# testing this in a container by hand.

set -euo pipefail

MODE="${1:?usage: install-smoke-test.sh <root|sudo-user>}"
SRC="${SMOKE_SRC:-/src}"
WORK="/work"
TEST_USER="smoketest"

fail() { printf '\nSMOKE TEST FAILED (%s): %s\n' "$MODE" "$1" >&2; exit 1; }

assert_bootstrap_result() {
	local tool
	for tool in docker uv gh; do
		if ! command -v "$tool" >/dev/null 2>&1; then
			fail "install.sh exited 0 but '${tool}' is not on PATH for $(id -un)."
		fi
		"$tool" --version >/dev/null || fail "'${tool} --version' does not run for $(id -un)."
	done
	printf '\nSMOKE TEST PASSED (%s): docker, uv and gh are installed and runnable as %s.\n' \
		"$MODE" "$(id -un)"
	printf '  docker: %s\n  uv:     %s\n  gh:     %s\n' \
		"$(docker --version)" "$(uv --version)" "$(gh --version | sed -n 1p)"
}

# $SRC is mounted read-only, so run against a copy. cp -a keeps the harness
# skill symlinks and the .git directory intact, both of which install.sh
# inspects. Skipped on the re-exec below, where the copy already exists.
if [[ ! -d "$WORK" ]]; then
	cp -a "$SRC" "$WORK"
fi

case "$MODE" in
	root)
		[[ "$(id -u)" -eq 0 ]] || fail "this mode expects to run as root, but is running as $(id -un)."
		if command -v sudo >/dev/null 2>&1; then
			fail "this mode exists to prove install.sh needs no sudo at all, but sudo is present in this container."
		fi
		cd "$WORK"
		./install.sh
		assert_bootstrap_result
		;;
	sudo-user)
		if [[ "$(id -u)" -eq 0 ]]; then
			# Still the container's root shell: build the unprivileged account
			# install.sh is to be tested against, then hand over to it. sudo is
			# not in the base image, so installing it is part of the fixture.
			apt-get update -y
			DEBIAN_FRONTEND=noninteractive apt-get install -y sudo
			useradd --create-home --shell /bin/bash "$TEST_USER"
			printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$TEST_USER" > "/etc/sudoers.d/${TEST_USER}"
			chmod 0440 "/etc/sudoers.d/${TEST_USER}"
			chown -R "${TEST_USER}:${TEST_USER}" "$WORK"
			exec su "$TEST_USER" -c "bash '${WORK}/.github/ci/install-smoke-test.sh' sudo-user"
		fi
		cd "$WORK"
		./install.sh
		assert_bootstrap_result
		;;
	*)
		fail "unknown mode '${MODE}'; expected 'root' or 'sudo-user'."
		;;
esac
