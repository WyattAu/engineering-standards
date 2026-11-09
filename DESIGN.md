# DESIGN: the visual and interaction canon

> **Status: PROPOSED (v0.2.0, 2026-11-09).** Ratification: ADR-0013;
> type, spacing and motion gates: ADR-0017.
> Numeric core: `color-kit` (specs/color-kit.md). Token contract and gate:
> `theme-kit` (specs/theme-kit.md). This document is the estate-level policy
> those crates implement, so a surface can be judged without reading crate
> source.

**Applies to:** every rendered surface (web, desktop, TUI, docs sites,
charts, email HTML) and every design artifact that feeds one.
**Oracle:** `scripts/check-design-tokens.py` over a DTCG token document.

## Why a design standard at all

Design decisions fail in a different way from code: they fail silently,
by degrees, in front of users, and they are usually defended with taste
instead of numbers. The estate had three design systems and four UI stacks
before a single token contract (ADR-0004). The fix is the same one used for
code: one address per concern, a number per rule, and a gate that fails the
build instead of shipping a 2.31:1 border.

Every rule below states the number, the source, and the reason. A rule whose
reason is only "it looks better" is marked `REVIEW` and says so.

## DS-1 Authored colour exists only at the role layer

**MUST.** Components, pages, and themes consume semantic roles
(`surface`, `on-surface`, `accent`, `on-accent`, `border`, `focus-ring`,
`warn`, `error`, `success`, `selection`, `on-surface-muted`). A hex, rgb(),
or hsl() literal outside the role definition file fails the gate.

- Evidence: `GATE` (`check-design-tokens.py`: every colour token must be
  reachable from a declared pair or carry an explicit `ungated` reason)
- Why: a literal is a decision with no address. It cannot be re-derived for
  dark mode, high contrast, or a CVD variant, so it silently becomes the one
  pixel that ignores every other rule.

## DS-2 All colour arithmetic happens in linear sRGB, with Oklab for perception

**MUST.** Compositing, gradient interpolation, and alpha blending happen in
linear light. Perceptual comparisons, lightness targeting, and palette
generation use Oklab/OkLCH. sRGB8 is a display encoding, never a working
type.

- Threshold: two colours are "the same colour" only at delta-E-Ok <= 0.02
  (just-noticeable difference is ~0.02 in Oklab; below it, treat as equal)
- Evidence: `TEST` (color-kit REQ-COL-001/002 round-trip properties)
- Why: gamma-encoded blending darkens the midpoint and makes 50% alpha
  compositing wrong in a way nobody notices until a token is stacked twice.
  Oklab comparisons stop hue-shift arguments that are really lightness
  arguments.

## DS-3 Text contrast is a build gate, not a review comment

**MUST.** Every declared text pair meets, at minimum:

| Text | Ratio | Source |
|---|---|---|
| Body text (< 18.66px regular, < 24px bold) | >= 4.5:1 | WCAG 2.1 SC 1.4.3 (AA) |
| Large text (>= 18.66px regular, >= 24px bold) | >= 3:1 | WCAG 2.1 SC 1.4.3 (AA) |
| Any text claiming AAA | >= 7:1 (>= 4.5:1 large) | WCAG 2.1 SC 1.4.6 |
| Placeholder and disabled text | >= 3:1, and never the only cue | WCAG 2.1 SC 1.4.3 + 1.4.1 |

- Evidence: `GATE` (`check-design-tokens.py`, thresholds read from the pair
  declaration; default 4.5 for `kind: text`, 3.0 for `kind: large|ui`)
- Why: 4.5:1 is the level where large populations read without strain at
  default sizes; it is also the only threshold with legal force in several
  jurisdictions (EN 301 549, ADA case law). A ratio computed from
  gamma-encoded values is the classic wrong answer, hence DS-2.

## DS-4 Non-text contrast and focus are gated too

**MUST.** Borders, dividers that carry meaning, icons, form control
boundaries, chart strokes, and focus indicators meet >= 3:1 against the
adjacent colour. A focus indicator MUST be >= 3:1 against both the component
and the background, and >= 2 CSS px thick (or an equivalent area).

- Threshold: 3:1 (WCAG 2.1 SC 1.4.11); 2 px (WCAG 2.2 SC 2.4.13 Focus
  Appearance, minimum area)
- Evidence: `GATE` (pairs with `kind: ui`), `TEST` (focus-ring visibility
  assertion in the component suite)
- Why: the estate's own theme-kit gate rejected its first fixture at 2.31:1
  (`#6e7681` border on `#0d1117`). That is the exact class of bug a human
  reviewer approves and a keyboard user cannot see.

## DS-5 Perceptual separation is declared per component rank

**MUST.** Where two roles must read as "quieter" or "louder" than each
other (surface vs raised surface, muted vs body text, warn vs error), the
separation is declared and checked, using lightness contrast.

- Threshold: body-level rank separation >= 60 Lc; large text and
  high-contrast variants >= 75 Lc; any declared pair >= 45 Lc
- Naming: the computation is exposed as `lightness_contrast`, never by the
  upstream acronym (licence restricts conformance claims; ADR-0004)
- Evidence: `TEST` (theme-kit REQ-THM-004 rank assertions)
- Why: WCAG ratio alone cannot express "this is one step louder"; it is a
  ratio against a background, not a rank. Rank is what makes a design
  system feel ordered, and it is the property that breaks first when a
  palette is hand-tweaked.

## DS-6 Colour is never the only channel

**MUST.** Every state that uses colour also carries a second signal: text,
icon, position, underline, or pattern. Error and success MUST differ in
shape or label, not only in hue. Each semantic pair MUST survive all three
dichromacies (protan, deutan, tritan) without collapsing.

- Threshold: adjacent semantic roles stay distinguishable under Brettel/
  Viénot simulation (no pair converges to delta-E-Ok <= 0.02); contrast
  ratio against the shared background stays >= 3:1 after simulation
- Evidence: `TEST` (theme-kit REQ-THM-005 collision check) + `GATE`
- Why: roughly 8% of men and 0.5% of women have a CVD; red/green error
  states are the single most common accessibility regression in forms, and
  they are invisible to the person who authored them.

## DS-7 Variants are derived, deterministic, and never hand-authored

**MUST.** Light, dark, high-contrast, monochrome, and CVD-adapted variants
are produced by declared derivation modes from one seed palette. No variant
carries an authored colour that does not exist in the seed graph. Derivation
is byte-deterministic for a given seed and version.

- Threshold: identical seed + version => identical serialized output
  (sha256 stable across runs and feature sets)
- Evidence: `TEST` (theme-kit REQ-THM-006/009)
- Why: seven hand-maintained palettes drift within one release cycle. A
  derived variant cannot drift, and the diff of a seed change tells you
  exactly what every surface will do.

## DS-8 Dark mode is a re-derivation, not an inversion

**MUST.** Dark mode re-derives surfaces by elevation (raised surfaces get
lighter, not darker) and re-checks every DS-3/DS-4 threshold in the dark
graph. `filter: invert()` and pure `#000`/`#fff` extremes are banned for
large surfaces.

- Threshold: all DS-3 and DS-4 ratios hold in every declared variant;
  surface elevation step >= 2% relative luminance
- Evidence: `GATE` (the gate runs every variant in the document)
- Why: inversion inverts the meaning of hierarchy: shadows become glows and
  raised panels sink. Pure black makes OLED smearing and halation visible;
  every major design system moved off it.

## DS-9 Token naming is semantic, DTCG 2025.10, and closed

**MUST.** Tokens are DTCG 2025.10 JSON. Names describe role or intent, never
appearance or brand (`color.text.muted`, not `color.grey-500`). The role
vocabulary is a closed enum: an unknown key is an error, not a new token.
Hue-named tokens are allowed only inside the seed palette layer.

- Evidence: `GATE` (schema + closed vocabulary), `TEST` (round-trip
  byte-stability, theme-kit REQ-THM-001/002)
- Why: `grey-500` is a question ("500 of what?") and a lie the moment the
  palette changes. Semantic names survive a rebrand; appearance names are a
  rename project.

## DS-10 Type: one integer scale per surface, leading attached

**MUST.** Type sizes are `type.size.*` tokens: integer CSS px, 12 to 72, 4
to 8 steps, all on one ratio. The estate ratio is 1.25, and each
consecutive step must land within 0.05 of it, because integer rounding
moves a step by less than that only when the scale is honest. `body` MUST
equal the declared base (16 px), and every size MUST carry a line height of
at least 1.2, with `body` at 1.5 or more. Units other than px fail: a rem
scale drifts with the reader's font size.

- Evidence: `GATE` (`type-order`, `type-range`, `type-ratio`, `type-body`,
  `type-leading`, `type-unit`)
- Why: 1.25 is the smallest ratio whose steps stay distinguishable at body
  size and the largest that still fits five steps between 13 and 31 px.
  Attaching leading to the size token is what stops 31 px display text from
  arriving with body leading bolted on in a component. Prose measure (45 to
  75 characters) and tabular figures stay `REVIEW`: both need a rendered
  line box, not a token document.

## DS-11 Spacing is a 4 px base with an 8 px rhythm

**MUST.** Spacing tokens are integer CSS px, multiples of 4, unique, 5 to
10 steps, starting at exactly 4 and ending at or below 96. The base (4) and
the layout rhythm (8) are declared on the `space` group.
**REVIEW.** Stacks, card padding and section gaps use the multiples of 8
(8, 16, 24, 32); optical adjustments below the base are not tokens.

- Evidence: `GATE` (`space-multiple`, `space-base`, `space-order`,
  `space-range`, `space-count`), `REVIEW` (rhythm usage in a surface)
- Why: a single base makes every gap alignable by construction and ends the
  "nudge it 3 px" negotiation. 4 and 8 survive fractional device pixel
  ratios; 13 px never does. The gate sees the scale, not which member a
  component picked, so rhythm usage is the one part a reader still checks.

## DS-12 Motion is short, purposeful, and reducible

**MUST.** Durations are `motion.duration.*` tokens in ms, inside their
named bands: `instant` 0 to 100, `fast` 100 to 200, `base` 200 to 300,
`slow` 300 to 400. Nothing above 400 ms without
`$extensions.estate.justification`. `motion.duration.reduced` MUST be 0 and
MUST be the path taken under `prefers-reduced-motion: reduce` (WCAG 2.3.3).
Curves are `motion.easing.*` tokens, 2 to 5 of them, each a cubic-bezier
with all four values in 0 to 1.

- Evidence: `GATE` (`motion-band`, `motion-justify`, `motion-reduced`,
  `motion-easing`), `TEST` (the reduced-motion path is asserted wherever a
  surface has a component suite)
- Why: above ~200 ms an interaction stops feeling like a response; below
  ~100 ms it reads as a jump. Reducing motion is not cosmetic: for
  vestibular disorders it is the difference between usable and nauseating,
  which is why the 0 ms token is mandatory rather than advisory.

## DS-13 State layers are composited, never authored

**MUST.** Hover, focus, active, and disabled states are alpha composites of
the role colour over its background (typical 8% hover, 12% focus, 16%
pressed), not new hex values. Pressed is never lighter than hover.

- Evidence: `GATE` (no state token may carry an authored literal outside the
  state-overlay scale), `TEST` (contrast of every state remains >= DS-3)
- Why: authored state colours are the most common source of "the button
  looks fine until dark mode". Compositing keeps the state derived from the
  role, so it inherits every fix.

## DS-14 Data visualisation uses a bounded, ordered palette

**MUST.** Categorical palettes have at most 8 series; beyond that, group or
facet. Series colours are CVD-separated (DS-6). Sequential scales are
monotonic in lightness with a declared direction. Never encode a value with
hue alone and never use a rainbow scale for ordered data.

- Evidence: `GATE` (palette fixture under CVD simulation), `REVIEW` (chart
  in PR)
- Why: more than ~8 categories is beyond what a legend can support, and
  rainbow scales create false boundaries where the data is continuous.

## DS-15 Focus, selection, and disabled are distinct and all visible

**MUST.** Focus ring: >= 3:1 against both neighbours, 2 px, never removed
without an equivalent. Selection: distinguishable from hover and from
focus. Disabled: >= 3:1 text, `aria-disabled` (not `pointer-events: none`
alone), and never the only indication that an action is unavailable.

- Evidence: `TEST` (component suite) + `GATE` (DS-4 pairs)
- Why: `outline: none` is the single most common accessibility defect in
  the wild, and a disabled control that cannot be read is indistinguishable
  from a broken one.

## DS-16 Icons carry meaning only with a label

**MUST.** An icon that conveys information has an accessible name (visible
label or `aria-label`); decorative icons are `aria-hidden="true"`. Icon-only
controls have a tooltip and an accessible name. Icons use the same stroke
weight and optical size within a surface.

- Evidence: `TEST` (a11y tree audit, `a11y-kit`)
- Why: an unlabelled icon button is a riddle to a screen reader and to
  anyone who has not learned the glyph. Naming it costs one attribute.

## DS-17 Licensing and naming of colour science

**MUST.** The perceptual contrast computation is never exposed under the
upstream brand acronym, and no doc, crate name, or marketing claims
conformance to it. The WCAG ratio may be named as such (it is a W3C
recommendation, not a restricted mark).

- Evidence: `REVIEW` (naming check in PR) + `TEST` (public API surface
  snapshot contains `lightness_contrast` only)
- Why: the reference implementation's licence restricts conformance claims
  and marks. Porting the math is fine; claiming the brand is not.

## DS-18 Localisation changes the layout, so it is a design constraint

**MUST.** No text container is sized to the English string. Layouts survive
+30% string growth (German, Finnish) and -30% (Chinese, Japanese) without
clipping or overlap. Logical properties (`margin-inline-start`, not
`margin-left`) are used so RTL mirrors without a stylesheet. No text baked
into images.

- Evidence: `REVIEW` (pseudo-locale screenshot) + `TEST` (pseudo-locale
  layout assertion where the stack supports it)
- Why: +30% is the measured p95 expansion for Germanic languages against
  English, and a clipped button label is a functional bug, not a polish
  item.

## DS-19 Exceptions are declared with owner, reason, and expiry

**MUST.** A token that cannot meet a threshold carries
`$extensions.estate.ungated` with a non-empty reason, or a dated exception
entry naming owner and expiry. The gate fails on an undeclared exception
and reports declared ones on every run. Expired exceptions fail.

- Evidence: `GATE` (undeclared exception = failure; declared = counted)
- Why: the alternative is a gate everyone disables. A dated exception is
  pressure with a deadline; a silent one is decay.

## Conformance summary

| Level | Requires |
|---|---|
| Baseline (every surface) | DS-1, DS-2, DS-3, DS-4, DS-6, DS-9, DS-13, DS-19 |
| Product surface | Baseline + DS-5, DS-7, DS-8, DS-10, DS-11, DS-12, DS-15, DS-16 |
| Public or regulated surface | Product + DS-14, DS-17, DS-18 and a recorded `MEASURE` snapshot per release |

## Reference palette

`tokens/estate-dark.dtcg.json` and `tokens/estate-light.dtcg.json` are the
canonical seed documents: twelve roles each, exactly theme-kit's closed
vocabulary (REQ-THM-002), ten declared pairs each (REQ-THM-003). Measured
by the gate on 2026-11-09, not asserted:

| Pair | Dark | Light | Floor |
|---|---|---|---|
| body on surface | 16.02:1 | 15.80:1 | 4.5:1 |
| body on raised surface | 14.64:1 | 14.84:1 | 4.5:1 |
| muted on surface | 7.50:1 | 6.11:1 | 4.5:1 |
| on-accent on accent | 4.63:1 | 5.19:1 | 4.5:1 |
| warn on surface | 7.50:1 | 4.87:1 | 4.5:1 |
| error on surface | 5.65:1 | 5.36:1 | 4.5:1 |
| success on surface | 7.45:1 | 5.08:1 | 4.5:1 |
| body on selection | 7.19:1 | 10.65:1 | 4.5:1 |
| border on surface | 4.12:1 | 4.55:1 | 3:1 |
| focus ring on surface | 7.49:1 | 5.19:1 | 3:1 |

Both documents are gated in CI. The tightest margin is the accent label at
4.63:1, which is the one pair a future palette change is most likely to
break, so it is the one worth watching in review.

## Type, spacing and motion scales

The same two documents carry the non-colour scales, because a surface that
imports roles without sizes still invents its own type ramp. Measured by
the gate on 2026-11-09 (33 tokens per document):

| Type step | px | Step ratio | Line height |
|---|---|---|---|
| caption | 13 | 1.231 from body | 1.55 |
| body | 16 | base | 1.50 |
| title | 20 | 1.250 | 1.40 |
| heading | 25 | 1.250 | 1.25 |
| display | 31 | 1.240 | 1.20 |

Every step is `16 * 1.25^n` rounded to an integer, which is why the ratios
read 1.231 and 1.240 rather than a flat 1.25: the rounding is the price of
integer px, and the 0.05 tolerance is what makes that honest instead of a
loophole.

| Scale | Members | Constraint |
|---|---|---|
| space | 4, 8, 12, 16, 24, 32, 48, 64 | multiples of 4, base 4, rhythm 8 |
| duration | 100, 150, 240, 320, 0 (reduced) | bands: instant, fast, base, slow |
| easing | 3 cubic-beziers | all coordinates in 0..1 |

`scripts/check-design-tokens.py` implements the machine-checkable subset:
DS-1 (coverage and declared exceptions), DS-3, DS-4, DS-9 (resolution),
DS-10 to DS-12 (scales and motion), and DS-19. DS-2, DS-5, DS-6, DS-7, DS-8
live in the `color-kit` / `theme-kit` test suites; DS-14 to DS-18 are
`REVIEW` items until a visual regression harness exists, and are labelled as
such in `STANDARDS-INDEX.md`. The `--require-scales` flag is what makes the
three groups mandatory rather than merely validated when present, and CI
passes it for both estate documents.
