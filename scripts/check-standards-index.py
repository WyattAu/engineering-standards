#!/usr/bin/env python3
"""check-standards-index: the index must not cite files that do not exist.

Validates STANDARDS-INDEX.md (SM-9):
  - every table row has the six expected columns
  - every `Standard` cell is `none`, a path in this repo, or `ext:<repo>/<path>`
  - every `Gate` cell is `none`, an existing path, `tool:<name>`, or
    `repo:<workflow>`
  - `Enforcement` is one of gated | advisory | declared | none
  - the `## Totals` table matches the counts the rows actually produce

Cross-repo references use `ext:<repo>/<path>` because CI checks out this
repository alone. With a sibling checkout present (the normal local layout)
each reference is verified; without one it is listed as unverified rather
than passed silently, and `--strict-external` turns that list into a failure
for runs that do have the siblings.

Usage: check-standards-index.py [STANDARDS-INDEX.md] [--json] [--strict-external]
Exit codes: 0 clean, 1 drift, 2 usage error.
"""

from __future__ import annotations

import json
import os
import sys

COLUMNS = ["Concern", "Standard", "Requirements", "Gate", "Enforcement", "Adoption"]
ENFORCEMENT = {"gated", "advisory", "declared", "none"}
GATE_SUFFIXES = (".py", ".sh", ".yml", ".yaml")
TOTAL_KEYS = {
    "Concerns listed": "total",
    "With a standard": "with_standard",
    "With a machine check": "with_gate",
    "Gated": "gated",
    "Advisory": "advisory",
    "Declared only": "declared",
    "No standard": "none",
}


def cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse(path):
    rows = []
    totals = {}
    in_totals = False
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("## Totals"):
                in_totals = True
                continue
            if stripped.startswith("## ") and not stripped.startswith("## Totals"):
                in_totals = False
            if not stripped.startswith("|"):
                continue
            parts = cells(stripped)
            if in_totals:
                if len(parts) == 2 and parts[0] in TOTAL_KEYS:
                    totals[parts[0]] = parts[1]
                continue
            if parts[0] in COLUMNS or set(parts[0]) <= set("-: "):
                continue
            if len(parts) == len(COLUMNS):
                rows.append(dict(zip(COLUMNS, parts)))
    return rows, totals


def looks_like_path(value):
    if value == "none":
        return False
    return "/" in value or value.endswith(GATE_SUFFIXES)


def audit(root, rows, totals, strict_external=False):
    parent = os.path.dirname(root)
    findings = []
    unverified = []
    counts = {"total": len(rows), "with_standard": 0, "with_gate": 0,
              "gated": 0, "advisory": 0, "declared": 0, "none": 0}

    def check_ref(value, kind, label):
        """Verify one reference. Returns True when the reference is acceptable."""
        if value.startswith("ext:"):
            target = os.path.join(parent, value[4:])
            if os.path.exists(target):
                return True
            if strict_external:
                findings.append(
                    "%s: %s external ref unresolvable: %s" % (label, kind, value)
                )
            else:
                unverified.append(value)
            return True
        if os.path.exists(os.path.join(root, value)):
            return True
        findings.append("%s: %s path missing: %s" % (label, kind, value))
        return False

    for row in rows:
        label = row["Concern"]
        standard = row["Standard"]
        if standard != "none":
            counts["with_standard"] += 1
            check_ref(standard, "standard", label)

        gate = row["Gate"]
        if gate == "none":
            pass
        elif gate.startswith("tool:"):
            # An external tool or suite (zizmor, cargo-llvm-cov, a crate's
            # test suite). A machine check, but not a file in this repo.
            counts["with_gate"] += 1
        elif gate.startswith("repo:"):
            # Implemented per repository, never counted as estate-wide; its
            # adoption is the number in the Adoption column.
            pass
        elif gate.startswith("ext:") or looks_like_path(gate):
            counts["with_gate"] += 1
            check_ref(gate, "gate", label)
        else:
            findings.append(
                "%s: gate %r must be none, an existing path, ext:<repo>/<path>, "
                "tool:<name>, or repo:<workflow>" % (label, gate)
            )

        enforcement = row["Enforcement"]
        if enforcement not in ENFORCEMENT:
            findings.append(
                "%s: enforcement %r not in %s" % (label, enforcement, sorted(ENFORCEMENT))
            )
            continue
        if enforcement in counts:
            counts[enforcement] += 1
        if enforcement == "gated" and standard == "none":
            findings.append("%s: gated without a standard" % label)
        if enforcement == "gated" and (gate == "none" or gate.startswith("repo:")):
            findings.append("%s: gated without an estate gate" % label)

    for label, value in totals.items():
        key = TOTAL_KEYS[label]
        try:
            declared = int(value)
        except ValueError:
            findings.append("totals: %s is not a number: %r" % (label, value))
            continue
        if declared != counts[key]:
            findings.append(
                "totals: %s says %d, rows produce %d" % (label, declared, counts[key])
            )
    return findings, counts, unverified


def main(argv):
    args = [arg for arg in argv[1:] if not arg.startswith("--")]
    as_json = "--json" in argv[1:]
    strict = "--strict-external" in argv[1:]
    index = args[0] if args else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "STANDARDS-INDEX.md"
    )
    if not os.path.exists(index):
        sys.stderr.write("check-standards-index: no index at %s\n" % index)
        return 2
    root = os.path.dirname(os.path.abspath(index))
    rows, totals = parse(index)
    if not rows:
        sys.stderr.write("check-standards-index: no concern rows parsed from %s\n" % index)
        return 2
    findings, counts, unverified = audit(root, rows, totals, strict)
    if as_json:
        print(json.dumps(
            {"findings": findings, "counts": counts, "unverified_external": unverified},
            indent=2,
        ))
    else:
        for finding in findings:
            print("FAIL %s" % finding)
        if unverified:
            print(
                "note: %d external reference(s) not checked (no sibling checkout); "
                "run with --strict-external where the siblings exist" % len(unverified)
            )
        print(
            "check-standards-index: %d concerns, %d with a standard, %d gated, "
            "%d advisory, %d declared, %d none, %d findings"
            % (
                counts["total"],
                counts["with_standard"],
                counts["gated"],
                counts["advisory"],
                counts["declared"],
                counts["none"],
                len(findings),
            )
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
