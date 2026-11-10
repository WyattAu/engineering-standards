#!/usr/bin/env python3
"""check-provenance.py - PROVENANCE (PV-1..PV-3) conformance for one repo.

Stdlib only. Exit 0 on success, 1 on findings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FINDING = tuple[str, str, str]  # rule, path, message

ATTEST_ACTION_RE = re.compile(r"actions/attest-build-provenance\b")
ID_TOKEN_RE = re.compile(r"(?m)^\s*id-token\s*:\s*write\b")
ATTESTATIONS_RE = re.compile(r"(?m)^\s*attestations\s*:\s*write\b")
NONE_RE = re.compile(r"(?mi)^\s*distributables?\s*:\s*none\s*$")


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def find_attest_workflows(root: Path) -> list[Path]:
    wfdir = root / ".github" / "workflows"
    found: list[Path] = []
    if not wfdir.is_dir():
        return found
    # canonical name first
    for name in ("attest.yml", "attest.yaml", "provenance.yml", "provenance.yaml"):
        p = wfdir / name
        if p.is_file():
            found.append(p)
    # also accept any workflow that uses the attestation action
    if not found:
        for p in sorted(wfdir.glob("*.yml")) + sorted(wfdir.glob("*.yaml")):
            txt = read_text(p)
            if ATTEST_ACTION_RE.search(txt):
                found.append(p)
    return found


def check_provenance(root: Path) -> list[FINDING]:
    # PV-1 path 2: explicit no-distributables declaration
    scope = root / ".provenance-scope"
    if scope.is_file():
        txt = read_text(scope)
        if NONE_RE.search(txt):
            return []
        return [("PV-1", ".provenance-scope", "present but does not declare 'distributable: none' / 'distributables: none'")]

    workflows = find_attest_workflows(root)
    if not workflows:
        return [(
            "PV-1",
            ".github/workflows/attest.yml",
            "no attestation workflow found and no '.provenance-scope' declaring 'distributable: none' (OMNI-CORE 11c)",
        )]

    findings: list[FINDING] = []
    for wf in workflows:
        rel = str(wf.relative_to(root))
        txt = read_text(wf)
        if not ATTEST_ACTION_RE.search(txt):
            findings.append(("PV-1", rel, "workflow does not use 'actions/attest-build-provenance'"))
        if not ID_TOKEN_RE.search(txt):
            findings.append(("PV-1", rel, "missing 'id-token: write' permission required for attestation"))
        if not ATTESTATIONS_RE.search(txt):
            findings.append(("PV-1", rel, "missing 'attestations: write' permission required for attestation"))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="repository root to check")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.path).resolve()
    findings = check_provenance(root)
    if args.json:
        print(json.dumps([{"rule": r, "path": p, "message": m} for r, p, m in findings], indent=2))
    else:
        for r, p, m in findings:
            print(f"{r}: {p}: {m}")
        print(f"check-provenance: {root.name} - {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
