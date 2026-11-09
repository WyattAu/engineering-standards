#!/usr/bin/env python3
"""check-commits: the COMMITS.md gate over a git revision range.

Checks CS-1..CS-7 mechanically and reports CS-8 (signature state):
  header grammar, closed type set, subject length and punctuation,
  blank line after the header, body width, breaking-change format,
  trailer position, and the signature status of every commit.

Usage:
    check-commits.py [--range A..B] [--require-signature] [--json]

`--range` defaults to `HEAD~1..HEAD`. Exit: 0 clean, 1 findings, 2 usage.
Stdlib only; git is the store (SC-9: runs locally, no secrets).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}
HEADER = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^()]+)\))?(?P<breaking>!)?: (?P<subject>.+)$"
)
TRAILER = re.compile(r"^[A-Z][A-Za-z-]*(?:-[A-Za-z]+)*: .+$")
SUBJECT_MAX = 50
BODY_MAX = 72
GOOD_SIGNATURES = {"G", "U"}


def git(args, cwd=None):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git failed: %s" % " ".join(args))
    return result.stdout


def commits(rev_range):
    out = git(["log", "--format=%H", rev_range])
    return [line.strip() for line in out.splitlines() if line.strip()]


def message(sha):
    return git(["show", "-s", "--format=%B", sha]).rstrip("\n")


def signature(sha):
    return git(["show", "-s", "--format=%G?", sha]).strip()


def audit_message(sha, text):
    findings = []

    def fail(code, detail):
        findings.append({"sha": sha[:7], "code": code, "message": detail})

    lines = text.split("\n")
    header = lines[0] if lines else ""
    match = HEADER.match(header)
    if not match:
        fail("header", "not `<type>(<scope>): <subject>`: %r" % header)
        return findings

    kind = match.group("type")
    subject = match.group("subject")
    if kind not in TYPES:
        fail("type", "unknown type %r (closed set, CS-2)" % kind)
    if len(subject) > SUBJECT_MAX:
        fail("subject-length", "subject is %d chars, limit %d" % (len(subject), SUBJECT_MAX))
    if subject.rstrip().endswith("."):
        fail("subject-period", "subject ends with a period")
    if len(lines) > 1 and lines[1].strip() != "":
        fail("blank-line", "second line must be blank when a body follows")

    body = lines[2:] if len(lines) > 2 else []
    burning = match.group("breaking") == "!"
    has_footer_breaking = False
    seen_trailer = False
    for index, line in enumerate(body):
        stripped = line.strip()
        if stripped.startswith("BREAKING CHANGE:"):
            has_footer_breaking = True
            continue
        if stripped.lower().startswith("breaking change"):
            fail("breaking-format", "use `BREAKING CHANGE: ` (uppercase) on line %d" % (index + 3))
            continue
        if len(line) > BODY_MAX and " " in stripped:
            fail("body-width", "body line %d is %d chars, limit %d" % (index + 3, len(line), BODY_MAX))
        if TRAILER.match(stripped) and not stripped.startswith(("*", "-")):
            seen_trailer = True
        elif seen_trailer and stripped and not TRAILER.match(stripped):
            fail("trailer-position", "prose after a trailer on line %d" % (index + 3))
    if match.group("breaking") and not has_footer_breaking:
        # Allowed by Conventional Commits: `!` alone is sufficient.
        pass
    return findings


def run(rev_range, require_signature):
    findings = []
    shas = commits(rev_range)
    signatures = {"good": 0, "unsigned": 0, "bad": 0}
    for sha in shas:
        findings.extend(audit_message(sha, message(sha)))
        state = signature(sha)
        if state in GOOD_SIGNATURES:
            signatures["good"] += 1
        elif state == "N":
            signatures["unsigned"] += 1
            if require_signature:
                findings.append({
                    "sha": sha[:7], "code": "signature", "message": "unsigned commit"
                })
        else:
            signatures["bad"] += 1
            findings.append({
                "sha": sha[:7],
                "code": "signature",
                "message": "signature state %r is not good (expired, revoked, or bad)" % state,
            })
    return shas, findings, signatures


def main(argv):
    args = list(argv[1:])
    rev_range = "HEAD~1..HEAD"
    as_json = "--json" in args
    require_signature = "--require-signature" in args
    if "--range" in args:
        index = args.index("--range")
        try:
            rev_range = args[index + 1]
        except IndexError:
            sys.stderr.write("check-commits: --range needs a value\n")
            return 2
    try:
        shas, findings, signatures = run(rev_range, require_signature)
    except RuntimeError as exc:
        sys.stderr.write("check-commits: %s\n" % exc)
        return 2

    if as_json:
        print(json.dumps(
            {"range": rev_range, "commits": len(shas), "signatures": signatures,
             "findings": findings},
            indent=2,
        ))
    else:
        for finding in findings:
            print("FAIL %s %s: %s" % (finding["sha"], finding["code"], finding["message"]))
        print(
            "check-commits: %d commit(s) in %s, %d finding(s); signatures: "
            "%d good, %d unsigned, %d bad"
            % (len(shas), rev_range, len(findings), signatures["good"],
               signatures["unsigned"], signatures["bad"])
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
