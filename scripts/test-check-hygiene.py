#!/usr/bin/env python3
"""Self-test for scripts/check-hygiene.py. Stdlib only."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("check_hygiene", Path(__file__).with_name("check-hygiene.py"))
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)
check = mod.check


def rules(findings):
    return sorted({r for r, _, _ in findings})


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def valid_repo(root: Path) -> None:
    write(root / "SECURITY.md", "Report vulnerabilities to security@example.com. Do not open a public issue.\n")
    write(root / ".github/CODEOWNERS", "* @owner\n")
    write(root / ".github/ISSUE_TEMPLATE/bug_report.md", "## bug\n")
    write(root / ".github/PULL_REQUEST_TEMPLATE.md", "## summary\n")


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # 1 valid
        r = root / "ok"; r.mkdir(); valid_repo(r)
        f = check(r)
        if f: print("FAIL valid", f); fails += 1

        # 2 missing security
        r = root / "no_sec"; r.mkdir(); valid_repo(r); (r / "SECURITY.md").unlink()
        f = check(r)
        if rules(f) != ["RH-1"]: print("FAIL no_sec", f); fails += 1

        # 3 security no reporting path
        r = root / "bad_sec"; r.mkdir(); valid_repo(r); write(r / "SECURITY.md", "Be safe.\n")
        f = check(r)
        if "RH-1" not in rules(f): print("FAIL bad_sec", f); fails += 1

        # 4 public issue only
        r = root / "pub"; r.mkdir(); valid_repo(r); write(r / "SECURITY.md", "Please open a public issue to report bugs.\n")
        f = check(r)
        if "RH-1" not in rules(f): print("FAIL pub", f); fails += 1

        # 5 missing codeowners
        r = root / "no_co"; r.mkdir(); valid_repo(r); (r / ".github/CODEOWNERS").unlink()
        f = check(r)
        if rules(f) != ["RH-2"]: print("FAIL no_co", f); fails += 1

        # 6 codeowners comments only
        r = root / "co_com"; r.mkdir(); valid_repo(r); write(r / ".github/CODEOWNERS", "# nobody\n\n")
        f = check(r)
        if "RH-2" not in rules(f): print("FAIL co_com", f); fails += 1

        # 7 missing issue template
        r = root / "no_it"; r.mkdir(); valid_repo(r)
        for x in (r / ".github/ISSUE_TEMPLATE").iterdir(): x.unlink()
        (r / ".github/ISSUE_TEMPLATE").rmdir()
        f = check(r)
        if rules(f) != ["RH-3"]: print("FAIL no_it", f); fails += 1

        # 8 issue config.yml only, non-empty, ok
        r = root / "it_cfg"; r.mkdir(); valid_repo(r)
        for x in (r / ".github/ISSUE_TEMPLATE").iterdir(): x.unlink()
        write(r / ".github/ISSUE_TEMPLATE/config.yml", "blank_issues_enabled: false\n")
        f = check(r)
        if f: print("FAIL it_cfg", f); fails += 1

        # 9 missing pr template
        r = root / "no_pr"; r.mkdir(); valid_repo(r); (r / ".github/PULL_REQUEST_TEMPLATE.md").unlink()
        f = check(r)
        if rules(f) != ["RH-4"]: print("FAIL no_pr", f); fails += 1

        # 10 accepts alt locations
        r = root / "alt"; r.mkdir()
        write(r / "docs/SECURITY.md", "Contact https://example.com/security\n")
        write(r / "docs/CODEOWNERS", "* @owner\n")
        write(r / ".github/ISSUE_TEMPLATE.md", "hi\n")
        write(r / "docs/pull_request_template.md", "hi\n")
        f = check(r)
        if f: print("FAIL alt", f); fails += 1

    if fails:
        print(f"test-check-hygiene: {fails} failure(s)")
        return 1
    print("test-check-hygiene: PASS (10 fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
