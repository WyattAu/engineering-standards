# ADR-0017: type, spacing and motion are gated scales, not review items

- **Status**: Proposed (2026-11-09). Ratification pending; `standards-index`
  stays advisory for one loop (AGENTS.md rule 3).
- **Date**: 2026-11-09
- **Amends**: `DESIGN.md` DS-10, DS-11, DS-12 (v0.1.0 -> v0.2.0)
- **Supersedes**: nothing
- **Related**: ADR-0013 (design canon), ADR-0016 (adoption registry)

## Context

v0.1.0 gated colour completely: twelve roles, ten declared pairs, a contrast
floor that a document cannot undercut. The rest of the visual system was
prose. DS-10 said "ratio 1.2 for dense UI, 1.25 for prose", DS-11 said
"multiples of 4 px", DS-12 said "100 to 300 ms", and every one of those
carried `REVIEW` as its evidence class.

The result is measurable and already visible. A surface can import the
twelve roles, pass the colour gate, and still invent a fourteen-step type
ramp, a 13 px gap and a 600 ms drawer. The gate reports success because it
only ever looked at hue. That is the same failure the colour canon was
written to end: a rule that is real in prose, absent in builds.

Two objections were considered and rejected:

1. **"These are judgement calls."** The judgement is in the ratio, the base
   and the bands. Once chosen, applying them is arithmetic. Where judgement
   genuinely cannot be tokenised (prose measure in characters, rhythm usage
   per component, the reduced-motion experience) the rule stays `REVIEW` and
   says so, which is SM-5 rather than a loophole.
2. **"A gate will reject legitimate designs."** It rejects undocumented
   ones. A surface with a real need for a 1.33 ratio can say so in an ADR,
   and the canon moves. A surface that just prefers 1.33 cannot, which is the
   point.

## Decision

Type, spacing and motion become token groups with closed constraints, checked
by `scripts/check-design-tokens.py`:

| Group | Constraint | Finding codes |
|---|---|---|
| `type.size` | integer px, 12..72, 4..8 steps, ratio 1.25 +/- 0.05, `body` = base (16), leading >= 1.2 (body >= 1.5), px only | `type-order`, `type-range`, `type-ratio`, `type-body`, `type-leading`, `type-unit` |
| `space` | integer px, multiples of 4, unique, 5..10 steps, starts at 4, max 96 | `space-multiple`, `space-base`, `space-order`, `space-range`, `space-count` |
| `motion.duration` | ms inside named bands (instant 0..100, fast 100..200, base 200..300, slow 300..400); > 400 needs a justification; `reduced` = 0 and required | `motion-band`, `motion-justify`, `motion-reduced` |
| `motion.easing` | 2..5 tokens, each `[x1, y1, x2, y2]` with every value in 0..1 | `motion-easing` |

The estate documents (`tokens/estate-dark.dtcg.json`,
`tokens/estate-light.dtcg.json`) gain all three groups, and CI runs the gate
with `--require-scales`, so a document cannot drop a scale and still pass.
Without the documents carrying them, the rules would validate nothing, which
is why the flag exists rather than a default.

Measured on 2026-11-09, 33 tokens per document, both clean:

- Type: 13, 16, 20, 25, 31 px. Each is `16 * 1.25^n` rounded to an integer,
  so the realised ratios are 1.231, 1.250, 1.250, 1.240 rather than a flat
  1.25. The 0.05 tolerance exists to absorb that rounding and nothing else.
- Spacing: 4, 8, 12, 16, 24, 32, 48, 64. One scale, one base, 8 px rhythm.
- Motion: 100, 150, 240, 320 ms plus 0 ms reduced; three easings, all
  coordinates inside 0..1.

## Consequences

- A surface can no longer pass the design gate with a private type ramp.
  Typography, spacing and motion move from `declared` to `advisory` in
  `STANDARDS-INDEX.md` (advisory for one loop, then blocking), which raises
  machine-checked concerns from 38 to 40 without inventing a new concern.
- The token documents become one document per variant carrying colour, type,
  space and motion. That is a smaller surface than four files, and it means
  a variant switch swaps everything at once instead of half of it.
- The gate now encodes a ratio, a base and four bands. Changing any of them
  is a material change: version bump, this ADR amended, changelog entry.
- Motion is the weakest of the three rules: the gate proves the tokens are
  sane, not that a component uses `reduced` when the media query fires. That
  path stays `TEST` per component suite, and saying so is more honest than
  claiming a gate that cannot see a stylesheet.
- Prose measure and tabular figures remain `REVIEW`. A token document has no
  line box to measure, so a visual regression harness is still the missing
  piece, and it stays named as a gap rather than implied by a green run.
