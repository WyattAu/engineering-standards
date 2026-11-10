#!/usr/bin/env python3
"""check-dependabot-cooldown.py - DEPENDENCY-COOLDOWN (CD-1..CD-3).

Stdlib only. Checks a repository's .github/dependabot.yml for cooldown
settings meeting OMNI-CORE 11d minimums.
Exit 0 on success, 1 on findings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FINDING = tuple[str, str, str]  # rule, path, message

CONFIG_NAMES = [".github/dependabot.yml", ".github/dependabot.yaml"]

MIN_GHA_DEFAULT = 7
MIN_MAJOR = 30
MIN_MINOR = 7
MIN_PATCH = 3


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def parse_updates(text: str) -> list[dict]:
    """Minimal indentation-aware parse of dependabot updates entries.

    Extracts per-entry: ecosystem, cooldown (dict of key->int), and whether
    a cooldown mapping was present. Not a general YAML parser.
    """
    lines = text.splitlines()
    # locate 'updates:' at top level
    in_updates = False
    updates_indent = None
    entries: list[dict] = []
    current: dict | None = None
    in_cooldown = False
    cooldown_indent = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.lstrip(" ")
        indent = len(raw) - len(stripped)
        # skip blanks/comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if re.match(r"^updates\s*:\s*$", stripped):
            in_updates = True
            updates_indent = indent
            i += 1
            continue

        if not in_updates:
            i += 1
            continue

        # end of updates block: new top-level key at same/less indent
        if indent <= (updates_indent or 0) and re.match(r"^[\w-]+\s*:", stripped):
            break

        # new list item (update entry) - detect '- ' at entry level
        m_item = re.match(r"^-\s+(.*)$", stripped)
        if m_item and (current is None or indent <= (current.get("_indent", indent))):
            # start new entry; flush cooldown state
            current = {"_indent": indent, "ecosystem": None, "cooldown": None, "has_cooldown": False}
            entries.append(current)
            in_cooldown = False
            cooldown_indent = None
            rest = m_item.group(1)
            # handle inline 'key: value' on the '-' line
            m_kv = re.match(r"^([\w-]+)\s*:\s*(.*)$", rest)
            if m_kv:
                k, v = m_kv.group(1), m_kv.group(2).strip()
                if k == "package-ecosystem":
                    current["ecosystem"] = strip_quotes(v)
                elif k == "cooldown":
                    current["has_cooldown"] = True
                    if v and v not in ("|", ">"):
                        # unlikely inline mapping, but note presence
                        current["cooldown"] = current["cooldown"] or {}
                    else:
                        current["cooldown"] = {}
                        in_cooldown = True
                        cooldown_indent = None  # set on first child
            i += 1
            continue

        if current is None:
            i += 1
            continue

        # inside cooldown block
        if in_cooldown:
            if cooldown_indent is None:
                if indent > current["_indent"]:
                    cooldown_indent = indent
                else:
                    in_cooldown = False
            if in_cooldown and cooldown_indent is not None:
                if indent < cooldown_indent:
                    in_cooldown = False
                elif indent == cooldown_indent:
                    m_kv = re.match(r"^([\w-]+)\s*:\s*(.*)$", stripped)
                    if m_kv:
                        k, v = m_kv.group(1), m_kv.group(2).strip()
                        try:
                            current["cooldown"][k] = int(strip_quotes(v))
                        except (ValueError, TypeError):
                            pass
                    i += 1
                    continue
                else:
                    # deeper nested, ignore
                    i += 1
                    continue

        # key: value inside current entry (not in cooldown)
        if indent > current["_indent"]:
            m_kv = re.match(r"^([\w-]+)\s*:\s*(.*)$", stripped)
            if m_kv:
                k, v = m_kv.group(1), m_kv.group(2).strip()
                if k == "package-ecosystem":
                    current["ecosystem"] = strip_quotes(v)
                elif k == "cooldown":
                    current["has_cooldown"] = True
                    current["cooldown"] = {}
                    in_cooldown = True
                    cooldown_indent = None
            i += 1
            continue

        # indent fell back to entry level or below - could be sibling entry handled above
        i += 1

    return entries


def check_cooldown(root: Path) -> list[FINDING]:
    cfg = None
    rel = None
    for name in CONFIG_NAMES:
        p = root / name
        if p.is_file():
            cfg = p
            rel = name
            break
    if cfg is None:
        return [("CD-1", ".github/dependabot.yml", "missing; add dependabot config with per-entry cooldown (OMNI-CORE 11d)")]

    text = read_text(cfg)
    if not text.strip():
        return [("CD-1", rel, "file is empty")]

    if "updates" not in text:
        return [("CD-1", rel, "no 'updates:' key found")]

    entries = parse_updates(text)
    if not entries:
        return [("CD-2", rel, "no update entries parsed under 'updates:'")]

    findings: list[FINDING] = []
    for idx, e in enumerate(entries):
        eco = e.get("ecosystem") or f"<entry {idx}>"
        label = f"{rel} (package-ecosystem: {eco})"
        if not e.get("has_cooldown"):
            findings.append(("CD-2", label, "missing 'cooldown:' mapping"))
            continue
        cd = e.get("cooldown") or {}
        if eco == "github-actions":
            dd = cd.get("default-days")
            if dd is None:
                findings.append(("CD-3", label, "github-actions requires 'default-days' in cooldown"))
            elif dd < MIN_GHA_DEFAULT:
                findings.append(("CD-3", label, f"default-days {dd} < {MIN_GHA_DEFAULT} (minimum for github-actions)"))
        else:
            # non-github-actions: semver-specific mins, with default-days baseline if >=30
            dd = cd.get("default-days")
            major = cd.get("semver-major-days")
            minor = cd.get("semver-minor-days")
            patch = cd.get("semver-patch-days")

            def eff(val, baseline, dflt):
                if val is not None:
                    return val
                if dflt is not None:
                    return dflt
                return baseline  # None means not set and no default

            # if default-days provided and >= 30, it can cover all; else need specifics
            maj_eff = major if major is not None else dd
            min_eff = minor if minor is not None else dd
            pat_eff = patch if patch is not None else dd

            missing = []
            if maj_eff is None:
                missing.append("semver-major-days")
            elif maj_eff < MIN_MAJOR:
                findings.append(("CD-3", label, f"semver-major-days {maj_eff} < {MIN_MAJOR}"))
            if min_eff is None:
                missing.append("semver-minor-days")
            elif min_eff < MIN_MINOR:
                findings.append(("CD-3", label, f"semver-minor-days {min_eff} < {MIN_MINOR}"))
            if pat_eff is None:
                missing.append("semver-patch-days")
            elif pat_eff < MIN_PATCH:
                findings.append(("CD-3", label, f"semver-patch-days {pat_eff} < {MIN_PATCH}"))
            if missing:
                findings.append(("CD-3", label, "missing cooldown fields: " + ", ".join(missing) + " (or default-days >= 30)"))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="repository root to check")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.path).resolve()
    findings = check_cooldown(root)
    if args.json:
        print(json.dumps([{"rule": r, "path": p, "message": m} for r, p, m in findings], indent=2))
    else:
        for r, p, m in findings:
            print(f"{r}: {p}: {m}")
        print(f"check-dependabot-cooldown: {root.name} - {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
