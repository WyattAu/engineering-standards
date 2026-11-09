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


def case(name, expect_codes, expect_status, args=()):
    def register(func):
        CASES[name] = (func, tuple(expect_codes), expect_status, tuple(args))
        return func

    return register


def px(value):
    return {"value": value, "unit": "px"}


def ms(value):
    return {"value": value, "unit": "ms"}


def appearing(value):
    return {"$extensions": {"estate": {"lineHeight": value}}}


def scale_document(size=None, space=None, duration=None, easing=None):
    """A colour pair plus the three scale groups, each overridable."""
    sizes = size if size is not None else {
        "caption": {"$value": px(13), **appearing(1.55)},
        "body": {"$value": px(16), **appearing(1.5)},
        "title": {"$value": px(20), **appearing(1.4)},
        "heading": {"$value": px(25), **appearing(1.25)},
    }
    spacings = space if space is not None else {
        "xs": {"$value": px(4)},
        "sm": {"$value": px(8)},
        "md": {"$value": px(12)},
        "lg": {"$value": px(16)},
        "xl": {"$value": px(24)},
    }
    durations = duration if duration is not None else {
        "instant": {"$value": ms(100)},
        "fast": {"$value": ms(150)},
        "base": {"$value": ms(240)},
        "reduced": {"$value": ms(0)},
    }
    easings = easing if easing is not None else {
        "standard": {"$value": [0.2, 0.0, 0.0, 1.0]},
        "enter": {"$value": [0.0, 0.0, 0.0, 1.0]},
    }
    payload = document(
        {"surface": {"$value": SURFACE}, "on-surface": {"$value": ON_SURFACE}},
        [{"name": "body", "fg": "{color.on-surface}", "bg": "{color.surface}"}],
    )
    payload["type"] = {
        "$type": "dimension",
        "$extensions": {"estate": {"base": 16, "ratio": 1.25, "ratioTolerance": 0.05}},
        "size": sizes,
    }
    payload["space"] = {
        "$type": "dimension",
        "$extensions": {"estate": {"base": 4, "rhythm": 8}},
        **spacings,
    }
    payload["motion"] = {
        "duration": {"$type": "duration", **durations},
        "easing": {"$type": "cubicBezier", **easings},
    }
    return payload


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


@case("scales-clean", [], 0, args=("--require-scales",))
def _scales_clean(directory):
    return write(directory, "scales.json", scale_document())


@case("scales-missing", ["missing-scale"], 1, args=("--require-scales",))
def _scales_missing(directory):
    return write(
        directory,
        "scales-missing.json",
        document(
            {"surface": {"$value": SURFACE}, "on-surface": {"$value": ON_SURFACE}},
            [{"name": "body", "fg": "{color.on-surface}", "bg": "{color.surface}"}],
        ),
    )


@case("type-ratio", ["type-ratio"], 1)
def _type_ratio(directory):
    # 29 px after 20 px is a 1.45 step: a second, undeclared scale.
    size = {
        "caption": {"$value": px(13), **appearing(1.55)},
        "body": {"$value": px(16), **appearing(1.5)},
        "title": {"$value": px(20), **appearing(1.4)},
        "heading": {"$value": px(29), **appearing(1.2)},
    }
    return write(directory, "type-ratio.json", scale_document(size=size))


@case("type-range", ["type-range"], 1)
def _type_range(directory):
    size = {
        "caption": {"$value": px(10), **appearing(1.6)},
        "body": {"$value": px(16), **appearing(1.5)},
        "title": {"$value": px(20), **appearing(1.4)},
        "heading": {"$value": px(25), **appearing(1.25)},
    }
    return write(directory, "type-range.json", scale_document(size=size))


@case("type-leading", ["type-leading"], 1)
def _type_leading(directory):
    # 1.3 leading at body size is below the 1.5 floor in DS-10.
    size = {
        "caption": {"$value": px(13), **appearing(1.55)},
        "body": {"$value": px(16), **appearing(1.3)},
        "title": {"$value": px(20), **appearing(1.4)},
        "heading": {"$value": px(25), **appearing(1.25)},
    }
    return write(directory, "type-leading.json", scale_document(size=size))


@case("type-unit", ["type-unit"], 1)
def _type_unit(directory):
    size = {
        "caption": {"$value": {"value": 0.81, "unit": "rem"}, **appearing(1.55)},
        "body": {"$value": px(16), **appearing(1.5)},
        "title": {"$value": px(20), **appearing(1.4)},
        "heading": {"$value": px(25), **appearing(1.25)},
    }
    return write(directory, "type-unit.json", scale_document(size=size))


@case("space-multiple", ["space-multiple"], 1)
def _space_multiple(directory):
    space = {
        "xs": {"$value": px(4)},
        "sm": {"$value": px(8)},
        "md": {"$value": px(13)},
        "lg": {"$value": px(16)},
        "xl": {"$value": px(24)},
    }
    return write(directory, "space-multiple.json", scale_document(space=space))


@case("space-base", ["space-base"], 1)
def _space_base(directory):
    space = {
        "xs": {"$value": px(8)},
        "sm": {"$value": px(12)},
        "md": {"$value": px(16)},
        "lg": {"$value": px(24)},
        "xl": {"$value": px(32)},
    }
    return write(directory, "space-base.json", scale_document(space=space))


@case("motion-band", ["motion-band"], 1)
def _motion_band(directory):
    duration = {
        "instant": {"$value": ms(100)},
        "fast": {"$value": ms(260)},
        "base": {"$value": ms(240)},
        "reduced": {"$value": ms(0)},
    }
    return write(directory, "motion-band.json", scale_document(duration=duration))


@case("motion-reduced", ["motion-reduced"], 1)
def _motion_reduced(directory):
    duration = {
        "fast": {"$value": ms(150)},
        "base": {"$value": ms(240)},
        "reduced": {"$value": ms(120)},
    }
    return write(directory, "motion-reduced.json", scale_document(duration=duration))


@case("motion-easing", ["motion-easing"], 1)
def _motion_easing(directory):
    easing = {
        "standard": {"$value": [0.2, 0.0, 0.0, 1.0]},
        "overshoot": {"$value": [0.2, 1.6, 0.0, 1.0]},
    }
    return write(directory, "motion-easing.json", scale_document(easing=easing))


def main():
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        for name, (builder, codes, status, args) in sorted(CASES.items()):
            path = builder(directory)
            actual_status, output = run(path, *args)
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
