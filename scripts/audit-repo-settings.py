#!/usr/bin/env python3
"""audit-repo-settings: declared repository settings vs what GitHub reports.

OMNI-CORE 10 (security defaults) and 11g (trunk discipline) name settings
that no other gate could see, because `estate.yml` records intent, not state.
This audit closes that blind spot for the settings REST exposes:

  branch protection on the default branch
  secret scanning
  secret scanning push protection
  Dependabot security updates

`merge_queue` has no REST endpoint. It is reported as `unknown`, never as a
pass (AGENTS.md rule 7). Requirements and waivers live in
`settings-policy.yml`; the repo list and statuses come from `estate.yml`.

Usage:
  audit-repo-settings.py [--limit N] [--repo NAME] [--strict] [--json]
Exit: 0 clean or advisory drift, 1 drift with --strict, 2 usage error.

Advisory by default because the first run necessarily reports the estate as
it is (branch protection is off almost everywhere), and a gate that red-lights
every unrelated PR teaches people to ignore it. LOOP.md graduation applies.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys

import yaml

HERE = __import__("pathlib").Path(__file__).resolve().parent
ROOT = HERE.parent
SETTINGS = {"branch_protection", "secret_scanning", "push_protection",
            "dependabot_security_updates"}


def gh(path):
    """Return (ok, payload). 404 is a legitimate answer: the setting is off."""
    result = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    try:
        return True, json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "non-JSON response"


def load_yaml(name):
    with open(ROOT / name, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def observe(owner, repo):
    """Observed state, with None meaning 'the API cannot tell us'."""
    ok, payload = gh("repos/%s/%s" % (owner, repo))
    if not ok:
        raise RuntimeError("cannot read %s/%s: %s" % (owner, repo, payload))
    branch = payload.get("default_branch") or "main"
    analysis = (payload.get("security_and_analysis") or {})
    observed = {
        "default_branch": branch,
        "secret_scanning": (analysis.get("secret_scanning") or {}).get("status") == "enabled",
        "push_protection": (analysis.get("secret_scanning_push_protection") or {}).get("status") == "enabled",
    }
    protected, detail = gh("repos/%s/%s/branches/%s/protection" % (owner, repo, branch))
    observed["branch_protection"] = bool(protected)
    observed["required_status_checks"] = None
    if protected and isinstance(detail, dict):
        checks = detail.get("required_status_checks") or {}
        observed["required_status_checks"] = len(checks.get("contexts") or [])
    fixes, fixes_detail = gh("repos/%s/%s/automated-security-fixes" % (owner, repo))
    observed["dependabot_security_updates"] = bool(
        fixes and isinstance(fixes_detail, dict) and fixes_detail.get("enabled")
    )
    return observed


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=25,
                        help="repos to check (default 25; 3 API calls each)")
    parser.add_argument("--repo", help="check one repo")
    parser.add_argument("--strict", action="store_true", help="exit 1 on drift")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    estate = load_yaml("estate.yml")
    policy = load_yaml("settings-policy.yml")
    repos = estate["repos"]
    require = {k for k, v in (policy.get("require") or {}).items() if v}
    skip = set(policy.get("skip_status") or [])
    exemptions = policy.get("exemptions") or {}

    unknown = require - SETTINGS
    if unknown:
        sys.stderr.write("audit-repo-settings: policy requires unobservable %s\n"
                         % sorted(unknown))
        return 2

    owner = estate.get("owner") or "WyattAu"
    names = [args.repo] if args.repo else [
        name for name, entry in sorted(repos.items())
        if (entry or {}).get("status") not in skip
    ][: args.limit]

    today = datetime.date.today()
    findings = []
    rows = []
    for name in names:
        entry = repos.get(name) or {}
        if not isinstance(entry, dict):
            findings.append("%s: registry entry is not a mapping" % name)
            continue
        status = entry.get("status")
        if status in skip and not args.repo:
            continue
        waiver = exemptions.get(name) or {}
        if waiver:
            expires = waiver.get("expires")
            reason = (waiver.get("reason") or "").strip()
            owner_name = (waiver.get("owner") or "").strip()
            if not reason or not owner_name or not expires:
                findings.append("%s: waiver needs owner, reason, and expires" % name)
                continue
            try:
                expired = datetime.date.fromisoformat(str(expires)) < today
            except ValueError:
                findings.append("%s: waiver expiry %r is not ISO 8601" % (name, expires))
                continue
            if expired:
                findings.append("%s: waiver expired %s" % (name, expires))
                continue
            rows.append({"repo": name, "status": status, "waived": str(expires)})
            continue
        try:
            observed = observe(owner, name)
        except RuntimeError as exc:
            findings.append(str(exc))
            continue
        off = sorted(key for key in require if observed.get(key) is False)
        rows.append({
            "repo": name,
            "status": status,
            "branch": observed.get("default_branch"),
            "branch_protection": observed.get("branch_protection"),
            "required_status_checks": observed.get("required_status_checks"),
            "secret_scanning": observed.get("secret_scanning"),
            "push_protection": observed.get("push_protection"),
            "dependabot_security_updates": observed.get("dependabot_security_updates"),
            "merge_queue": "unknown",
            "off": off,
        })
        for key in off:
            findings.append("%s: %s is off" % (name, key))

    counts = {key: sum(1 for row in rows if row.get("waived") is None and row.get(key))
              for key in sorted(require)}
    checked = sum(1 for row in rows if row.get("waived") is None)

    if args.json:
        print(json.dumps({"checked": checked, "counts": counts,
                          "rows": rows, "findings": findings}, indent=2))
    else:
        for finding in findings:
            print("FAIL %s" % finding)
        print("audit-repo-settings: %d repo(s) checked%s"
              % (checked, " (advisory; --strict to block)" if not args.strict else ""))
        for key in sorted(require):
            print("  %-28s %d/%d" % (key, counts.get(key, 0), checked))
        print("  %-28s unknown (no REST endpoint; see 11g)" % "merge_queue")
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
