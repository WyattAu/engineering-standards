#!/usr/bin/env bash
# Enable flakes, then auto-enter the flake shell on login. IN_NIX_SHELL
# guards against recursion once nix develop takes over.
set -euo pipefail
mkdir -p ~/.config/nix
grep -q 'nix-command' ~/.config/nix/nix.conf 2>/dev/null ||
  echo 'experimental-features = nix-command flakes' >>~/.config/nix/nix.conf
grep -q 'IN_NIX_SHELL' ~/.bashrc 2>/dev/null || cat >>~/.bashrc <<'RC'

# Omni devshell: drop into the flake shell automatically.
if [ -z "${IN_NIX_SHELL:-}" ] && [ -f flake.nix ]; then
  exec nix develop -c bash
fi
RC
echo "nix devcontainer ready — shell will enter 'nix develop' automatically."
