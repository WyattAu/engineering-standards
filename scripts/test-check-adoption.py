#!/usr/bin/env python3
"""Self-test for check-adoption.py: one mutation per rule.

Imports the checker, deep-copies a valid document, mutates one field, and
asserts the expected finding code appears. A rule that stops firing means a
candidate can be taken into the estate without its licence or its cost
being stated.
"""

from __future__ import annotations

import copy
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("adoption", os.path.join(HERE, "check-adoption.py"))
adoption = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adoption)

BASE = {
    "schema": "wyattau.candidates/1",
    "measured": "2026-11-09",
    "candidates": [
        {
            "name": "owner/repo",
            "url": "https://github.com/owner/repo",
            "language": "Rust",
            "license": "MIT",
            "license_verified": True,
            "stars": 1234,
            "pushed": "2026-11-01",
            "open_issues": 12,
            "archived": False,
            "layer": "L2",
            "decision": "adopt",
            "rationale": "Covers a concern the estate does not own yet, actively released.",
            "source": "https://github.com/owner/repo",
            "review_by": "2027-02-07",
        }
    ],
}

CASES = [
    ("clean", None, None, None),
    ("bad-decision", "decision", "maybe", "decision"),
    ("copyleft-fork", "license", "AGPL-3.0", "copyleft"),
    ("unverified-adopt", "license_verified", False, "license-unverified"),
    ("short-rationale", "rationale", "because", "rationale"),
    ("adopt-no-layer", "layer", None, "layer"),
    ("bad-url", "url", "https://gitlab.com/owner/repo", "url"),
    ("hold-no-question", "decision", "hold", "hold-question"),
    ("review-too-far", "review_by", "2028-01-01", "review-by"),
    ("no-source", "source", None, "source"),
]


def main():
    failures = []
    for name, field, value, expected in CASES:
        document = copy.deepcopy(BASE)
        if field:
            document["candidates"][0][field] = value
        if name == "copyleft-fork":
            document["candidates"][0]["decision"] = "fork"
        codes = {finding["code"] for finding in adoption.audit(document)}
        if expected is None:
            if codes:
                failures.append("%s: expected clean, got %s" % (name, sorted(codes)))
        elif expected not in codes:
            failures.append("%s: expected %s, got %s" % (name, expected, sorted(codes)))
    if failures:
        print("test-check-adoption: FAIL (%d)" % len(failures))
        for failure in failures:
            print("  " + failure)
        return 1
    print("test-check-adoption: PASS (%d fixtures)" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
