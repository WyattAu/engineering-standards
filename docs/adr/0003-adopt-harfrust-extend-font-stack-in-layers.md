# ADR-0003: adopt harfrust — shaping is adopted, rasterization stays owned

- **Status**: Proposed (2026-10-17)
- **Date**: 2026-10-17
- **Supersedes**: nothing (first ADR for the `ui`/text-stack area)

## Context

The estate owns a three-crate font stack — `font-parse` (L0), `font-model`
(L1), `font-shape` (L2) — whose text half does advance/kerning layout and
bidi reordering (`shape_line`, `resolve_bidi`), and whose rasterization half
is an exact-coverage scanline filler with stroke expansion. What it does not
have is real shaping: no GSUB substitution, no GPOS mark positioning, no
script itemization. The gap is the reason the stack cannot yet back a real
text renderer.

Meanwhile the Rust shaping ecosystem went through a succession event: the
RazrFalcon lineage (`ttf-parser`/`rustybuzz`) stepped back, the HarfBuzz org
absorbed the repos, and the ecosystem (parley, cosmic-text, fontique) is
migrating to `harfrust`. Estate doctrine says adopt vs extract vs build is a
per-seam decision made on a measurement, not a vibe.

## The measurement

Verified 2026-10-17 (crates.io API, docs.rs, GitHub):

1. **`rustybuzz` is dead.** Last publish 0.20.1 (Nov 2024); repo archived
   under the harfbuzz org; README says "not developed further"; tracked as
   **RUSTSEC-2026-0206**. `ttf-parser` 0.25.1 is alive-but-frozen
   maintenance mode. Nothing in the estate currently depends on either;
   the cargo-deny advisories gate now enforces that permanently.
2. **`harfrust` 0.14.0** (2026-10-04, MIT) is the successor: official
   HarfBuzz port on `read-fonts` 0.45, owned by the HarfBuzz principals
   (dfrg, behdad, drott, rsheeter). API surface confirmed on docs.rs:
   `ShaperFont`/`Buffer`/`shape()`, reusable `ShapePlan`/`ShapePlanKey`,
   `Feature`/`Script`/`Direction`/`Language`, `ClusterLevel`, and a
   `FontFuncs` trait for overriding cmap/metrics. `core_maths` is an
   optional dep → no_std-lean. parley 0.12 (2026-10-09) and cosmic-text
   already shape through it.
3. **The upstream layering already did our work**: parley 0.12 splits
   cleanly (`parlance`, `attributed_text`, `parley_engine`, `fontique`),
   and fontations (`font-types`/`read-fonts`/`skrifa`) is Google-funded
   and strict. `font-parse` already builds on `font-types` 0.8 — the
   alignment is half-taken.
4. **Landing zones are free**: `font-compose` and `font-conformance` both
   return 404 from the crates.io API today.

What we did **not** measure yet: `font-shape`'s rasterizer vs `zeno`,
`tiny-skia-path`, and `vello_cpu` on a hostile-geometry corpus. That
measurement gates the rasterizer-merge decision (below) and is owed by
`font-conformance` before any ADR-0004 verdict.

## Decision

Four per-seam verdicts for the text stack:

1. **Adopt `harfrust` as the shaping engine.** New L2 crate `font-compose`
   over `font-model`; harfrust is an unconstrained *external* dependency,
   exactly like tokio is for `uds-kit`. We do not fork it and we do not
   re-implement GSUB/GPOS. The estate's differentiator — never-panic
   discipline, typed errors, fuzz harnesses, layer purity — wraps the
   engine; it does not replace it.
2. **Keep `font-parse` as the owned L0.** No read-fonts adoption for
   parsing; align table semantics with fontations release-by-release
   (already on `font-types`) and add interop conversions behind a feature
   where a consumer needs skrifa/read-fonts types. The rustybuzz/ttf-parser
   line is dead; read-fonts is not our layer to own.
3. **Rasterization stays in `font-shape`.** The keep-vs-merge verdict
   against `zeno`/`tiny-skia-path`/`vello_cpu` is deferred until
   `font-conformance` produces the differential + throughput baseline,
   recorded in the same commit (contract §1). No rasterizer code moves
   before that number exists.
4. **Attributed spans are deferred.** Parley's `attributed_text` (Apache-2.0
   OR MIT) is the donor when `font-compose` v0.2 needs a spans model; until
   a layout consumer exists, extraction would be a crate without a caller.

## Consequences

- Two new repos: `font-compose` (L2, `tier = "L2"` at creation,
  estate dep: `font-model` only) and `font-conformance` (L3, dev-only
  oracle suite, pattern donor: `audiobook-conformance`). Specs:
  [specs/font-compose.md](../../specs/font-compose.md),
  [specs/font-conformance.md](../../specs/font-conformance.md).
- `docs/layers.md` gains both rows at first publish; `estate.yml` gains
  both repos (`area: ui`, status `support` until a consumer suite pins
  them — candidates: the burin-doc text path, `plycharts`).
- The cargo-deny advisories gate becomes the permanent rustybuzz guard.
- The no_std story for `font-compose` is an open question (harfrust is
  no_std-lean, unproven end-to-end); v0.1 targets std+alloc and the spec
  records the question rather than answering it.
- Wave-0 boundary, recorded but not decided here: `polyfont-*` remains a
  parallel estate; the `font-*` stack is the canonical no-panic/no_std
  text line. Consolidation is its own future ADR.
