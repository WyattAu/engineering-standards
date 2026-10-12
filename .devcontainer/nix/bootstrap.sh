#!/usr/bin/env bash
# Deterministic Nix bootstrap for the nix devcontainer flavor.
#
# Why not the `ghcr.io/devcontainers-extra/features/nix` feature: anonymous
# pulls of that artifact 401, which broke the container build on every
# platform. The official installer is scriptable and the flake (flake.nix)
# stays the single source of truth for the *toolchain* — this script only
# provides Nix itself.
set -euo pipefail

if command -v nix >/dev/null 2>&1; then
  nix --version
  exit 0
fi

installer="$(mktemp -t nix-install-XXXXXX.sh)"
curl -fsSL -o "$installer" https://nixos.org/nix/install
# --no-daemon: containers have no systemd; a daemonized install would hang.
# shellcheck source=/dev/null
sh "$installer" --no-confirm --no-daemon
rm -f "$installer"

# Make nix visible to non-login shells (editors, CI steps, post-create).
for rc in \
  "${HOME:-/root}/.nix-profile/etc/profile.d/nix.sh" \
  /nix/var/nix/profiles/default/etc/profile.d/nix.sh; do
  if [ -f "$rc" ]; then
    # shellcheck source=/dev/null
    . "$rc"
    break
  fi
done

if ! command -v nix >/dev/null 2>&1; then
  echo "bootstrap-nix: nix is installed but not on PATH; add it to your profile" >&2
  exit 1
fi

nix --version
echo "bootstrap-nix: ready — the flake provides the toolchain (nix develop)."
