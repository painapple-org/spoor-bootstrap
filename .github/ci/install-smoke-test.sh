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
# Asserted: install.sh exits 0; docker, uv and gh are all on PATH and actually
# runnable in the same shell it ran in — not merely that nothing crashed; and
# the docker install.sh produced can really run a container, not just answer
# --version.
#
# That last assertion needs the daemon up, and a container has no systemd for
# install.sh to start dockerd with, so install.sh takes its own no-systemd
# branch and reports NOT VERIFIED. This harness therefore starts dockerd
# itself, after install.sh has finished, and only then runs a container. The
# daemon start is this script's doing and install.sh is not credited with it;
# what gets proven is that install.sh leaves behind a docker that works once
# something starts it, which on a real VPS is the systemd branch install.sh
# does exercise and verify.
#
# Nested dockerd needs two things from the invocation in ../workflows/ci.yml,
# both load-bearing and both verified by their absence:
#   --privileged   without it dockerd dies at startup, unable to set up its
#                  bridge network ("iptables ... Permission denied"). A narrower
#                  --cap-add SYS_ADMIN/NET_ADMIN set gets the daemon up but
#                  then cannot write /sys/fs/cgroup to start a container.
#   an anonymous volume on /var/lib/docker
#                  without it the daemon starts but every container fails to
#                  mount its rootfs ("fstype: overlay ... invalid argument"):
#                  overlayfs cannot stack an upperdir on another overlayfs, and
#                  the container's own root is one. A volume puts the image
#                  store on the host filesystem instead. Same reason the
#                  official docker:dind image declares VOLUME /var/lib/docker.

set -euo pipefail

MODE="${1:?usage: install-smoke-test.sh <root|sudo-user>}"
SRC="${SMOKE_SRC:-/src}"
WORK="/work"
TEST_USER="smoketest"
DOCKERD_LOG="/tmp/dockerd.log"
DOCKERD_START_TIMEOUT_SECONDS=60

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

dump_dockerd_log() {
	printf '\n--- dockerd log (%s) ---\n' "$DOCKERD_LOG" >&2
	cat "$DOCKERD_LOG" >&2 || true
}

# Starting dockerd is this harness's job and not install.sh's — see the header.
# Backgrounded because dockerd is a foreground daemon; the container is
# throwaway and dies with this script, so nothing needs to reap it.
start_dockerd() {
	"${SUDO[@]}" dockerd >"$DOCKERD_LOG" 2>&1 &
	local waited=0
	while [[ "$waited" -lt "$DOCKERD_START_TIMEOUT_SECONDS" ]]; do
		if "${SUDO[@]}" docker info >/dev/null 2>&1; then
			printf '  daemon: %s\n' \
				"$("${SUDO[@]}" docker info --format 'v{{.ServerVersion}}, storage driver {{.Driver}}')"
			return 0
		fi
		sleep 1
		waited=$(( waited + 1 ))
	done
	dump_dockerd_log
	fail "dockerd did not answer 'docker info' within ${DOCKERD_START_TIMEOUT_SECONDS}s of being started."
}

# The payoff assertion: a real container, from a real image pull, on the docker
# install.sh just installed.
#
# Run through the argv this mode's account actually has to use. In root mode
# that is a bare docker command. In sudo-user mode it goes through `sg docker`,
# which is what additionally proves install.sh's usermod step took effect: the
# account reaches the socket on group membership alone, with no sudo, and an
# already-open login shell needs `sg` to pick that new group up.
assert_docker_runs_a_container() {
	local -a docker_cmd
	case "$MODE" in
		root) docker_cmd=(docker run --rm hello-world) ;;
		sudo-user) docker_cmd=(sg docker -c "docker run --rm hello-world") ;;
	esac

	local output
	if ! output="$("${docker_cmd[@]}" 2>&1)"; then
		printf '\n--- %s ---\n%s\n' "${docker_cmd[*]}" "$output" >&2
		dump_dockerd_log
		fail "docker is installed and the daemon is up, but it cannot actually run a container as $(id -un)."
	fi

	# hello-world's whole purpose is printing this; if the image ran but said
	# something else, the run did not prove what this asserts it did.
	if [[ "$output" != *"installation appears to be working correctly"* ]]; then
		printf '\n--- %s ---\n%s\n' "${docker_cmd[*]}" "$output" >&2
		fail "'docker run hello-world' exited 0 but did not print its success message."
	fi
	printf '  container: ran hello-world via "%s" as %s.\n' "${docker_cmd[*]}" "$(id -un)"
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
		SUDO=()
		start_dockerd
		assert_docker_runs_a_container
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
		SUDO=(sudo)
		start_dockerd
		assert_docker_runs_a_container
		;;
	*)
		fail "unknown mode '${MODE}'; expected 'root' or 'sudo-user'."
		;;
esac
