#!/usr/bin/env python3
"""Estate audit — the single source of truth for WyattAu repo/crate health.

`estate.yml` is the manifest of record: one entry per repo, with its area,
status, and the crates.io packages it publishes. This script proves the
manifest still matches reality on three axes, and reports the two classes of
drift that silently rot an estate of this size:

  1. **Pin drift** — a crate pinned by exact version in a consumer repo
     (`estate-integration/Cargo.toml`) no longer matches the version
     published on crates.io. The consumer tests an artifact nobody ships.
  2. **Coverage debt** — a published crate is never composed by any
     consumer suite, so nothing proves it still works with its neighbours.

Usage:
    estate-audit.py                  # audit, human-readable report, exit 1 on errors
    estate-audit.py --json           # machine-readable findings
    estate-audit.py --sync           # refresh the *_seen metadata fields in estate.yml
    estate-audit.py --offline        # skip network (uses the last cached snapshot)

Exit codes:
    0  no errors (warnings allowed)
    1  manifest errors (missing repo, unpinned core crate, unowned crate)
    2  bad invocation / missing dependencies

Manifest schema (see ../estate.yml):
    repos.<name>.area      one of AREAS
    repos.<name>.status    one of STATUSES
    repos.<name>.crates    crates.io package names published from this repo
    repos.<name>.canonical_of  repo names this one supersedes
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("estate-audit.py needs PyYAML: pip install pyyaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "estate.yml"
CACHE = ROOT / ".estate-cache.json"
OWNER = "WyattAu"
# crates.io numeric owner id for the WyattAu account (from /api/v1/users/WyattAu)
CRATES_OWNER_ID = "404181"
# Repos that pin estate crates by exact version, and the file that does it.
CONSUMERS = ("WyattAu/estate-integration",)

UA = "wyatt-estate-audit (+https://github.com/WyattAu/engineering-standards)"
NET_TIMEOUT = 30

REPO_KEYS = {"area", "status", "notes", "crates", "canonical_of", "fork", "_seen"}

AREAS = {
    "infra",  # CI, templates, dotfiles, infra stacks, images
    "auth",   # credentials, identity, authorization
    "net",    # transports, proxies, gateways, wire codecs
    "obsv",   # telemetry, metrics, health, logging
    "money",  # money, ledger, billing, spreadsheets, reporting
    "data",   # storage, encoding, encoding/decoding, search
    "conc",   # concurrency, actors, pools, IPC
    "ui",     # leptos / charting / theming / design system
    "dx",     # dev tooling, testing, CI, templates
    "docs",   # documentation pipeline, publishing
    "app",    # applications and products
    "research",  # experiments, engines, models
    "personal",  # private personal repos
}

STATUSES = {
    "core",      # published + dogfooded in a consumer suite
    "support",   # published, active, not yet composed
    "orphan",    # published, no dogfood coverage, no recent activity
    "dormant",   # no meaningful activity for a long window
    "template",  # scaffolding for other repos
    "fork",      # upstream fork kept for vendoring/patching
    "personal",  # private, not part of the published estate
    "infra",     # CI/infra/tooling, not a published crate
}

# Published crates that are never dogfooded by design, with the reason. Keeps
# the coverage report honest instead of shouting about every lepto.
COVERAGE_EXEMPT = {
    "leptos-*": "UI components; exercised by crdt-demo / site, not by the API suites",
    "vane-*": "separate product monorepo with its own test suite",
    "polyfont-*": "editor plugin family, dormant since 2026-05",
    "suture-*": "separate product monorepo, under evaluation (see estate.yml notes)",
    "crawlkit-*": "separate product monorepo with its own test suite",
    "ply*": "charting library, wasm-first",
    "resilient-fetch": "superseded by fetch-kit; kept pinned for the migration round",
    "loop-retry": "repo retry-backoff; renamed package, same crate",
}

DORMANT_DAYS = 120  # no push for this long = dormant, unless pinned as core


# --------------------------------------------------------------------------
# network
# --------------------------------------------------------------------------

def _get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as fh:
        return json.loads(fh.read())


def fetch_repos() -> list[dict]:
    raw = subprocess.run(
        ["gh", "repo", "list", OWNER, "--limit", "400", "--json",
         "name,description,isArchived,isFork,pushedAt,visibility,primaryLanguage"],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(raw)


def fetch_crates() -> dict:
    """Every package published under the WyattAu crates.io account."""
    out: dict[str, dict] = {}
    page = 1
    while True:
        data = _get_json(
            f"https://crates.io/api/v1/crates?user_id={CRATES_OWNER_ID}&per_page=100&page={page}"
        )
        crates = data.get("crates") or []
        for c in crates:
            out[c["name"]] = {
                "max_stable": c.get("max_stable_version"),
                "updated": (c.get("updated_at") or "")[:10],
                "downloads": c.get("downloads", 0),
            }
        if len(crates) < 100:
            return out
        page += 1


def fetch_consumer_pins(repo: str, ref: str = "HEAD") -> dict[str, str]:
    """crate -> exact pinned version, from a consumer repo's Cargo.toml."""
    try:
        raw = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/Cargo.toml?ref={ref}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return {}
    import base64
    import tomllib

    text = base64.b64decode(json.loads(raw)["content"]).decode()
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        print(f"warn: could not parse {repo}/Cargo.toml: {exc}", file=sys.stderr)
        return {}

    pins: dict[str, str] = {}
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        for name, spec in (data.get(section) or {}).items():
            if isinstance(spec, str):
                ver, real = spec, name
            elif isinstance(spec, dict):
                # `pkg = { package = "other", version = "=1.2.3" }` renames.
                ver, real = spec.get("version"), spec.get("package", name)
            else:
                continue
            if isinstance(ver, str) and ver.startswith("="):
                pins[real] = ver[1:]
    return pins


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}


def save_cache(data: dict) -> None:
    CACHE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")


# --------------------------------------------------------------------------
# manifest
# --------------------------------------------------------------------------

class Manifest:
    def __init__(self, path: pathlib.Path):
        raw = yaml.safe_load(path.read_text())
        self.schema = raw.get("schema", 1)
        self.repos: dict[str, dict] = raw["repos"]
        self.pins_held: list[dict] = raw.get("pins_held") or []
        self.path = path

    def problems(self) -> list[str]:
        out = []
        for name, entry in sorted(self.repos.items()):
            if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
                out.append(f"{name}: illegal repo name")
            area = entry.get("area")
            if area not in AREAS:
                out.append(f"{name}: area {area!r} not in {sorted(AREAS)}")
            status = entry.get("status")
            if status not in STATUSES:
                out.append(f"{name}: status {status!r} not in {sorted(STATUSES)}")
            if not entry.get("area") or not entry.get("status"):
                out.append(f"{name}: needs both area and status")
            for sup in entry.get("canonical_of", []) or []:
                if sup not in self.repos:
                    out.append(f"{name}: canonical_of {sup!r} is not a known repo")
                elif sup == name:
                    out.append(f"{name}: canonical_of itself")
            for dep in entry.get("consumes", []) or []:
                if dep not in self.repos:
                    out.append(f"{name}: consumes {dep!r} is not a known repo")
            for key in sorted(entry):
                if key not in REPO_KEYS:
                    out.append(f"{name}: unknown key {key!r} (typo?)")
        return out

    def pin_problems(self) -> list[str]:
        out = []
        seen = set()
        for hold in self.pins_held:
            key = (hold.get("consumer"), hold.get("crate"))
            if key in seen:
                out.append(f"duplicate hold for {key}")
            seen.add(key)
            if not hold.get("reason"):
                out.append(f"hold on {key} has no reason")
            if hold.get("consumer") not in CONSUMERS:
                out.append(f"hold names an unknown consumer {hold.get('consumer')!r}")
        return out

    def dump(self) -> str:
        return self.path.read_text()


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------

def exempt(crate: str) -> str | None:
    for pattern, reason in COVERAGE_EXEMPT.items():
        if fnmatch(crate, pattern):
            return reason
    return None


def fnmatch(name: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return name.startswith(pattern[:-1])
    return name == pattern


def audit(man: Manifest, repos: list[dict], crates: dict, pins_by_repo: dict) -> list[dict]:
    findings: list[dict] = []
    gh = {r["name"]: r for r in repos}
    now = dt.datetime.now(dt.UTC)

    def add(kind: str, subject: str, msg: str, fix: str = "") -> dict:
        finding = {"kind": kind, "subject": subject, "message": msg, "fix": fix}
        findings.append(finding)
        return finding

    # --- manifest vs GitHub ------------------------------------------------
    for name in man.repos:
        if name not in gh:
            add("error", name, "manifest lists a repo GitHub does not return",
                "archive it, or fix the name")
    for name in gh:
        if name not in man.repos:
            add("error", name, "repo is missing from estate.yml",
                "add an entry with area+status, or mark it excluded")

    # --- manifest vs crates.io ---------------------------------------------
    declared: dict[str, str] = {}  # crate -> repo
    for repo, entry in man.repos.items():
        for crate in entry.get("crates", []) or []:
            if crate in declared:
                add("error", crate,
                    f"published by both {declared[crate]} and {repo} in the manifest",
                    "one repo owns the package")
            declared[crate] = repo
            if crate not in crates:
                add("error", crate, "manifest claims a crate that is not published",
                    "publish it or drop the entry")
    for crate, info in sorted(crates.items()):
        if crate not in declared:
            add("error", crate, "published under the account but unclaimed by any repo",
                "add it to the owning repo's crates list")

    # --- pin drift ---------------------------------------------------------
    # Only crates this account publishes are drift-checkable. Consumer repos
    # legitimately exact-pin third-party crates too (reqwest, tokio), and an
    # exact pin on something unpublished is the crate name being wrong.
    #
    # A pin may also be held behind deliberately, when a newer release
    # cannot be consumed yet. Those live in the manifest's `pins` block with
    # the reason, so the audit reports the hold instead of nagging about it
    # forever — and so the reason is reviewable rather than tribal.
    holds: dict[tuple[str, str], str] = {}
    for hold in man.pins_held or []:
        holds[(hold["consumer"], hold["crate"])] = hold["reason"]

    pinned_any: dict[str, str] = {}
    for consumer, pins in pins_by_repo.items():
        for crate, ver in sorted(pins.items()):
            if crate not in crates:
                severity = "error" if crate in declared else "info"
                add(severity, crate,
                    f"{consumer} exact-pins {crate} but no such crate is published "
                    "under this account",
                    "check the pin's spelling, or the crates.io owner id")
                continue
            pinned_any[crate] = consumer
            live = crates[crate]["max_stable"]
            if live and ver != live:
                held = holds.get((consumer, crate))
                finding = add("drift", crate,
                    f"{consumer} pins ={ver} but crates.io has {live} "
                    f"(published {crates[crate]['updated']})",
                    (f"held deliberately: {held}" if held
                     else f"bump the pin to ={live}, then fix whatever the bump broke"))
                if held:
                    finding["held"] = held

    # --- coverage debt -----------------------------------------------------
    # A repo's `core` status is satisfied when a consumer pins *any* crate it
    # publishes: sibling crates (derive macros, proc-macro halves, renamed
    # packages) are pulled transitively by that pin, so pinning them
    # separately would just duplicate the lockfile.
    pinned_by_repo: dict[str, set[str]] = {}
    for crate, consumer in pinned_any.items():
        repo = declared.get(crate)
        if repo:
            pinned_by_repo.setdefault(repo, set()).add(crate)

    for crate, repo in sorted(declared.items()):
        if crate in pinned_any or exempt(crate):
            continue
        siblings = pinned_by_repo.get(repo, set())
        if siblings:
            add("debt", crate,
                f"composed only transitively via {', '.join(sorted(siblings))}",
                "fine if intentional; pin it directly if it has its own surface")
            continue
        entry = man.repos[repo]
        if entry.get("status") == "core":
            add("error", crate,
                "status=core but no consumer pins it — the suite does not prove it",
                "pin it in a consumer suite, or demote the status")
        else:
            add("debt", crate,
                f"published, never composed by a consumer suite (repo {repo})",
                "add a suite that wires it, or record an exemption")

    # --- dormancy ----------------------------------------------------------
    for name, entry in sorted(man.repos.items()):
        meta = gh.get(name)
        if not meta or entry.get("status") in ("dormant", "personal"):
            continue
        pushed = (meta.get("pushedAt") or "")[:10]
        if not pushed:
            continue
        age = (now - dt.datetime.fromisoformat(pushed).replace(tzinfo=dt.UTC)).days
        if age > DORMANT_DAYS:
            add("dormant", name,
                f"last push {pushed} ({age}d) but status={entry['status']}",
                f"mark status=dormant, or set a dormancy exemption")

    return findings


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

SEV = {"error": 2, "drift": 1, "debt": 0, "dormant": 0, "info": -1}


def report(findings: list[dict], man: Manifest, repos: list[dict], crates: dict,
           pins_by_repo: dict) -> None:
    by_kind: dict[str, list[dict]] = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f)

    print("=" * 72)
    print("ESTATE AUDIT")
    print("=" * 72)
    statuses: dict[str, int] = {}
    areas: dict[str, int] = {}
    for e in man.repos.values():
        statuses[e["status"]] = statuses.get(e["status"], 0) + 1
        areas[e["area"]] = areas.get(e["area"], 0) + 1
    print(f"repos: {len(man.repos)}   crates published: {len(crates)}   "
          f"consumers audited: {len(pins_by_repo)}")
    print("  status: " + "  ".join(f"{k}={v}" for k, v in sorted(statuses.items())))
    print("  area:   " + "  ".join(f"{k}={v}" for k, v in sorted(areas.items())))

    n_pins = sum(len(p) for p in pins_by_repo.values())
    print(f"  exact pins: {n_pins} across {len(pins_by_repo)} consumer repo(s)")

    for kind in ("error", "drift", "debt", "dormant", "info"):
        items = by_kind.get(kind, [])
        print()
        print(f"--- {kind.upper()} ({len(items)}) " + "-" * (56 - len(kind)))
        if not items:
            print("  none")
            continue
        for f in sorted(items, key=lambda x: (SEV[x["kind"]] * -1, x["subject"])):
            print(f"  {f['subject']}: {f['message']}")
            # A pin held behind on purpose is not drift — it is a filed
            # ask, so it prints once, as the fix line.
            if f["fix"]:
                print(f"      -> {f['fix']}")
    print()


def sync(man: Manifest, repos: list[dict], crates: dict) -> int:
    """Refresh the auto-derived `_seen` fields in place."""
    gh = {r["name"]: r for r in repos}
    path = man.path
    text = path.read_text()
    changed = 0
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^  ([A-Za-z0-9._-]+):$", line)
        out.append(line)
        if m and m.group(1) in man.repos:
            name = m.group(1)
            meta = gh.get(name, {})
            seen = {}
            if meta:
                seen["last_push"] = (meta.get("pushedAt") or "")[:10]
                if meta.get("isFork"):
                    seen["fork"] = True
                if meta.get("isArchived"):
                    seen["archived"] = True
                if meta.get("visibility") == "PRIVATE":
                    seen["private"] = True
            for crate in man.repos[name].get("crates", []) or []:
                if crate in crates:
                    seen.setdefault("crate_versions", {})[crate] = crates[crate]["max_stable"]
            # find the block extent to drop stale _seen keys
            j = i + 1
            block = []
            while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                block.append(lines[j])
                j += 1
            kept = [b for b in block if not re.match(r"^    _seen", b)]
            if seen:
                indent = "    _seen:"
                kept.insert(0, indent)
                for k, v in seen.items():
                    if k == "crate_versions":
                        for c, cv in v.items():
                            kept.append(f"      {c}: {cv}")
                    elif v is True:
                        kept.append(f"      {k}: true")
                    else:
                        kept.append(f"      {k}: \"{v}\"")
            if kept != block:
                changed += 1
            out.extend(kept)
            out.extend(lines[j:j + 0])
            # skip the old block lines by tracking; handled below
    # The loop above needs index control; redo cleanly with an explicit rewrite.
    return sync_rewrite(path, man, gh, crates, changed)


def sync_rewrite(path: pathlib.Path, man: Manifest, gh: dict, crates: dict,
                 _unused: int) -> int:
    """Rewrite estate.yml with refreshed `_seen` blocks, preserving all other keys."""
    changed = 0
    new_lines: list[str] = []
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        m = re.match(r"^  ([A-Za-z0-9._-]+):$", line)
        if not m or m.group(1) not in man.repos:
            i += 1
            continue
        name = m.group(1)
        i += 1
        block: list[str] = []
        while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
            if not lines[i].strip() and not any(
                lines[k].startswith("    ") for k in range(i + 1, min(i + 4, len(lines)))
            ):
                break
            block.append(lines[i])
            i += 1
        body = [b for b in block if not re.match(r"^    _seen", b)]
        meta = gh.get(name, {})
        seen_lines: list[str] = []
        if meta:
            seen_lines.append("    _seen:")
            if meta.get("last_push") or meta.get("pushedAt"):
                seen_lines.append(f'      last_push: "{(meta.get("pushedAt") or "")[:10]}"')
            if meta.get("isFork"):
                seen_lines.append("      fork: true")
            if meta.get("isArchived"):
                seen_lines.append("      archived: true")
            if meta.get("visibility") == "PRIVATE":
                seen_lines.append("      private: true")
            versions = {
                c: crates[c]["max_stable"]
                for c in (man.repos[name].get("crates", []) or [])
                if c in crates
            }
            if versions:
                for c, v in versions.items():
                    seen_lines.append(f"      {c}: {v}")
        merged = body + seen_lines
        if merged != block:
            changed += 1
        new_lines.extend(merged)
    path.write_text("\n".join(new_lines) + "\n")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--sync", action="store_true", help="refresh _seen metadata")
    ap.add_argument("--offline", action="store_true", help="use the cached snapshot")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"no manifest at {MANIFEST}", file=sys.stderr)
        return 2

    try:
        man = Manifest(MANIFEST)
    except Exception as exc:  # noqa: BLE001
        print(f"manifest unreadable: {exc}", file=sys.stderr)
        return 2

    schema_problems = man.problems() + man.pin_problems()

    cache = load_cache()
    if args.offline:
        if not cache:
            print("no cache and --offline given; run without --offline first", file=sys.stderr)
            return 2
        repos, crates = cache["repos"], cache["crates"]
        pins_by_repo = cache["pins"]
    else:
        try:
            repos = fetch_repos()
            crates = fetch_crates()
            pins_by_repo = {c: fetch_consumer_pins(c) for c in CONSUMERS}
        except (urllib.error.URLError, subprocess.CalledProcessError, OSError) as exc:
            if cache:
                print(f"warn: network failed ({exc}); falling back to cache", file=sys.stderr)
                repos, crates = cache["repos"], cache["crates"]
                pins_by_repo = cache["pins"]
            else:
                print(f"network failed and no cache: {exc}", file=sys.stderr)
                return 2
        save_cache({"repos": repos, "crates": crates, "pins": pins_by_repo,
                    "fetched_at": dt.datetime.now(dt.UTC).isoformat()})

    if args.sync:
        n = sync_rewrite(MANIFEST, man, {r["name"]: r for r in repos}, crates)
        print(f"synced {n} repo block(s) in {MANIFEST.relative_to(ROOT)}")
        return 0

    findings = audit(man, repos, crates, pins_by_repo)
    for p in schema_problems:
        findings.insert(0, {"kind": "error", "subject": "estate.yml",
                            "message": p, "fix": "fix the schema"})

    if args.json:
        print(json.dumps({
            "repos": len(man.repos),
            "crates": len(crates),
            "pins": {k: len(v) for k, v in pins_by_repo.items()},
            "findings": findings,
        }, indent=1))
    else:
        report(findings, man, repos, crates, pins_by_repo)

    return 1 if any(f["kind"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())