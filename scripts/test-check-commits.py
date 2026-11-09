#!/usr/bin/env python3
"""Self-test for check-commits.py: builds a throwaway repo with one commit per
rule violation, then asserts the gate names exactly that rule.

The gate is run as a subprocess against `--range <first>..HEAD` so the test
exercises the same entry point CI does.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "check-commits.py")

ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
}

# (name, message, expected finding code or None for a clean commit)
CASES = [
    ("clean", "feat(design): add the token gate", None),
    ("clean-body", "fix(cli): gate alerts behind full\n\nThe module is only reachable\nfrom the compare subcommand.", None),
    ("clean-breaking", "feat(api)!: drop the v1 endpoint\n\nBREAKING CHANGE: v1 is gone", None),
    ("bad-header", "update stuff", "header"),
    ("bad-type", "wip: rewrite everything", "type"),
    ("long-subject", "fix(core): " + "x" * 60, "subject-length"),
    ("period", "fix(core): remove the trailing period.", "subject-period"),
    ("no-blank", "fix(core): change behaviour\nBody starts immediately.", "blank-line"),
    ("lower-breaking", "feat(api): reshape\n\nbreaking change: the field moved", "breaking-format"),
    ("trailer-middle", "fix(core): tidy\n\nRefs: #1\n\nmore prose after the trailer", "trailer-position"),
]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **ENV}, check=False)


def main():
    failures = []
    with tempfile.TemporaryDirectory() as repo:
        run(["git", "init", "-q", "-b", "main"], repo)
        run(["git", "config", "user.name", "Test"], repo)
        run(["git", "config", "user.email", "test@example.invalid"], repo)
        run(["git", "commit", "-q", "--allow-empty", "-m", "chore: seed"], repo)
        base = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
        for name, message, expected in CASES:
            result = run(["git", "commit", "-q", "--allow-empty", "-m", message], repo)
            if result.returncode != 0:
                failures.append("%s: could not create commit: %s" % (name, result.stderr))
                continue
            sha = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
            check = run([sys.executable, GATE, "--range", "%s~1..%s" % (sha, sha), "--json"], repo)
            import json as _json
            try:
                payload = _json.loads(check.stdout)
            except ValueError:
                failures.append("%s: gate produced no JSON: %s %s" % (name, check.stdout, check.stderr))
                continue
            codes = {finding["code"] for finding in payload["findings"]}
            if expected is None:
                if codes:
                    failures.append("%s: expected clean, got %s" % (name, sorted(codes)))
            elif expected not in codes:
                failures.append("%s: expected %s, got %s" % (name, expected, sorted(codes)))
            # The seed commit carries its own subject; the range is one commit
            # so the count is the check that the range is honoured.
            if payload["commits"] != 1:
                failures.append("%s: range returned %d commits" % (name, payload["commits"]))
    if failures:
        print("test-check-commits: FAIL (%d)" % len(failures))
        for failure in failures:
            print("  " + failure)
        return 1
    print("test-check-commits: PASS (%d fixtures)" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
