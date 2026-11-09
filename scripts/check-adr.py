#!/usr/bin/env python3
"""Gate: ADR records conform to DECISIONS.md.

Usage:
  python3 scripts/check-adr.py [--dir DIR] [--json]

Validates every NNNN-*.md file under DIR (default docs/adr). Checks the
filename contract, required metadata, required sections, status vocabulary,
and number uniqueness. Sequence gaps are reported but do not fail the gate:
a withdrawn draft can leave a hole, and rewriting history to close it costs
more than the hole does. Uniqueness is the invariant.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9][a-z0-9-]*)\.md$")
DATE_VALUE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.M)

REQUIRED_SECTIONS = {"context", "decision"}
# A record must explain what follows from the decision. Accept the names the
# existing corpus uses rather than forcing a rename of settled history.
CONSEQUENCE_ALIASES = {
    "consequences", "consequence", "rationale", "outcome", "outcomes",
    "amendment", "amendments", "alternatives considered", "alternatives",
    "impact", "risks",
}

KNOWN_STATUS = {
    "proposed", "accepted", "rejected", "superseded", "deprecated",
    "withdrawn", "draft",
}


def norm_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().rstrip(":"))


def _strip_md(s: str) -> str:
    return re.sub(r"[*_`]+", "", s).strip()


def extract_meta(text: str, key: str) -> str | None:
    """Find `key: value` in metadata lines or `## key` section text."""
    head = "\n".join(text.splitlines()[:80])
    # Metadata line forms: `- **Status**: ...`, `**Status:** ...`, `Status: ...`
    line_re = re.compile(
        rf"^[\s\-*]*{re.escape(key)}\s*[*_`]*\s*[:\-]\s*(.+)$", re.M | re.I
    )
    m = line_re.search(head)
    if m:
        return _strip_md(m.group(1))
    # Section form: `## Status` followed by a paragraph (0008 style).
    sec_re = re.compile(
        rf"^#{{1,3}}\s+{re.escape(key)}\s*$", re.M | re.I
    )
    m = sec_re.search(text)
    if m:
        rest = text[m.end():]
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                break
            return _strip_md(line)
    return None


def check_file(path: Path) -> tuple[list[dict], list[dict], int | None]:
    findings: list[dict] = []
    notes: list[dict] = []
    name = path.name
    m = FILENAME_RE.match(name)
    if not m:
        findings.append(
            {"file": name, "code": "adr-filename", "detail": "expected NNNN-lowercase-slug.md"}
        )
        return findings, notes, None
    number = int(m.group(1))

    text = path.read_text(encoding="utf-8", errors="replace")

    status_val = extract_meta(text, "Status")
    if not status_val:
        findings.append({"file": name, "code": "adr-status", "detail": "Status is required (metadata or ## Status)"})
    else:
        first_word = re.split(r"[\s(,:]", status_val.strip().lower(), maxsplit=1)[0]
        if first_word and first_word not in KNOWN_STATUS:
            findings.append(
                {
                    "file": name,
                    "code": "adr-status-word",
                    "detail": f"unrecognised status lead {first_word!r}; expected one of {sorted(KNOWN_STATUS)}",
                }
            )

    date_val = extract_meta(text, "Date")
    if not date_val:
        findings.append({"file": name, "code": "adr-date", "detail": "Date is required (metadata or ## Date)"})
    elif not DATE_VALUE_RE.search(date_val):
        findings.append(
            {"file": name, "code": "adr-date-format", "detail": "Date must contain YYYY-MM-DD"}
        )

    headings = {norm_heading(h.group(2)) for h in HEADING_RE.finditer(text)}
    for req in sorted(REQUIRED_SECTIONS):
        if req not in headings:
            findings.append(
                {"file": name, "code": "adr-section", "detail": f"missing required section: ## {req.title()}"}
            )
    if not headings.intersection(CONSEQUENCE_ALIASES):
        findings.append(
            {
                "file": name,
                "code": "adr-section",
                "detail": "missing a consequence/rationale/outcome section",
            }
        )

    return findings, notes, number


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="docs/adr", help="ADR directory (default: docs/adr)")
    ap.add_argument("--json", action="store_true", dest="json_out", help="emit JSON")
    args = ap.parse_args(argv)

    root = Path(args.dir)
    if not root.is_dir():
        msg = {"ok": False, "error": f"ADR directory not found: {root}"}
        if args.json_out:
            print(json.dumps(msg, indent=2))
        else:
            print(f"check-adr: {msg['error']}", file=sys.stderr)
        return 2

    files = sorted(p for p in root.iterdir() if p.suffix == ".md" and p.name[0].isdigit())
    findings: list[dict] = []
    notes: list[dict] = []
    numbers: list[tuple[int, str]] = []

    for path in files:
        f, n, num = check_file(path)
        findings.extend(f)
        notes.extend(n)
        if num is not None:
            numbers.append((num, path.name))

    seen: dict[int, str] = {}
    for num, name in numbers:
        if num in seen:
            findings.append(
                {
                    "file": name,
                    "code": "adr-duplicate",
                    "detail": f"number {num:04d} also used by {seen[num]}",
                }
            )
        else:
            seen[num] = name

    nums = sorted(seen)
    if nums:
        full = set(range(nums[0], nums[-1] + 1))
        gaps = sorted(full - set(nums))
        for g in gaps:
            notes.append({"code": "adr-sequence-gap", "detail": f"{g:04d} is absent (reported, not a failure)"})

    ok = not findings
    summary = {
        "ok": ok,
        "records": len(files),
        "findings": len(findings),
        "notes": len(notes),
        "details": findings,
        "reported": notes,
    }
    if args.json_out:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"FAIL {f['file']}: [{f['code']}] {f['detail']}")
        for n in notes:
            print(f"NOTE [{n['code']}] {n['detail']}")
        print(
            f"check-adr: {len(files)} record(s), {len(findings)} finding(s), "
            f"{len(notes)} note(s)"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
