#!/usr/bin/env python3
"""check-hygiene.py - REPO-HYGIENE (RH-1..RH-4) conformance for one repo.

Stdlib only. Exit 0 on success, 1 on findings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FINDING = tuple[str, str, str]  # rule, path, message

SECURITY_LOCATIONS = ["SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md"]
CODEOWNERS_LOCATIONS = ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
PR_LOCATIONS = [
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/pull_request_template.md",
    "docs/PULL_REQUEST_TEMPLATE.md",
    "docs/pull_request_template.md",
]
ISSUE_SINGLE = [".github/ISSUE_TEMPLATE.md", ".github/ISSUE_TEMPLATE.yml", ".github/issue_template.md"]
PUBLIC_ISSUE_RE = re.compile(
    r"\b(open|file|create|submit|report|raise)\b[^\n]{0,60}\b(public\s+)?(issue|bug\s+report)\b",
    re.I,
)


def find_first(root: Path, rels: list[str]) -> Path | None:
    for rel in rels:
        p = root / rel
        if p.is_file():
            return p
    return None


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_security(root: Path) -> list[FINDING]:
    p = find_first(root, SECURITY_LOCATIONS)
    if p is None:
        return [("RH-1", "SECURITY.md", "missing; add SECURITY.md (root, .github/, or docs/) with a vulnerability reporting path")]
    text = read_text(p).strip()
    rel = str(p.relative_to(root))
    if not text:
        return [("RH-1", rel, "file is empty")]
    has_path = bool(
        re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
        or "mailto:" in text.lower()
        or re.search(r"https?://", text)
        or re.search(r"\b(report|disclos|contact|coordinated|vulnerabilit)\w*\b", text, re.I)
    )
    if not has_path:
        return [("RH-1", rel, "no reporting path found (need an email, URL, or explicit reporting instructions)")]
    if PUBLIC_ISSUE_RE.search(text) and not (re.search(r"[\w.+-]+@[\w.-]+\.\w+", text) or "mailto:" in text.lower() or re.search(r"https?://", text)):
        return [("RH-1", rel, "directs reporters to a public issue without an email/URL reporting path")]
    return []


def check_codeowners(root: Path) -> list[FINDING]:
    p = find_first(root, CODEOWNERS_LOCATIONS)
    if p is None:
        return [("RH-2", "CODEOWNERS", "missing; add CODEOWNERS (root, .github/, or docs/) with at least one ownership rule")]
    rel = str(p.relative_to(root))
    text = read_text(p)
    rules = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # A rule is: pattern + owner(s). Very loose: has whitespace and a token.
        parts = s.split()
        if len(parts) >= 2:
            rules.append(s)
    if not rules:
        return [("RH-2", rel, "no non-comment ownership rule found (need e.g. '* @owner')")]
    return []


def check_issue_templates(root: Path) -> list[FINDING]:
    tdir = root / ".github" / "ISSUE_TEMPLATE"
    if tdir.is_dir():
        files = [f for f in tdir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if not files:
            return [("RH-3", ".github/ISSUE_TEMPLATE/", "directory has no template files")]
        # config.yml alone is ok if non-empty
        non_config = [f for f in files if f.name.lower() != "config.yml"]
        if non_config:
            for f in non_config:
                if read_text(f).strip():
                    return []
        cfg = tdir / "config.yml"
        if cfg.is_file() and read_text(cfg).strip():
            return []
        return [("RH-3", ".github/ISSUE_TEMPLATE/", "template files are empty")]
    p = find_first(root, ISSUE_SINGLE)
    if p is None:
        return [("RH-3", ".github/ISSUE_TEMPLATE/", "missing; add .github/ISSUE_TEMPLATE/ or .github/ISSUE_TEMPLATE.md")]
    rel = str(p.relative_to(root))
    if not read_text(p).strip():
        return [("RH-3", rel, "issue template is empty")]
    return []


def check_pr_template(root: Path) -> list[FINDING]:
    p = find_first(root, PR_LOCATIONS)
    if p is not None:
        rel = str(p.relative_to(root))
        if not read_text(p).strip():
            return [("RH-4", rel, "pull request template is empty")]
        return []
    tdir = root / ".github" / "PULL_REQUEST_TEMPLATE"
    if tdir.is_dir():
        files = [f for f in tdir.iterdir() if f.is_file() and not f.name.startswith(".") and read_text(f).strip()]
        if files:
            return []
        return [("RH-4", ".github/PULL_REQUEST_TEMPLATE/", "directory has no non-empty template file")]
    return [("RH-4", ".github/PULL_REQUEST_TEMPLATE.md", "missing; add a pull request template (.github/PULL_REQUEST_TEMPLATE.md or docs/)")]


def check(root: Path) -> list[FINDING]:
    out: list[FINDING] = []
    out.extend(check_security(root))
    out.extend(check_codeowners(root))
    out.extend(check_issue_templates(root))
    out.extend(check_pr_template(root))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", default=".", help="repository root to check (default: .)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"check-hygiene: not a directory: {root}", file=sys.stderr)
        return 2
    findings = check(root)
    if args.json:
        print(json.dumps([{"rule": r, "path": p, "message": m} for r, p, m in findings], indent=2))
    else:
        for r, p, m in findings:
            print(f"FINDING [{r}] {p}: {m}")
        print(f"check-hygiene: {root.name} - {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
