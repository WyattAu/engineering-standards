#!/usr/bin/env python3
"""tier-route: which OMNI-CORE CI tier does this repo get, and what fires?

Encodes OMNI-CORE's tier doctrine (A latency/concurrency primitives,
B default kits, C informational) and the per-language coverage-tier
table. Prints the tier, the coverage floor, and the required tooling.
Advisory output: the estate-audit remains the enforcement (OMNI-CORE 7).

Usage:
  tier-route.py --traits "latency,concurrency" --lang rust
  tier-route.py --kind informational --lang python
  tier-route.py --crate decimal-money
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TIERS_JSON = Path(__file__).resolve().parent / "estate-tiers.json"

COVERAGE = {
    "rust": (">=90%", ">=80%", ">=70%"),
    "python": (">=90%", ">=80%", ">=70%"),
    "go": (">=80%", ">=70%", ">=60%"),
    "haskell": (">=70%", ">=60%", ">=50%"),
    "cpp": ("host tests + flash/RAM size budgets instead of coverage %",) * 3,
}


def decide(traits: set[str], kind: str | None) -> tuple[str, str]:
    if kind == "informational":
        return "c", "informational content (OMNI doctrine: tier C until the flip date)"
    if "latency" in traits or "concurrency" in traits:
        return "a", "latency-relevant or concurrency primitive -> tier A (loom, miri, top coverage floor)"
    if kind == "library":
        return "b", "default kit -> tier B"
    return "b", "default tier B (state a reason in the repo README if tier A/C is claimed)"


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--traits", help="comma-separated: latency, concurrency, memory, parsing")
    ap.add_argument("--kind", choices=["library", "app", "informational"])
    ap.add_argument("--lang", choices=["rust", "python", "go", "haskell", "cpp"], default="rust")
    ap.add_argument("--crate", help="look up the estate layer (L0-L3) from estate-tiers.json")
    a = ap.parse_args()
    if not (a.traits or a.kind or a.crate):
        ap.print_help(file=sys.stderr)
        return 2

    traits = {t.strip().lower() for t in (a.traits or "").split(",") if t.strip()}
    tier, why = decide(traits, a.kind)
    cov = COVERAGE.get(a.lang, COVERAGE["rust"])
    floor = {"a": cov[0], "b": cov[1], "c": cov[2]}[tier]

    print(f"tier {tier} ({why})")
    print(f"coverage floor ({a.lang}): {floor}")
    if tier == "a" and a.lang == "rust":
        print("required tooling: loom (concurrency interleavings); miri when unsafe is present;")
        print("contract tests wired per the shared rust-kit workflow.")
    if tier in ("a", "b"):
        print("workflow: shared rust-kit CI workflow; scripts are canonical, CI mirrors them (OMNI-CORE 2).")
    else:
        print("informational tier: gates advisory until the flip date.")

    if a.crate and TIERS_JSON.is_file():
        data = json.loads(TIERS_JSON.read_text())
        layer = (data.get("tiers") or {}).get(a.crate)
        if layer:
            print(f"estate layer: {a.crate} = {layer} (context for review depth; CI tier is orthogonal)")
        else:
            print(f"estate layer: {a.crate} not in estate-tiers.json; classify in docs/layers.md first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
