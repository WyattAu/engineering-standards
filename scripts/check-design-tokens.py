#!/usr/bin/env python3
"""check-design-tokens: the DTCG token gate for DESIGN.md.

Checks the machine-checkable subset of DESIGN.md:

  DS-1  every colour token is reachable from a declared contrast pair, or
        carries an explicit, non-empty `$extensions.estate.ungated` reason
  DS-3  text pairs meet the declared ratio (AA 4.5, AAA 7.0, large 3.0)
  DS-4  ui/large pairs meet 3:1
  DS-9  every alias resolves (no dangling `{token}` references, no cycles)
  DS-19 declared exceptions are non-empty and expired ones fail

Usage:
    check-design-tokens.py <tokens.json> [--json]

Exit codes: 0 clean, 1 findings, 2 usage or parse error.
No third-party dependencies: stdlib only (AGENTS.md rule 5).
"""

from __future__ import annotations

import datetime
import json
import sys

DEFAULT_MIN = {"text": 4.5, "large": 3.0, "ui": 3.0}
# The floor a pair may not undercut by declaring a smaller `min`. Lowering
# these requires an ADR (SM-5, SM-6), not a quieter number in the document.
FLOOR = {"text": 4.5, "large": 3.0, "ui": 3.0}
AAA_MIN = {"text": 7.0, "large": 4.5, "ui": 4.5}


class ColourError(Exception):
    pass


def walk(node, path=(), inherited_type=None):
    """Yield (path tuple, token node, declared type) for every DTCG token."""
    out = []
    if not isinstance(node, dict):
        return out
    token_type = node.get("$type", inherited_type)
    if "$value" in node:
        out.append((path, node, token_type))
        return out
    for key in sorted(node):
        if key.startswith("$"):
            continue
        out.extend(walk(node[key], path + (key,), token_type))
    return out


def _decode_hex(text):
    raw = text.strip()
    if not raw.startswith("#"):
        raise ColourError("colour string must start with '#'")
    digits = raw[1:]
    if len(digits) in (3, 4):
        digits = "".join(ch * 2 for ch in digits)
    if len(digits) not in (6, 8):
        raise ColourError("hex colour must have 3, 4, 6, or 8 digits")
    try:
        red, green, blue = (int(digits[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        alpha = int(digits[6:8], 16) / 255.0 if len(digits) == 8 else 1.0
    except ValueError as exc:
        raise ColourError("hex colour has non-hex digits") from exc
    return (red, green, blue, alpha)


def parse_colour(value):
    """Return (r, g, b, a) with components in the sRGB encoding, 0..1."""
    if isinstance(value, str):
        return _decode_hex(value)
    if isinstance(value, dict):
        space = value.get("colorSpace", "srgb")
        if space != "srgb":
            raise ColourError("only colorSpace 'srgb' is supported (DS-2)")
        components = value.get("components") or []
        if len(components) != 3:
            raise ColourError("colour needs exactly 3 components")
        try:
            red, green, blue = (float(c) for c in components)
        except (TypeError, ValueError) as exc:
            raise ColourError("components must be numbers (not 'none')") from exc
        alpha = value.get("alpha", 1.0)
        alpha = 1.0 if alpha is None else float(alpha)
        return (red, green, blue, alpha)
    raise ColourError("unrecognised colour value")


def _to_linear(channel):
    channel = min(1.0, max(0.0, channel))
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _to_encoded(channel):
    channel = min(1.0, max(0.0, channel))
    if channel <= 0.0031308:
        return 12.92 * channel
    return 1.055 * (channel ** (1 / 2.4)) - 0.055


def luminance(colour):
    red, green, blue = (_to_linear(c) for c in colour[:3])
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(one, other):
    a, b = luminance(one), luminance(other)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def composite_over(fg, bg):
    """Linear-light alpha composite (DS-2), returned in sRGB encoding."""
    alpha = fg[3]
    if alpha >= 1.0:
        return fg[:3] + (1.0,)
    out = tuple(
        _to_encoded(_to_linear(fg[i]) * alpha + _to_linear(bg[i]) * (1.0 - alpha))
        for i in range(3)
    )
    return out + (1.0,)


def ungated_reason(node):
    extensions = node.get("$extensions") or {}
    estate = extensions.get("estate") or {}
    if "ungated" not in estate:
        return None
    reason = estate.get("ungated")
    return reason if isinstance(reason, str) else ""


def ungated_expiry(node):
    extensions = node.get("$extensions") or {}
    estate = extensions.get("estate") or {}
    raw = estate.get("expires")
    return raw if isinstance(raw, str) else None


class Auditor:
    def __init__(self, document):
        self.document = document
        self.findings = []
        self.tokens = {
            ".".join(path): (node, token_type)
            for path, node, token_type in walk(document)
        }
        extensions = document.get("$extensions") or {}
        self.estate = extensions.get("estate") or {}
        self.pairs = self.estate.get("contrast") or []
        self.used = set()

    def fail(self, code, message):
        self.findings.append({"code": code, "message": message})

    def resolve(self, key, seen=()):
        if key in seen:
            raise KeyError("alias cycle: " + " -> ".join(seen + (key,)))
        if key not in self.tokens:
            raise KeyError("unknown token")
        node, token_type = self.tokens[key]
        value = node["$value"]
        if isinstance(value, str) and value.strip().startswith("{"):
            target = value.strip()[1:-1].strip()
            return self.resolve(target, seen + (key,))
        return node, token_type

    def run(self):
        if not self.pairs:
            self.fail("no-pairs", "document declares no $extensions.estate.contrast")
        for index, pair in enumerate(self.pairs, 1):
            self.check_pair(index, pair)
        self.check_coverage()
        return self.findings

    def check_pair(self, index, pair):
        label = pair.get("name") or "pair %d" % index
        kind = pair.get("kind", "text")
        if kind not in DEFAULT_MIN:
            self.fail("bad-kind", "%s: unknown kind %r (text|large|ui)" % (label, kind))
            return
        level = pair.get("level", "AA")
        floor = FLOOR[kind]
        minimum = pair.get("min")
        if minimum is None:
            minimum = AAA_MIN[kind] if level == "AAA" else DEFAULT_MIN[kind]
        try:
            minimum = float(minimum)
        except (TypeError, ValueError):
            self.fail("bad-min", "%s: min is not a number" % label)
            return
        if minimum < floor:
            self.fail(
                "below-floor",
                "%s: declared min %.2f undercuts the DS-%s floor %.2f"
                % (label, minimum, "3" if kind == "text" else "4", floor),
            )
            minimum = floor

        colours = {}
        for side in ("fg", "bg"):
            raw = pair.get(side)
            if not isinstance(raw, str):
                self.fail("bad-pair", "%s: missing %s" % (label, side))
                return
            key = raw.strip()
            if key.startswith("{") and key.endswith("}"):
                key = key[1:-1].strip()
            try:
                node, token_type = self.resolve(key)
            except KeyError as exc:
                self.fail(
                    "unresolved-alias",
                    "%s: %s %r does not resolve (%s)" % (label, side, raw, exc.args[0]),
                )
                return
            if token_type is not None and token_type != "color":
                self.fail("non-colour", "%s: %s is type %r, not colour" % (label, side, token_type))
                return
            try:
                colours[side] = parse_colour(node["$value"])
            except ColourError as exc:
                self.fail("bad-colour", "%s: %s %r: %s" % (label, side, key, exc))
                return
            self.used.add(key)

        fg = composite_over(colours["fg"], colours["bg"])
        ratio = contrast_ratio(fg, colours["bg"])
        if ratio < minimum:
            self.fail(
                "contrast",
                "%s: %.2f:1 below %.2f:1 (%s, %s)"
                % (label, ratio, minimum, kind, level),
            )

    def check_coverage(self):
        today = datetime.date.today()
        for key in sorted(self.tokens):
            node, token_type = self.tokens[key]
            if key in self.used:
                continue
            try:
                parse_colour(node["$value"])
            except ColourError as exc:
                if token_type == "color":
                    self.fail("bad-colour", "%s: %s" % (key, exc))
                continue
            reason = ungated_reason(node)
            if reason is None:
                self.fail(
                    "undeclared-exception",
                    "%s: no contrast pair and no $extensions.estate.ungated reason"
                    % key,
                )
                continue
            if not reason.strip():
                self.fail("empty-exception", "%s: ungated reason is empty" % key)
                continue
            expiry = ungated_expiry(node)
            if expiry:
                try:
                    parsed = datetime.date.fromisoformat(expiry)
                except ValueError:
                    self.fail("bad-expiry", "%s: expires %r is not ISO 8601" % (key, expiry))
                    continue
                if parsed < today:
                    self.fail(
                        "expired-exception",
                        "%s: exception expired %s (renew with an ADR or fix the pair)"
                        % (key, expiry),
                    )


def main(argv):
    paths = [arg for arg in argv[1:] if not arg.startswith("--")]
    as_json = "--json" in argv[1:]
    if len(paths) != 1:
        sys.stderr.write("usage: check-design-tokens.py <tokens.json> [--json]\n")
        return 2
    try:
        with open(paths[0], encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write("check-design-tokens: cannot read %s: %s\n" % (paths[0], exc))
        return 2

    auditor = Auditor(document)
    findings = auditor.run()
    if as_json:
        print(json.dumps({"findings": findings, "tokens": len(auditor.tokens)}, indent=2))
    else:
        for finding in findings:
            print("FAIL %s: %s" % (finding["code"], finding["message"]))
        print(
            "check-design-tokens: %d finding(s) across %d tokens"
            % (len(findings), len(auditor.tokens))
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
