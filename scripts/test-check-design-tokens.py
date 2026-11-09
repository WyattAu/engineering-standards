#!/usr/bin/env python3
"""Self-test for check-design-tokens.py (fixtures built in a temp dir).

Runs the gate as a subprocess so the test exercises the same entry point CI
does. Every fixture states the finding the gate must produce; a fixture that
stops failing means the gate lost a rule.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "check-design-tokens.py")

SURFACE = {"colorSpace": "srgb", "components": [0.05, 0.07, 0.09], "alpha": 1}
ON_SURFACE = {"colorSpace": "srgb", "components": [0.92, 0.94, 0.96], "alpha": 1}


def document(tokens, pairs):
    return {
        "$type": "color",
        "color": tokens,
        "$extensions": {"estate": {"contrast": pairs}},
    }


def write(directory, name, payload):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def run(path, *extra):
    result = subprocess.run(
        [sys.executable, GATE, path, *extra],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


CASES = {}


def case(name, expect_codes, expect_status):
    def register(func):
        CASES[name] = (func, expect_codes, expect_status)
        return func

    return register


@case("clean", [], 0)
def _clean(directory):
    return write(
        directory,
        "clean.json",
        document(
            {
                "surface": {"$value": SURFACE},
                "on-surface": {"$value": ON_SURFACE},
                "border": {"$value": "#8b949e"},
                "seed-accent": {
                    "$value": "#1f6feb",
                    "$extensions": {
                        "estate": {"ungated": "seed palette hue anchor; paired at component layer"}
                    },
                },
            },
            [
                {"name": "body", "fg": "{color.on-surface}", "bg": "{color.surface}"},
                {"name": "edge", "fg": "{color.border}", "bg": "{color.surface}", "kind": "ui"},
            ],
        ),
    )


@case("low-contrast", ["contrast"], 1)
def _low_contrast(directory):
    return write(
        directory,
        "low.json",
        document(
            {
                "surface": {"$value": SURFACE},
                "border": {"$value": "#3d4450"},
            },
            [{"name": "edge", "fg": "{color.border}", "bg": "{color.surface}", "kind": "ui"}],
        ),
    )


@case("undeclared", ["undeclared-exception"], 1)
def _undeclared(directory):
    return write(
        directory,
        "undeclared.json",
        document(
            {
                "surface": {"$value": SURFACE},
                "on-surface": {"$value": ON_SURFACE},
                "hover": {"$value": "#30363d"},
            },
            [{"name": "body", "fg": "{color.on-surface}", "bg": "{color.surface}"}],
        ),
    )


@case("alias", ["unresolved-alias"], 1)
def _alias(directory):
    return write(
        directory,
        "alias.json",
        document(
            {"surface": {"$value": SURFACE}},
            [{"name": "body", "fg": "{color.missing}", "bg": "{color.surface}"}],
        ),
    )


@case("below-floor", ["below-floor"], 1)
def _below_floor(directory):
    return write(
        directory,
        "floor.json",
        document(
            {"surface": {"$value": SURFACE}, "on-surface": {"$value": ON_SURFACE}},
            [
                {
                    "name": "body",
                    "fg": "{color.on-surface}",
                    "bg": "{color.surface}",
                    "min": 3.0,
                }
            ],
        ),
    )


@case("expired", ["expired-exception"], 1)
def _expired(directory):
    return write(
        directory,
        "expired.json",
        document(
            {
                "surface": {"$value": SURFACE},
                "on-surface": {"$value": ON_SURFACE},
                "legacy": {
                    "$value": "#444444",
                    "$extensions": {
                        "estate": {"ungated": "legacy divider", "expires": "2020-01-01"}
                    },
                },
            },
            [{"name": "body", "fg": "{color.on-surface}", "bg": "{color.surface}"}],
        ),
    )


@case("alpha-composite", ["contrast"], 1)
def _alpha(directory):
    # 12% white over the dark surface is a plausible hover layer and must be
    # measured composited, not as opaque white (DS-2 + DS-13).
    return write(
        directory,
        "alpha.json",
        document(
            {
                "surface": {"$value": SURFACE},
                "hover-text": {
                    "$value": {"colorSpace": "srgb", "components": [1, 1, 1], "alpha": 0.12}
                },
            },
            [{"name": "hover", "fg": "{color.hover-text}", "bg": "{color.surface}"}],
        ),
    )


def main():
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        for name, (builder, codes, status) in sorted(CASES.items()):
            path = builder(directory)
            actual_status, output = run(path)
            if actual_status != status:
                failures.append(
                    "%s: exit %d, expected %d\n%s" % (name, actual_status, status, output)
                )
                continue
            for code in codes:
                if "FAIL %s:" % code not in output:
                    failures.append("%s: missing finding %s\n%s" % (name, code, output))
    if failures:
        print("test-check-design-tokens: FAIL (%d)" % len(failures))
        for failure in failures:
            print(failure)
        return 1
    print("test-check-design-tokens: PASS (%d fixtures)" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
