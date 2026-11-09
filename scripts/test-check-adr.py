#!/usr/bin/env python3
"""Self-test for check-adr.py: one mutation per rule.

Builds a temporary ADR directory, writes a clean record and one mutation per
case, and asserts the expected finding code. A rule that stops firing means a
decision can land without a status, a date, or a rationale.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / "check-adr.py"

CLEAN = """\
# ADR-0099: an example decision

- **Status**: Proposed (2026-11-09)
- **Date**: 2026-11-09

## Context

Something needed deciding.

## Decision

We decided it.

## Consequences

This follows.
"""

CASES = [
    (
        "clean",
        "0099-example.md",
        CLEAN,
        None,
        0,
    ),
    (
        "bad-filename",
        "99-example.md",
        CLEAN,
        "adr-filename",
        1,
    ),
    (
        "missing-status",
        "0099-example.md",
        CLEAN.replace("- **Status**: Proposed (2026-11-09)\n", ""),
        "adr-status",
        1,
    ),
    (
        "missing-date",
        "0099-example.md",
        CLEAN.replace("- **Date**: 2026-11-09\n", ""),
        "adr-date",
        1,
    ),
    (
        "bad-date",
        "0099-example.md",
        CLEAN.replace("2026-11-09\n\n## Context", "someday\n\n## Context", 1),
        "adr-date-format",
        1,
    ),
    (
        "missing-context",
        "0099-example.md",
        CLEAN.replace("## Context\n\nSomething needed deciding.\n\n", ""),
        "adr-section",
        1,
    ),
    (
        "missing-decision",
        "0099-example.md",
        CLEAN.replace("## Decision\n\nWe decided it.\n\n", ""),
        "adr-section",
        1,
    ),
    (
        "missing-consequences",
        "0099-example.md",
        CLEAN.replace("## Consequences\n\nThis follows.\n", ""),
        "adr-section",
        1,
    ),
    (
        "unknown-status",
        "0099-example.md",
        CLEAN.replace("Proposed", "Vibing"),
        "adr-status-word",
        1,
    ),
]


def run_case(name: str, filename: str, content: str, expected: str | None, expected_rc: int) -> str | None:
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / filename).write_text(content, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(CHECK), "--dir", td, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != expected_rc:
            return f"{name}: expected rc {expected_rc}, got {proc.returncode}: {proc.stdout}{proc.stderr}"
        data = json.loads(proc.stdout)
        codes = {f["code"] for f in data["details"]}
        if expected is None:
            if codes:
                return f"{name}: expected clean, got {sorted(codes)}"
        elif expected not in codes:
            return f"{name}: expected {expected}, got {sorted(codes)}"
    return None


def main() -> int:
    failures = [r for r in (run_case(*c) for c in CASES) if r]
    if failures:
        print(f"test-check-adr: FAIL ({len(failures)})")
        for failure in failures:
            print("  " + failure)
        return 1
    print(f"test-check-adr: PASS ({len(CASES)} fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
