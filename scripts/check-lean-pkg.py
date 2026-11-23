#!/usr/bin/env python3
"""check-lean-pkg: LEAN-PKG oracle — packaging, toolchain, gates, inventory.

Validates Lean proof packages against docs/lean-pkg.md (LEAN-PKG):
  LP-1 lakefile.toml metadata: name, version, description, license
  LP-2 lean-toolchain pinned and equal to the fleet baseline (--baseline)
  LP-3 a CI workflow gates on the sorry grep ("declaration uses")
  LP-4 README postulate/native_decide inventory exists when axioms exist
  LP-6 every proof file under the library source dir is covered by a
       lakefile.toml roots entry (orphans fail; lakefile.lean -> REVIEW note)

Packages are discovered by scanning a directory root for repos containing
lean-toolchain. Packages using lakefile.lean (Lean-DSL config) are reported
as REVIEW rather than failed: their shape cannot be parsed here without a
Lean toolchain, and guessing would be the false confidence this oracle
exists to prevent.

Usage:
    check-lean-pkg.py [--root DIR] [--baseline VER] [--json]
Exit codes: 0 clean, 1 findings, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_BASELINE = "leanprover/lean4:v4.35.0"
DEFAULT_ROOT = os.path.expanduser("~/dev/src/github.com/WyattAu")
TOOLCHAIN_RE = re.compile(r"^leanprover/lean4:v\d+\.\d+\.\d+$")
META_FIELDS = ("name", "version", "description", "license")


def check_package(pkg: Path, baseline: str, siblings: set[Path]) -> list[str]:
    findings: list[str] = []
    name = pkg.name

    # git worktree of another scanned repo? Its branch state is historical;
    # report the main repo instead of four duplicate findings.
    dotgit = pkg / ".git"
    if dotgit.is_file():
        gitdir = dotgit.read_text().strip()
        m = re.match(r"gitdir: (.+)/\.git/worktrees/", gitdir)
        if m and Path(m.group(1)) in siblings:
            return [f"{name}: worktree of {Path(m.group(1)).name} — see main repo"]

    # LP-2 toolchain pin
    tc = pkg / "lean-toolchain"
    if not tc.is_file():
        return [f"{name}: no lean-toolchain (LP-2 FAIL)"]
    pin = tc.read_text().strip()
    if not TOOLCHAIN_RE.match(pin):
        findings.append(f"{name}: toolchain pin '{pin}' not leanprover/lean4:vX.Y.Z (LP-2)")
    elif pin != baseline:
        findings.append(f"{name}: toolchain {pin} != baseline {baseline} (LP-2 drift)")

    lf_toml = pkg / "lakefile.toml"
    lf_lean = pkg / "lakefile.lean"
    if lf_lean.is_file() and not lf_toml.is_file():
        findings.append(f"{name}: lakefile.lean — REVIEW (LP-1/LP-6 not machine-checkable)")
        return findings
    if not lf_toml.is_file():
        findings.append(f"{name}: no lakefile (LP-1 FAIL)")
        return findings
    text = lf_toml.read_text()

    has_requires = "[[require]]" in text or "[require]" in text
    has_libs = "[[lean_lib]]" in text or "[lean_lib]" in text
    if has_requires and not has_libs:
        # Consumer shim: requires proof packages, owns no proof source.
        # LP-2/LP-3 still apply; LP-1/LP-4/LP-6 are package concerns.
        if pin != baseline:
            findings.append(f"{name}: consumer toolchain {pin} != baseline {baseline} (LP-2)")
        ci_ok = False
        wf_dir = pkg / ".github" / "workflows"
        if wf_dir.is_dir():
            for wf in wf_dir.glob("*.y*ml"):
                if ("lean-action" in wf.read_text(errors="replace")
                        or "elan" in wf.read_text(errors="replace")) \
                        and "declaration uses" in wf.read_text(errors="replace"):
                    ci_ok = True
                    break
        if not ci_ok:
            findings.append(f"{name}: consumer shim lacks CI sorry gate (LP-3)")
        if findings:
            return findings
        return []

    # LP-1 metadata
    for field in META_FIELDS:
        if not re.search(rf"^{field}\s*=", text, re.M):
            findings.append(f"{name}: lakefile.toml missing '{field}' (LP-1)")

    # LP-3 sorry gate in CI
    ci_ok = False
    wf_dir = pkg / ".github" / "workflows"
    if wf_dir.is_dir():
        for wf in wf_dir.glob("*.y*ml"):
            body = wf.read_text(errors="replace")
            if ("lean-action" in body or "elan" in body) and "declaration uses" in body:
                ci_ok = True
                break
    if not ci_ok:
        findings.append(f"{name}: no CI sorry gate (lean-action/elan + 'declaration uses') (LP-3)")

    # LP-4 postulate inventory when axioms exist
    src_axioms = 0
    for lean in pkg.glob("src/**/*.lean"):
        src_axioms += len(re.findall(r"^axiom\b", lean.read_text(errors="replace"), re.M))
    readme = pkg / "README.md"
    if src_axioms and readme.is_file():
        body = readme.read_text(errors="replace")
        if "ostulate" not in body and "xiom" not in body:
            findings.append(f"{name}: {src_axioms} axioms, no README inventory (LP-4)")

    # LP-6 roots coverage (lakefile.toml only)
    # Parse [[lean_lib]] blocks: explicit `roots`, else the lib name is the
    # umbrella root (module L.lean + L/**). [[lean_exe]] root modules count.
    lib_blocks = re.split(r"\[\[lean_lib\]\]", text)[1:]
    covered_roots: set[str] = set()
    for block in lib_blocks:
        stop = block.find("[[")
        body = block[:stop] if stop != -1 else block
        lib_name = re.search(r'^name\s*=\s*"([^"]+)"', body, re.M)
        roots_m = re.search(r'roots\s*=\s*\[([^\]]*)\]', body, re.S)
        explicit = re.findall(r'"([^"]+)"', roots_m.group(1)) if roots_m else []
        if explicit:
            covered_roots.update(explicit)
        elif lib_name:
            covered_roots.add(lib_name.group(1))
    for exe_root in re.findall(r'\[\[lean_exe\]\][^[]*?root\s*=\s*"([^"]+)"', text, re.S):
        covered_roots.add(exe_root)
    root_norm = {r.replace(".", "/").removesuffix(".lean") for r in covered_roots}
    srcdir = Path(pkg)
    m = re.search(r'^srcDir\s*=\s*"([^"]+)"', text, re.M)
    if m:
        srcdir = pkg / m.group(1)
    if srcdir.is_dir():
        files = {
            str(p.relative_to(srcdir))
            for p in srcdir.rglob("*.lean")
            if ".lake" not in p.relative_to(pkg).parts
        }
        for f in sorted(files):
            stem = f.removesuffix(".lean")
            ok = any(
                stem == r or stem.startswith(r + "/") or stem.endswith("/" + r)
                for r in root_norm
            )
            if not ok:
                findings.append(f"{name}: {f} not covered by any lakefile root (LP-6)")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="LEAN-PKG oracle")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="directory scanned for packages")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, help="fleet toolchain baseline")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not Path(args.root).is_dir():
        print(f"check-lean-pkg: root not found: {args.root}", file=sys.stderr)
        return 2

    pkgs = sorted(
        p.parent for p in Path(args.root).glob("*/lean-toolchain")
    )
    if not pkgs:
        print(f"check-lean-pkg: no lean packages under {args.root}")
        return 0

    siblings = {p.parent.resolve() for p in Path(args.root).glob("*/lean-toolchain")}
    all_findings: dict[str, list[str]] = {}
    for pkg in pkgs:
        f = check_package(pkg, args.baseline, siblings)
        if f:
            all_findings[pkg.name] = f

    if args.json:
        print(json.dumps({"baseline": args.baseline, "packages": len(pkgs),
                          "findings": all_findings}, indent=2))
    else:
        print(f"check-lean-pkg: {len(pkgs)} packages, baseline {args.baseline}")
        for pkg, f in all_findings.items():
            for line in f:
                print(f"  ✗ {line}")
        clean = len(pkgs) - len(all_findings)
        print(f"  {clean}/{len(pkgs)} clean" if clean else "  0 packages clean")
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
