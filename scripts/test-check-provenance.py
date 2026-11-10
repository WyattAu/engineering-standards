#!/usr/bin/env python3
"""Self-test for scripts/check-provenance.py. Stdlib only."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_provenance", Path(__file__).with_name("check-provenance.py")
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)
check = mod.check_provenance


def rules(findings):
    return sorted({r for r, _, _ in findings})


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


GOOD_WF = """\
name: attest
permissions:
  contents: read
  id-token: write
  attestations: write
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/attest-build-provenance@abc123
        with:
          subject-path: dist/*
"""


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # 1 valid attest.yml
        r = base / "ok"; r.mkdir(); write(r / ".github/workflows/attest.yml", GOOD_WF)
        f = check(r)
        if f: print("FAIL ok", f); fails += 1

        # 2 explicit no distributables
        r = base / "none"; r.mkdir(); write(r / ".provenance-scope", "distributable: none\n")
        f = check(r)
        if f: print("FAIL none", f); fails += 1

        # 3 distributables: none also ok
        r = base / "nones"; r.mkdir(); write(r / ".provenance-scope", "distributables: none\n")
        f = check(r)
        if f: print("FAIL nones", f); fails += 1

        # 4 missing both
        r = base / "miss"; r.mkdir()
        f = check(r)
        if rules(f) != ["PV-1"]: print("FAIL miss", f); fails += 1

        # 5 scope file present but not declaring none
        r = base / "badscope"; r.mkdir(); write(r / ".provenance-scope", "distributable: some\n")
        f = check(r)
        if rules(f) != ["PV-1"]: print("FAIL badscope", f); fails += 1

        # 6 attest workflow missing action
        r = base / "noact"; r.mkdir(); write(r / ".github/workflows/attest.yml", """\
permissions:
  id-token: write
  attestations: write
jobs:
  a:
    steps:
      - run: echo hi
""")
        f = check(r)
        if "PV-1" not in rules(f): print("FAIL noact", f); fails += 1

        # 7 missing id-token permission
        r = base / "noid"; r.mkdir(); write(r / ".github/workflows/attest.yml", """\
permissions:
  attestations: write
jobs:
  a:
    steps:
      - uses: actions/attest-build-provenance@abc
""")
        f = check(r)
        if "PV-1" not in rules(f): print("FAIL noid", f); fails += 1

        # 8 missing attestations permission
        r = base / "noatt"; r.mkdir(); write(r / ".github/workflows/attest.yml", """\
permissions:
  id-token: write
jobs:
  a:
    steps:
      - uses: actions/attest-build-provenance@abc
""")
        f = check(r)
        if "PV-1" not in rules(f): print("FAIL noatt", f); fails += 1

        # 9 alternative workflow name (provenance.yml) accepted
        r = base / "prov"; r.mkdir(); write(r / ".github/workflows/provenance.yml", GOOD_WF)
        f = check(r)
        if f: print("FAIL prov", f); fails += 1

    if fails:
        print(f"test-check-provenance: {fails} failure(s)")
        return 1
    print("test-check-provenance: PASS (9 fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
