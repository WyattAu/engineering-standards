#!/usr/bin/env python3
"""check-adoption: validate candidates.yml against ADOPTION.md.

Rules enforced (AD-1..AD-9):
  decision vocabulary, licence verification and allowlist, copyleft
  handling, layer presence for adopt, rationale length, source/measured
  presence, review_by window, unique names, url/name agreement.

Usage: check-adoption.py [candidates.yml] [--json]
Exit: 0 clean, 1 findings, 2 usage or parse error.
"""

from __future__ import annotations

import datetime
import json
import sys

import yaml

DECISIONS = {"adopt", "fork", "rebuild", "follow", "hold", "reject"}
PERMISSIVE = {
    "Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC",
    "MPL-2.0", "Zlib", "Unlicense", "CC0-1.0",
}
COPYLEFT = {"AGPL-3.0", "GPL-2.0", "GPL-3.0", "SSPL-1.0", "BUSL-1.1", "EUPL-1.2"}
NEEDS_LICENCE = {"adopt", "fork", "rebuild"}
MAX_REVIEW_DAYS = 180
MIN_RATIONALE = 40


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def audit(document):
    findings = []

    def fail(subject, code, detail):
        findings.append({"subject": subject, "code": code, "message": detail})

    measured = parse_date(document.get("measured"))
    if measured is None:
        fail("registry", "measured", "top-level `measured` must be an ISO date")
        measured = datetime.date.today()
        findings.append({"subject": "registry", "code": "date-assumed",
                         "message": "dates compared against today instead"})

    candidates = document.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        fail("registry", "empty", "`candidates` must be a non-empty list")
        return findings

    seen = set()
    for index, entry in enumerate(candidates, 1):
        name = entry.get("name") or "candidate-%d" % index
        if name in seen:
            fail(name, "duplicate", "name appears twice")
        seen.add(name)

        url = entry.get("url") or ""
        if not url.startswith("https://github.com/"):
            fail(name, "url", "url must be an https://github.com/ link")
        elif url.rstrip("/").split("github.com/")[-1].lower() != name.lower():
            fail(name, "url-name", "url %r does not match name %r" % (url, name))

        decision = entry.get("decision")
        if decision not in DECISIONS:
            fail(name, "decision", "decision %r not in %s" % (decision, sorted(DECISIONS)))
            continue

        licence = entry.get("license")
        verified = entry.get("license_verified")
        if not isinstance(verified, bool):
            fail(name, "license-flag", "`license_verified` must be true or false")

        if decision in NEEDS_LICENCE or decision in {"hold", "follow"}:
            pass
        if decision in NEEDS_LICENCE:
            if not verified:
                fail(name, "license-unverified",
                     "%s requires license_verified: true" % decision)
            if licence not in PERMISSIVE:
                fail(name, "license",
                     "%s requires an allowlisted licence, got %r" % (decision, licence))

        if licence in COPYLEFT and decision in {"adopt", "fork", "rebuild"}:
            fail(name, "copyleft",
                 "%s is copyleft; only follow or reject (AD-3)" % licence)

        rationale = entry.get("rationale") or ""
        if len(rationale.strip()) < MIN_RATIONALE:
            fail(name, "rationale",
                 "rationale needs at least %d characters" % MIN_RATIONALE)

        if not entry.get("source"):
            fail(name, "source", "every candidate needs a source URL")
        if decision == "hold" and not entry.get("open_question"):
            fail(name, "hold-question", "a hold must name the open question")

        if decision == "adopt" and entry.get("layer") not in {"L0", "L1", "L2", "L3"}:
            fail(name, "layer", "adopt must name its layer (L0..L3, AD-6)")

        review = parse_date(entry.get("review_by"))
        if review is None:
            fail(name, "review-by", "review_by must be an ISO date (AD-9)")
        else:
            if review < measured:
                fail(name, "review-by", "review_by %s is before measured %s" % (review, measured))
            if (review - measured).days > MAX_REVIEW_DAYS:
                fail(name, "review-by",
                     "review_by is %d days out, limit %d" % ((review - measured).days, MAX_REVIEW_DAYS))
    return findings


def summarise(document):
    counts = {key: 0 for key in sorted(DECISIONS)}
    licences = {}
    for entry in document.get("candidates") or []:
        counts[entry.get("decision", "hold")] = counts.get(entry.get("decision", "hold"), 0) + 1
        key = entry.get("license") or "unverified"
        licences[key] = licences.get(key, 0) + 1
    return counts, licences


def main(argv):
    args = [arg for arg in argv[1:] if not arg.startswith("--")]
    as_json = "--json" in argv[1:]
    path = args[0] if args else "candidates.yml"
    try:
        with open(path, encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        sys.stderr.write("check-adoption: cannot read %s: %s\n" % (path, exc))
        return 2
    if not isinstance(document, dict):
        sys.stderr.write("check-adoption: %s is not a mapping\n" % path)
        return 2

    findings = audit(document)
    counts, licences = summarise(document)
    if as_json:
        print(json.dumps({"findings": findings, "decisions": counts,
                          "licences": licences}, indent=2))
    else:
        for finding in findings:
            print("FAIL %s %s: %s" % (finding["subject"], finding["code"],
                                      finding["message"]))
        print("check-adoption: %d candidate(s), %d finding(s)"
              % (len(document.get("candidates") or []), len(findings)))
        print("  decisions: " + ", ".join("%s=%d" % (k, v) for k, v in counts.items() if v))
        print("  licences:  " + ", ".join("%s=%d" % (k, v) for k, v in sorted(licences.items())))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
