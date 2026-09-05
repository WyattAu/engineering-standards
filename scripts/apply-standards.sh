#!/usr/bin/env bash
# Bulk-apply engineering-standards templates to a kit repo.
# Usage: scripts/apply-standards.sh <kit-repo-dir> [tier] [loom] [wasm] [miri]
# Idempotent: never overwrites an existing file (diffs printed instead).
set -euo pipefail

repo="${1:?usage: apply-standards.sh <kit-repo-dir> [tier] [loom] [wasm] [miri]}"
tier="${2:-c}"
loom="${3:-false}"
wasm="${4:-false}"
miri="${5:-false}"
std_dir="$(cd "$(dirname "$0")/.." && pwd)"

cd "$repo"
mkdir -p .github/workflows

# 1. CI: reusable-workflow call (only if the repo has no ci.yml yet, or has
# one and FORCE=1).
if [ ! -f .github/workflows/ci.yml ] || [ "${FORCE:-0}" = "1" ]; then
  cat > .github/workflows/ci.yml <<EOF
name: CI
on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  quality:
    uses: WyattAu/engineering-standards/.github/workflows/rust-kit.yml@main
    with:
      tier: $tier
      all-features: true
      loom: $loom
      wasm: $wasm
      miri: $miri
EOF
  echo "CI: written (tier=$tier loom=$loom wasm=$wasm miri=$miri)"
else
  echo "CI: exists — review manually"
fi

# 2. Templates: never clobber.
for f in deny.toml SECURITY.md CHANGELOG.md; do
  if [ ! -f "$f" ]; then
    cp "$std_dir/templates/$f" "$f"
    echo "$f: copied"
  else
    echo "$f: exists"
  fi
done

# 3. dependabot.
if [ ! -f .github/dependabot.yml ]; then
  cp "$std_dir/templates/dependabot.yml" .github/dependabot.yml
  echo "dependabot: copied"
else
  echo "dependabot: exists"
fi

echo "== $repo: apply complete (tier=$tier)"
