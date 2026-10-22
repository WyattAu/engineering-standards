# color-kit: colour science leaf (SPEC, implemented M1)

> **Status: IMPLEMENTED + PUBLISHED (M1, 2026-10-18).** `color-kit` 0.1.0 is
> live on crates.io; `github.com/WyattAu/color-kit`: 15 tests + doctest,
> clippy `-D warnings` clean, `no_std` verified. Two bugs
> were caught by its own tests during M1 (alpha wrongly round-tripped
> through the sRGB transfer curve; quantiser emitting duplicate centroids on
> uniform palettes): both fixed in the crate, both now regression-covered.
> Implementation deviations from this spec, recorded: `resolve`-style exact
> APCA conformance naming is deliberately neutral (`lightness_contrast`); the
> OkLCH hue is stored in radians (not degrees); `quantize` is farthest-point
> seeded (not k-means++) so a uniform palette yields one colour, not `n`
> duplicates.
> `REQ-COL-NNN` tags are the traceability anchors the implementation must cite.

**Layer:** L0: leaf · **REQs:** 7 (COL-001…007) · **Deps:** `libm` (no_std transcendentals) only · **no_std:** yes + alloc · **Date:** 2026-10-18

| Field | Value |
|---|---|
| Layer | **L0: leaf.** Zero estate-internal deps by mandate; `libm` mirrors `dsp-core`'s no_std float precedent. |
| Manifest declaration | `[package.metadata.layers] tier = "L0"` at repo creation |
| External deps | `libm` only. No serde by default (optional feature for the DTCG bridge, which lives in `theme-kit`). |
| Donor | `shroom-theme`'s `color-science.js` + `wcag-contrast.js` (linear-RGB compositing, WCAG 2.1 AA, lightness separation, dichromat simulation): ported, then the JS retires. |
| Name | `color-kit`: verified unclaimed (crates.io 404, 2026-10-18); `color-core` is taken (0.1.6, 19.7K dl) and avoided. |

## §Semantics

The estate's numeric colour core: one colour type, one set of conversions,
four computations. It answers questions every surface asks: is this pair
legible (WCAG), is this text louder than that (APCA-Lc), what does a
dichromat see (Brettel/Viénot), and does this colour even fit in sRGB
(gamut mapping). It owns no opinions about design; `theme-kit` (L1) owns
the opinions.

### One type, one working space

All internal arithmetic in **linear sRGB** (f64), with sRGB transfer,
Oklab/OkLCH round-trips, and a gamut-mapping boundary (CSS Color 4 style
with a documented clipping threshold). Display values (`Rgba8`) are a
view, not the storage type: compositing happens in linear space, which is
where shroom-theme's alpha-composited tokens get their correctness.

### Four computations, named honestly

1. **WCAG 2.1 contrast ratio**: (REQ-COL-003) the gate threshold everyone
   cites; relative luminance per WCAG.
2. **Lightness contrast (Lc)**: (REQ-COL-004) the perceptual ranking used
   by the shroom themes and modern accessibility guidance. **Naming and
   licensing:** the reference implementation ships under the Limited W3
   License, which restricts conformance claims and marks. The math is
   portable; this crate computes it under a neutral name (`lightness_contrast`)
   and claims no conformance. No crate, doc, or message in this family uses
   the upstream acronym.
3. **CVD simulation**: (REQ-COL-005) Brettel/Viénot dichromat projection
   in linear RGB, used both to *adapt* palettes and to *test* that
   adaptation (the deuteranopia fixture is the collision detector).
4. **Palette quantisation**: (REQ-COL-006) perceptual k-means toward
   N-colour targets (16/256), seed → terminal palette.

### Never panic, total on garbage

NaN/inf/out-of-gamut inputs yield typed `ColorError`s or documented
saturation rules: the decoder discipline from `font-parse`/`wire-kit`
(REQ-COL-007). This is not cosmetic: the theme gate runs on every authored
token, and a panic there would be a build-time crash from a colour literal.

## §API sketch

```rust
#![no_std]  // + alloc
pub struct Rgba { r: f64, g: f64, b: f64, a: f64 }   // LINEAR sRGB, 0..1

impl Rgba {
    pub fn from_srgb8(r: u8, g: u8, b: u8, a: u8) -> Self;
    pub fn to_srgb8(self) -> Result<Rgba8, ColorError>;        // gamut-mapped
    pub fn oklch(self) -> Oklch; pub fn from_oklch(c: Oklch) -> Result<Self, ColorError>;
    pub fn composite_over(self, bg: Rgba) -> Rgba;             // linear-space alpha
}

/// REQ-COL-003: WCAG 2.1 contrast ratio. Returns None for garbage inputs.
pub fn contrast_ratio(fg: Rgba, bg: Rgba) -> Option<f64>;

/// REQ-COL-004: perceptual lightness contrast (neutral name; see §Semantics).
pub fn lightness_contrast(fg: Rgba, bg: Rgba) -> Option<f64>;

/// REQ-COL-005: dichromat simulation (Brettel–Viénot), linear RGB.
pub fn simulate_cvd(c: Rgba, kind: CvdKind) -> Rgba;

/// REQ-COL-006: quantise toward n colours, deterministic given the seed.
pub fn quantize(palette: &[Rgba], n: usize, seed: u64) -> Vec<Rgba>;
```

## §Requirements

| REQ | Statement | Test |
|---|---|---|
| COL-001 | Linear-sRGB working type with exact sRGB↔linear transfer round-trips | property (all 2^24 u32 colours round-trip) |
| COL-002 | Oklab/OkLCH round-trip within 1e-9; out-of-sRGB OkLCH is a typed error or documented mapping | property + fixtures |
| COL-003 | `contrast_ratio` matches the WCAG 2.1 reference values (the standard's published examples) | golden values (white/black = 21:1, etc.) |
| COL-004 | `lightness_contrast` matches the reference algorithm's outputs (port conformance set) | golden values from the reference test vectors |
| COL-005 | CVD simulation: known dichromat probe colours map within tolerance; the deuteranopia fixture from shroom-theme is the regression | fixture + property (idempotence, symmetry) |
| COL-006 | Quantisation deterministic for a seed; k-means terminates on all-NaN/degenerate palettes (REQ-COL-007) | property: no hang, no panic, bounded iterations |
| COL-007 | No panics, no indexing: NaN/inf/empty inputs are typed results on every public fn | exhaustive edge table (the font-parse discipline) |

## §Cross-references

- [specs/theme-kit.md](theme-kit.md): the L1 consumer; owns all design opinions, this crate owns none of the maths' *meaning*.
- `shroom-theme`: donor of the algorithms and the CV/fixture corpus; retires its JS pipeline once the Rust gate is green.
- `dsp-core` (L0): the no_std + libm precedent this crate mirrors.
- `font-parse`/`font-shape`: the decoder/renderer discipline (total functions, typed errors, no panics) that COL-007 enforces.
- ADR-0004 §2/§Consequences: naming/licensing constraints (neutral APCA name, no brand claims).
