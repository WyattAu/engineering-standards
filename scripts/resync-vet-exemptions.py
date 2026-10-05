#!/usr/bin/env python3
"""Resync (or verify) cargo-vet `exemptions` against `Cargo.lock`.

## Why this exists

Every estate repo gates on `cargo vet --locked`. Because
`supply-chain/imports.lock` and `supply-chain/audits.toml` are
deliberately empty — all third-party crates are exempted rather than
vetted individually — a repo's exemption set must name **every**
registry-sourced package in `Cargo.lock`, at the **exact** locked version.

That makes `supply-chain/config.toml` a pure function of `Cargo.lock`.
Any dependency change therefore invalidates it, and a forgotten
regeneration is a red `quality / vet`. Across the estate this has been
the single most common CI failure, and it has bitten in at least four
repos within one week — twice in the same repo within an hour.

The fix is mechanical but was being done by hand, with the ordering
mistake (regenerating the exemptions *before* writing the lockfile)
producing a second round of red. This script makes it one command, in
the one correct order, and gives CI a `--check` mode that fails with the
fix spelled out instead of a wall of `missing ["safe-to-deploy"]`.

## Usage

```sh
# Regenerate (the fix). Run this AFTER Cargo.lock is final.
python3 scripts/resync-vet-exemptions.py --write

# Verify only (the gate). Exits non-zero and prints the fix command.
python3 scripts/resync-vet-exemptions.py --check
```

`--check` is what the shared `quality / vet` job runs before
`cargo vet --locked`.

## What it touches

Only `supply-chain/config.toml`, and only its `[[exemptions.*]]`
blocks. The `[cargo-vet]` preamble and any `[[criteria]]` / `[[audits]]`
sections are preserved verbatim. Packages with no `source` key (workspace
members and path dependencies) are skipped — cargo-vet treats those as
first-party and never demands an exemption.
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys

DEFAULT_LOCK = "Cargo.lock"
DEFAULT_CONFIG = os.path.join("supply-chain", "config.toml")

_EXEMPTION_HEADER = "[[exemptions."
_ANCHOR = "cargo-vet config file"


def locked_registry_packages(lock_path: str) -> dict[str, set[str]]:
    """Every registry- or git-sourced package in the lockfile.

    Returns ``{name: {versions, ...}}``. Workspace members and path
    dependencies carry no ``source`` key and are excluded — cargo-vet
    never requires an exemption for first-party code.
    """
    with open(lock_path, encoding="utf-8") as fh:
        lock = fh.read()

    required: dict[str, set[str]] = collections.defaultdict(set)
    for block in lock.split("[[package]]")[1:]:
        name = re.search(r'^name = "(.+)"', block, re.M)
        version = re.search(r'^version = "(.+)"', block, re.M)
        source = re.search(r"^source = ", block, re.M)
        if name and version and source:
            required[name.group(1)].add(version.group(1))
    return required


def render(config_path: str, required: dict[str, set[str]]) -> str:
    """The config text with its exemption blocks replaced by `required`."""
    with open(config_path, encoding="utf-8") as fh:
        existing = fh.read()

    head = existing.split(_EXEMPTION_HEADER)[0].rstrip("\n")
    if _ANCHOR not in head:
        sys.exit(
            f"error: {config_path} does not look like a cargo-vet config "
            f"(no '{_ANCHOR}' header before the first exemption block)"
        )

    out = [head, ""]
    for name in sorted(required):
        for version in sorted(required[name]):
            out += [
                f"{_EXEMPTION_HEADER}{name}]]",
                f'version = "{version}"',
                'criteria = "safe-to-deploy"',
                "",
            ]
    return "\n".join(out).rstrip("\n") + "\n"


def diff_summary(required: dict[str, set[str]], config_path: str) -> str:
    """Human-readable drift report, or "" when the config is in sync."""
    with open(config_path, encoding="utf-8") as fh:
        existing = fh.read()

    have: dict[str, set[str]] = collections.defaultdict(set)
    for block in existing.split(_EXEMPTION_HEADER)[1:]:
        name = block.split("]]")[0]
        version = re.search(r'version = "(.+)"', block)
        if version:
            have[name].add(version.group(1))

    missing = sorted(
        (n, v) for n, versions in required.items() for v in versions if v not in have.get(n, set())
    )
    stale = sorted(
        (n, v) for n, versions in have.items() for v in versions if v not in required.get(n, set())
    )
    if not missing and not stale:
        return ""

    lines = []
    if missing:
        preview = ", ".join(f"{n} {v}" for n, v in missing[:8])
        lines.append(f"  {len(missing)} missing:  {preview}{' …' if len(missing) > 8 else ''}")
    if stale:
        preview = ", ".join(f"{n} {v}" for n, v in stale[:8])
        lines.append(f"  {len(stale)} stale:    {preview}{' …' if len(stale) > 8 else ''}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lock", default=DEFAULT_LOCK, help="path to Cargo.lock")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="path to supply-chain/config.toml")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify only; non-zero exit on drift")
    mode.add_argument("--write", action="store_true", help="rewrite the exemption blocks")
    args = ap.parse_args()

    if not os.path.exists(args.lock):
        sys.exit(f"error: {args.lock} not found — run from the repo root")
    if not os.path.exists(args.config):
        if args.check:
            sys.exit(f"error: {args.config} not found — nothing to verify")
        sys.exit(f"error: {args.config} not found — nothing to resync")

    required = locked_registry_packages(args.lock)
    if not required:
        sys.exit(f"error: no registry packages in {args.lock} — refusing to touch {args.config}")

    if args.write:
        before = open(args.config, encoding="utf-8").read()
        after = render(args.config, required)
        if before == after:
            print(f"vet exemptions already in sync ({len(required)} crates)")
            return 0
        with open(args.config, "w", encoding="utf-8") as fh:
            fh.write(after)
        total = sum(len(v) for v in required.values())
        print(f"resynced {args.config}: {total} blocks across {len(required)} crates")
        print("now run `cargo vet fmt` (canonical ordering), then `cargo vet --locked`")
        return 0

    drift = diff_summary(required, args.config)
    if not drift:
        print(f"vet exemptions in sync ({len(required)} crates)")
        return 0
    print(f"error: {args.config} is out of sync with {args.lock}:")
    print(drift)
    print()
    print("The exemption set must name every registry package at its exact")
    print("locked version. Cargo.lock must already be final — regenerate in")
    print("this order:")
    print("    python3 scripts/resync-vet-exemptions.py --write")
    print("    cargo vet fmt")
    print("    cargo vet --locked")
    return 1


if __name__ == "__main__":
    sys.exit(main())
