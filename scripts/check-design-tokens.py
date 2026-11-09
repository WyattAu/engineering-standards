#!/usr/bin/env python3
"""check-design-tokens: the DTCG token gate for DESIGN.md.

Checks the machine-checkable subset of DESIGN.md:

  DS-1  every colour token is reachable from a declared contrast pair, or
        carries an explicit, non-empty `$extensions.estate.ungated` reason
  DS-3  text pairs meet the declared ratio (AA 4.5, AAA 7.0, large 3.0)
  DS-4  ui/large pairs meet 3:1
  DS-9  every alias resolves (no dangling `{token}` references, no cycles)
  DS-10 the type scale is integer px, monotonic, on one ratio, with leading
  DS-11 spacing is a 4 px scale, monotonic and bounded
  DS-12 motion durations sit in their named bands and reduced motion is 0
  DS-19 declared exceptions are non-empty and expired ones fail

Usage:
    check-design-tokens.py <tokens.json> [--json] [--require-scales]

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


# Scale rules (DS-10..DS-12). The numbers are the canon, not the document:
# a token file may not widen them any more than a contrast pair may undercut
# its floor. Changing one is an ADR (SM-5, SM-6).
TYPE_MIN_STEPS, TYPE_MAX_STEPS = 4, 8
TYPE_MIN_PX, TYPE_MAX_PX = 12.0, 72.0
LEADING_MIN, LEADING_BODY = 1.2, 1.5
SPACE_MIN_PX, SPACE_MAX_PX = 4.0, 96.0
SPACE_MIN_STEPS, SPACE_MAX_STEPS = 5, 10
SPACE_BASE = 4.0
MOTION_BANDS = {
    "instant": (0.0, 100.0),
    "fast": (100.0, 200.0),
    "base": (200.0, 300.0),
    "slow": (300.0, 400.0),
}
MOTION_CEILING = 400.0


class ScaleError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def dimension_px(value, unit_code="type-unit"):
    """Return a DTCG dimension in px, or raise the finding it deserves."""
    if isinstance(value, dict):
        unit = value.get("unit", "px")
        if unit != "px":
            raise ScaleError(
                unit_code,
                "unit %r is not px: a rem scale drifts with the reader's font size"
                % (unit,),
            )
        value = value.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScaleError(unit_code, "value %r is not a number" % (value,))
    return float(value)


def extension(node, key, default=None):
    estate = ((node.get("$extensions") or {}).get("estate") or {})
    return estate.get(key, default)


def check_type(document, fail):
    group = document.get("type") or {}
    sizes = group.get("size")
    if not isinstance(sizes, dict) or not sizes:
        return False
    settings = (group.get("$extensions") or {}).get("estate") or {}
    base = float(settings.get("base", 16))
    ratio = float(settings.get("ratio", 1.25))
    tolerance = float(settings.get("ratioTolerance", 0.05))

    steps = []
    for role in sorted(sizes):
        node = sizes[role]
        if not isinstance(node, dict) or "$value" not in node:
            fail("type-shape", "type.size.%s: not a token" % role)
            continue
        try:
            px = dimension_px(node["$value"])
        except ScaleError as exc:
            fail(exc.code, "type.size.%s: %s" % (role, exc.message))
            continue
        steps.append((role, px, node))

    if not TYPE_MIN_STEPS <= len(steps) <= TYPE_MAX_STEPS:
        fail(
            "type-count",
            "%d type steps: the canon allows %d..%d"
            % (len(steps), TYPE_MIN_STEPS, TYPE_MAX_STEPS),
        )

    steps.sort(key=lambda step: step[1])
    previous = None
    for role, px, node in steps:
        if px != int(px):
            fail("type-range", "type.size.%s: %g px is not an integer" % (role, px))
        if not TYPE_MIN_PX <= px <= TYPE_MAX_PX:
            fail(
                "type-range",
                "type.size.%s: %g px outside %g..%g"
                % (role, px, TYPE_MIN_PX, TYPE_MAX_PX),
            )
        if previous is not None:
            last_role, last_px = previous
            if px <= last_px:
                fail(
                    "type-order",
                    "type.size.%s (%g px) is not larger than %s (%g px)"
                    % (role, px, last_role, last_px),
                )
            else:
                step_ratio = px / last_px
                if not ratio - tolerance <= step_ratio <= ratio + tolerance:
                    fail(
                        "type-ratio",
                        "type.size.%s: step %.3f off ratio %.2f by more than %.2f"
                        % (role, step_ratio, ratio, tolerance),
                    )
        previous = (role, px)

        leading = extension(node, "lineHeight")
        if leading is None:
            fail("type-leading", "type.size.%s: no $extensions.estate.lineHeight" % role)
            continue
        if isinstance(leading, bool) or not isinstance(leading, (int, float)):
            fail("type-leading", "type.size.%s: lineHeight is not a number" % role)
            continue
        need = LEADING_BODY if role == "body" else LEADING_MIN
        if leading < need:
            fail(
                "type-leading",
                "type.size.%s: line-height %.2f below %.2f (DS-10)"
                % (role, leading, need),
            )

    if "body" not in sizes:
        fail("type-body", "type.size.body is required: it anchors the scale")
        return True
    try:
        body_px = dimension_px(sizes["body"]["$value"])
    except (ScaleError, KeyError, TypeError):
        return True
    if body_px != base:
        fail(
            "type-body",
            "type.size.body is %g px but the declared base is %g px"
            % (body_px, base),
        )
    return True


def check_space(document, fail):
    group = document.get("space")
    if not isinstance(group, dict) or not group:
        return False
    values = []
    for role in sorted(group):
        if role.startswith("$"):
            continue
        node = group[role]
        if not isinstance(node, dict) or "$value" not in node:
            fail("space-shape", "space.%s: not a token" % role)
            continue
        try:
            px = dimension_px(node["$value"], "space-unit")
        except ScaleError as exc:
            fail(exc.code, "space.%s: %s" % (role, exc.message))
            continue
        values.append((role, px))
        if px % SPACE_BASE != 0:
            fail(
                "space-multiple",
                "space.%s: %g px is not a multiple of %g (DS-11)"
                % (role, px, SPACE_BASE),
            )
        if not SPACE_MIN_PX <= px <= SPACE_MAX_PX:
            fail(
                "space-range",
                "space.%s: %g px outside %g..%g"
                % (role, px, SPACE_MIN_PX, SPACE_MAX_PX),
            )
    if not SPACE_MIN_STEPS <= len(values) <= SPACE_MAX_STEPS:
        fail(
            "space-count",
            "%d spacing steps: the canon allows %d..%d"
            % (len(values), SPACE_MIN_STEPS, SPACE_MAX_STEPS),
        )
    # Spacing roles are semantic names, so their values are checked as a set:
    # a scale is unique members starting at the base, not an alphabetical order.
    ordered = sorted(px for _, px in values)
    if len(set(ordered)) != len(ordered):
        fail("space-order", "duplicate spacing values: %r" % (ordered,))
    if ordered and ordered[0] != SPACE_BASE:
        fail(
            "space-base",
            "smallest step is %g px but the scale starts at %g px"
            % (ordered[0], SPACE_BASE),
        )
    return True


def check_motion(document, fail):
    group = document.get("motion")
    if not isinstance(group, dict) or not group:
        return False

    durations = group.get("duration") or {}
    if not isinstance(durations, dict) or not durations:
        fail("motion-shape", "motion.duration must be a token group")
        return True
    if "reduced" not in durations:
        fail(
            "motion-reduced",
            "motion.duration.reduced is required: WCAG 2.3.3 needs a 0 ms path",
        )
    for role in sorted(durations):
        if role.startswith("$"):
            continue
        node = durations[role]
        try:
            ms = dimension_px_ms(node.get("$value"))
        except ScaleError as exc:
            fail(exc.code, "motion.duration.%s: %s" % (role, exc.message))
            continue
        if role == "reduced":
            if ms != 0:
                fail(
                    "motion-reduced",
                    "motion.duration.reduced is %g ms; reduced motion must be 0" % ms,
                )
            continue
        band = MOTION_BANDS.get(role)
        if band is not None and not band[0] <= ms <= band[1]:
            fail(
                "motion-band",
                "motion.duration.%s: %g ms outside %g..%g"
                % (role, ms, band[0], band[1]),
            )
        if ms > MOTION_CEILING:
            reason = extension(node, "justification")
            if not isinstance(reason, str) or not reason.strip():
                fail(
                    "motion-justify",
                    "motion.duration.%s: %g ms over %g needs a justification (DS-12)"
                    % (role, ms, MOTION_CEILING),
                )

    easings = group.get("easing") or {}
    roles = [role for role in sorted(easings) if not role.startswith("$")] if isinstance(easings, dict) else []
    if not 2 <= len(roles) <= 5:
        fail(
            "motion-easing",
            "%d easing tokens: the canon allows 2..5, all declared" % len(roles),
        )
    for role in roles:
        value = (easings[role] or {}).get("$value")
        if not (
            isinstance(value, list)
            and len(value) == 4
            and all(
                isinstance(item, (int, float))
                and not isinstance(item, bool)
                and 0.0 <= item <= 1.0
                for item in value
            )
        ):
            fail(
                "motion-easing",
                "motion.easing.%s: expected [x1, y1, x2, y2] with every value in 0..1"
                % role,
            )
    return True


def dimension_px_ms(value):
    if isinstance(value, dict):
        unit = value.get("unit", "ms")
        if unit != "ms":
            raise ScaleError("motion-duration", "unit %r is not ms" % (unit,))
        value = value.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScaleError("motion-duration", "duration %r is not a number" % (value,))
    return float(value)


def check_scales(document, require_groups):
    findings = []

    def fail(code, message):
        findings.append({"code": code, "message": message})

    present = {
        "type scale (DS-10)": check_type(document, fail),
        "spacing scale (DS-11)": check_space(document, fail),
        "motion set (DS-12)": check_motion(document, fail),
    }
    if require_groups:
        for name, found in present.items():
            if not found:
                fail("missing-scale", "document declares no %s" % name)
    return findings


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
    require_scales = "--require-scales" in argv[1:]
    if len(paths) != 1:
        sys.stderr.write(
            "usage: check-design-tokens.py <tokens.json> [--json] [--require-scales]\n"
        )
        return 2
    try:
        with open(paths[0], encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write("check-design-tokens: cannot read %s: %s\n" % (paths[0], exc))
        return 2

    auditor = Auditor(document)
    findings = auditor.run()
    findings.extend(check_scales(document, require_scales))
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
