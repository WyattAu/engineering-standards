#!/usr/bin/env python3
"""Self-test for scripts/check-dependabot-cooldown.py. Stdlib only."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_dep_cooldown", Path(__file__).with_name("check-dependabot-cooldown.py")
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)
check = mod.check_cooldown


def rules(findings):
    return sorted({r for r, _, _ in findings})


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def dep(root: Path, text: str, name: str = ".github/dependabot.yml") -> Path:
    write(root / name, text)
    return root


VALID_GHA = """\
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    cooldown:
      default-days: 7
"""

VALID_CARGO = """\
version: 2
updates:
  - package-ecosystem: "cargo"
    directory: "/"
    schedule:
      interval: "weekly"
    cooldown:
      semver-major-days: 30
      semver-minor-days: 7
      semver-patch-days: 3
"""

VALID_DEFAULT30 = """\
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    cooldown:
      default-days: 30
"""


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # 1 valid github-actions
        r = base / "ok_gha"; r.mkdir(); dep(r, VALID_GHA)
        f = check(r)
        if f: print("FAIL ok_gha", f); fails += 1

        # 2 valid cargo semver fields
        r = base / "ok_cargo"; r.mkdir(); dep(r, VALID_CARGO)
        f = check(r)
        if f: print("FAIL ok_cargo", f); fails += 1

        # 3 valid npm with default-days 30 baseline
        r = base / "ok_def30"; r.mkdir(); dep(r, VALID_DEFAULT30)
        f = check(r)
        if f: print("FAIL ok_def30", f); fails += 1

        # 4 missing file
        r = base / "missing"; r.mkdir()
        f = check(r)
        if rules(f) != ["CD-1"]: print("FAIL missing", f); fails += 1

        # 5 empty file
        r = base / "empty"; r.mkdir(); dep(r, "")
        f = check(r)
        if rules(f) != ["CD-1"]: print("FAIL empty", f); fails += 1

        # 6 no updates key
        r = base / "noup"; r.mkdir(); dep(r, "version: 2\n")
        f = check(r)
        if rules(f) != ["CD-1"]: print("FAIL noup", f); fails += 1

        # 7 entry missing cooldown
        r = base / "nocd"; r.mkdir(); dep(r, """\
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
""")
        f = check(r)
        if rules(f) != ["CD-2"]: print("FAIL nocd", f); fails += 1

        # 8 gha missing default-days
        r = base / "gha_nodd"; r.mkdir(); dep(r, """\
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    cooldown: {}
""")
        # our parser may treat inline {} oddly; also test block form
        dep(r, """\
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    cooldown:
      semver-major-days: 30
""")
        f = check(r)
        if "CD-3" not in rules(f): print("FAIL gha_nodd", f); fails += 1

        # 9 gha default-days too low
        r = base / "gha_low"; r.mkdir(); dep(r, """\
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    cooldown:
      default-days: 3
""")
        f = check(r)
        if rules(f) != ["CD-3"]: print("FAIL gha_low", f); fails += 1

        # 10 cargo missing semver fields (no default)
        r = base / "cargo_miss"; r.mkdir(); dep(r, """\
version: 2
updates:
  - package-ecosystem: "cargo"
    directory: "/"
    cooldown:
      semver-minor-days: 7
""")
        f = check(r)
        if "CD-3" not in rules(f): print("FAIL cargo_miss", f); fails += 1

        # 11 cargo low major
        r = base / "cargo_low"; r.mkdir(); dep(r, """\
version: 2
updates:
  - package-ecosystem: "cargo"
    directory: "/"
    cooldown:
      semver-major-days: 14
      semver-minor-days: 7
      semver-patch-days: 3
""")
        f = check(r)
        if rules(f) != ["CD-3"]: print("FAIL cargo_low", f); fails += 1

        # 12 dependabot.yaml alternate name accepted
        r = base / "yaml_alt"; r.mkdir(); dep(r, VALID_GHA, ".github/dependabot.yaml")
        f = check(r)
        if f: print("FAIL yaml_alt", f); fails += 1

    if fails:
        print(f"test-check-dependabot-cooldown: {fails} failure(s)")
        return 1
    print("test-check-dependabot-cooldown: PASS (12 fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
