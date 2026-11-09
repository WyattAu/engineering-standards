#!/usr/bin/env bash
# buildinfo.sh: record the inputs of a build (OMNI-CORE 11b).
#
# Writes a deterministic JSON record of everything that can silently change
# an artifact: commit, toolchain, lockfile digests, locale/timezone,
# SOURCE_DATE_EPOCH, compiler flags, host, CPU count, and the command.
# Two runs on the same inputs produce byte-identical output, so a
# reproducibility gate can compare them with `--compare`.
#
# Usage:
#   buildinfo.sh [--out FILE] [--command "cargo build --release --locked"]
#   buildinfo.sh --compare A.json B.json
#
# Exit: 0 on success/match, 1 on mismatch, 2 on usage error.

set -euo pipefail

die() { printf 'buildinfo: %s\n' "$1" >&2; exit 2; }

json_escape() {
  python3 -c 'import json,sys; sys.stdout.write(json.dumps(sys.argv[1]))' "$1"
}

digest() {
  if [ -f "$1" ]; then
    sha256sum "$1" | cut -d' ' -f1
  else
    printf ''
  fi
}

compare() {
  local left="$1" right="$2"
  [ -f "$left" ] || die "missing $left"
  [ -f "$right" ] || die "missing $right"
  if cmp -s "$left" "$right"; then
    printf 'buildinfo: MATCH %s == %s\n' "$left" "$right"
    exit 0
  fi
  printf 'buildinfo: MISMATCH %s != %s\n' "$left" "$right"
  diff -u "$left" "$right" || true
  exit 1
}

out=""
command_text=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --out) out="${2:-}"; shift 2 ;;
    --command) command_text="${2:-}"; shift 2 ;;
    --compare) compare "${2:-}" "${3:-}" ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$repo_root"

commit=$(git rev-parse HEAD 2>/dev/null || printf 'unknown')
dirty="false"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then dirty="true"; fi
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'unknown')

rustc_version="none"
# sed, not head: `head -1` closes the pipe, rustc takes SIGPIPE, and
# `set -o pipefail` turns a successful read into a failed script.
if command -v rustc >/dev/null 2>&1; then rustc_version=$(rustc -vV | sed -n '1p'); fi
cargo_version="none"
if command -v cargo >/dev/null 2>&1; then cargo_version=$(cargo -V); fi
python_version="none"
if command -v python3 >/dev/null 2>&1; then python_version=$(python3 -V); fi
go_version="none"
if command -v go >/dev/null 2>&1; then go_version=$(go version); fi

lockfiles=""
for candidate in Cargo.lock package-lock.json bun.lock bun.lockb uv.lock flake.lock go.sum pnpm-lock.yaml; do
  if [ -f "$candidate" ]; then
    lockfiles="${lockfiles}${lockfiles:+,}{\"file\": $(json_escape "$candidate"), \"sha256\": $(json_escape "$(digest "$candidate")")}"
  fi
done

epoch="${SOURCE_DATE_EPOCH:-unset}"
tz="${TZ:-unset}"
locale="${LC_ALL:-${LANG:-unset}}"
flags="${RUSTFLAGS:-unset}"
cflags="${CFLAGS:-unset}"

host_os=$(uname -s)
host_release=$(uname -r)
host_arch=$(uname -m)
cpu_count="unknown"
if command -v nproc >/dev/null 2>&1; then cpu_count=$(nproc); fi
target="host"
if command -v rustc >/dev/null 2>&1; then
  target=$(rustc -vV | awk '/^host:/ {print $2}')
fi

record=$(cat <<JSON
{
  "schema": "wyattau.buildinfo/1",
  "repo": $(json_escape "$(basename "$repo_root")"),
  "commit": $(json_escape "$commit"),
  "branch": $(json_escape "$branch"),
  "dirty": $dirty,
  "command": $(json_escape "$command_text"),
  "toolchain": {
    "rustc": $(json_escape "$rustc_version"),
    "cargo": $(json_escape "$cargo_version"),
    "python": $(json_escape "$python_version"),
    "go": $(json_escape "$go_version")
  },
  "target": $(json_escape "$target"),
  "lockfiles": [$lockfiles],
  "environment": {
    "source_date_epoch": $(json_escape "$epoch"),
    "tz": $(json_escape "$tz"),
    "locale": $(json_escape "$locale"),
    "rustflags": $(json_escape "$flags"),
    "cflags": $(json_escape "$cflags")
  },
  "host": {
    "os": $(json_escape "$host_os"),
    "release": $(json_escape "$host_release"),
    "arch": $(json_escape "$host_arch"),
    "cpu_count": $(json_escape "$cpu_count")
  }
}
JSON
)

# Canonical form: sorted keys, no trailing whitespace, so two records of the
# same inputs compare equal as bytes.
canonical=$(printf '%s' "$record" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin), indent=2, sort_keys=True))')

if [ -n "$out" ]; then
  printf '%s\n' "$canonical" > "$out"
  printf 'buildinfo: wrote %s (sha256 %s)\n' "$out" "$(digest "$out")"
else
  printf '%s\n' "$canonical"
fi
