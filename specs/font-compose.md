# font-compose — script shaping over the font stack (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file (and on [ADR-0003](../docs/adr/0003-adopt-harfrust-extend-font-stack-in-layers.md)).
> `REQ-FCO-NNN` tags below are the traceability anchors the implementation must
> cite: doc comments on public items carry the tags, every REQ maps to ≥ 1
> named test (provisional matrix in §Requirements).

**Layer:** L2 — domain · **REQs:** 8 (FCO-001…008) · **Deps:** `font-model` (L1) + external `harfrust` 0.14, `thiserror` — nothing else · **no_std:** open question · **Date:** 2026-10-17

| Field | Value |
|---|---|
| Layer | **L2 — domain.** Ceiling rule: only estate dep is `font-model` (L1). Same-layer composition with `font-shape` (L2) is legal but v0.1 has none — see §Cross-references. |
| Manifest declaration | `[package.metadata.layers] tier = "L2"` at repo creation |
| External deps | `harfrust` 0.14 (MIT; pulls `read-fonts` 0.45, `bitflags`, `bytemuck`, `smallvec`, optional `icu_normalizer`/`icu_properties`/`core_maths`), `thiserror` 2. No `rustybuzz` (RUSTSEC-2026-0206), no `ttf-parser`, no `swash`. |
| Name | `font-compose` — verified unclaimed (crates.io API 404, 2026-10-17) |
| Sibling | `font-shape` (L2) owns **drawing and measuring** (rasterize, kern-advance, bidi levels); `font-compose` owns **substitution and positioning** (GSUB/GPOS, script itemization). Neither subsumes the other. |

## §Semantics

font-compose turns a Unicode run plus a font into the glyph sequence a
rasterizer can draw: which glyphs (GSUB), where they sit (GPOS), and which
input characters they answer for (clusters). It is a thin, disciplined shell
around harfrust — the estate adds the vocabulary, the error taxonomy, the
plan cache, and the never-panic guarantee; it does not re-implement the
engine.

### One bidi oracle

Bidi levels are computed **once** in the estate, by `font-shape`'s
`resolve_bidi` (REQ-FCO-002). font-compose consumes
`font_shape`-equivalent levels as input and never recomputes them; given
explicit levels it only itemizes scripts and directions for harfrust.
Two bidi implementations would be two answers to one question.

### The bridge

harfrust reads GSUB/GPOS/GDEF/cmap from font bytes through `read-fonts`.
The estate holds the same bytes through `font-parse`'s zero-copy views and
the typed `font-model::Font`. The bridge is deliberately boring:

- font bytes enter once as `&[u8]`; harfrust's `FontRef` borrows them
  (no estate-side copy of table data);
- the `font-model::Font` rides along for validated metrics, upem, and the
  owned outline/glyph model the *rasterizer* consumes next;
- glyph ids are font-global, so `font_model::GlyphId` (u16 domain) and
  harfrust's 32-bit `GlyphId` convert by checked widening/narrowing
  (REQ-FCO-006) — no mapping table exists or is needed;
- variable-font locations are harfrust `Font` coordinates built from
  `font-parse`'s parsed `fvar` axes (REQ-FCO-003).

If a future harfrust makes the read-fonts coupling pluggable beyond
`FontFuncs` (cmap/metrics only — not enough for shaping), re-evaluate; until
then the byte bridge is the whole integration surface.

### Plans are reused, runs are cheap

A `ShapePlan` is keyed by (script, direction, language, features,
coordinate hash) and cached (REQ-FCO-004). Shaping a run must never rebuild
a plan; the speedup is a criterion bench whose number is recorded in the
same commit that adds the cache (contract §1).

### Never crash

Hostile bytes are the norm: every font-compose entry point takes data an
untrusted caller supplied. A truncated GPOS, a lying table offset, a glyph
id outside the u16 domain all yield a typed `ComposeError` naming the table
and reason — never a panic (REQ-FCO-005). read-fonts does the bounds
checking; this crate wraps it and owns the guarantee. The fuzz target is
byte-entry `shape`, and its corpus seeds from `font-conformance`'s hostile
set.

## §API sketch

```rust
// features: std (default) · icu (harfrust normalization, on by default upstream)
// no_std: open question — harfrust is core_maths-lean but unproven end-to-end;
// v0.1 ships std+alloc and records the answer, it does not promise it.

/// REQ-FCO-001: GSUB/GPOS/GDEF shaping with cluster mapping preserved.
/// REQ-FCO-004: plans cached per (script, direction, language, features, coords).
pub struct Composer { /* … */ }

impl Composer {
    /// Borrow font bytes; `model` is the validated L1 view of the same font.
    pub fn new(bytes: &[u8], model: &Font) -> Result<Self, ComposeError>;

    /// REQ-FCO-003: pin a variable-font location (axes validated against fvar).
    pub fn at_location(self, coords: &[(Tag, f32)]) -> Result<Self, ComposeError>;
}

/// REQ-FCO-002: levels come from the caller (font-shape's resolve_bidi);
/// this crate itemizes scripts and drives harfrust — it never re-derives bidi.
pub struct Run<'a> {
    pub text: &'a str,
    pub level: u8,                 // explicit bidi level from font-shape
    pub language: Option<Language>,
    pub features: &'a [Feature],   // REQ-FCO-007: e.g. disable `liga`
}

pub struct ShapedRun {
    pub glyphs: Vec<ShapedGlyph>,  // REQ-FCO-006: font_model::GlyphId domain
    pub clusters: ClusterMap,      // REQ-FCO-001: glyph ↔ source-char mapping
}

impl ShapedGlyph {
    pub fn id(&self) -> font_model::GlyphId;
    pub fn advance(&self) -> (i32, i32);       // font units
    pub fn offset(&self) -> (i32, i32);        // GPOS-adjusted, font units
    /// REQ-FCO-008: ink extents for the rasterizer handoff.
    pub fn extents(&self) -> Result<InkExtents, ComposeError>;
}
```

Open at implementation time: the hand-off type to `font-shape` — feed
`ShapedGlyph` positions into `rasterize_glyph` directly, or widen
`font-shape`'s `ShapedLine`/`GlyphPlacement` to accept GPOS offsets. Decide
with the first consumer in front of you, not in this spec.

## §Requirements

| REQ | Statement | Test |
|---|---|---|
| FCO-001 | Shaping applies GSUB + GPOS + GDEF and preserves cluster mapping (`ClusterLevel::MonotoneGraphemes` default, settable) | conformance corpus vs HarfBuzz expected outputs (font-conformance) |
| FCO-002 | Explicit bidi levels are honored, never recomputed; script/direction itemization feeds harfrust | unit: RTL run with caller-set levels; property: levels in ⇒ same levels out |
| FCO-003 | Variable fonts shape at any fvar-validated location; axes outside fvar are a typed error | unit: wght 100..900 drift on a VF corpus font |
| FCO-004 | `ShapePlan` reuse: repeated runs with the same key never rebuild the plan | criterion bench, number recorded in the commit |
| FCO-005 | Malformed/truncated bytes → typed `ComposeError`, never panic | fuzz: `shape` byte-entry, Err-not-panic |
| FCO-006 | Glyph ids stay in `font_model::GlyphId`'s u16 domain; out-of-domain harfrust ids are typed errors | unit + property over corpus |
| FCO-007 | OpenType features and buffer flags pass through to the engine | unit: `liga` off changes output on a corpus font with ligs |
| FCO-008 | Per-glyph ink extents available for rasterization handoff | unit vs `font-shape::glyph_path` bounds |

## §Cross-references

- `font-shape` (L2) — owns bidi levels and rasterization; consumes `ShapedGlyph`s.
- `font-model` (L1) / `font-parse` (L0) — the owned model and byte views under everything.
- `font-conformance` (L3, specced alongside) — the oracle; FCO-001/005 verdicts land there.
- [ADR-0003](../docs/adr/0003-adopt-harfrust-extend-font-stack-in-layers.md) — the adopt-vs-extract decision this spec implements.
- Boundary: `polyfont-*` is the parallel estate; no dependency either way until the consolidation ADR.
