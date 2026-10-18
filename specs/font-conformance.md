# font-conformance — the text stack's independent oracle (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file (and on [ADR-0003](../docs/adr/0003-adopt-harfrust-extend-font-stack-in-layers.md)).
> `REQ-FCN-NNN` tags are the traceability anchors the implementation must cite.

**Layer:** L3 — composition (dev-only) · **REQs:** 6 (FCN-001…006) · **Deps:** the font stack + external `read-fonts`/`skrifa`, `zeno`, `tiny-skia`, `vello_cpu` · **Date:** 2026-10-17

| Field | Value |
|---|---|
| Layer | **L3** — composes the estate font stack with the external world (corpus fetch, rival rasterizers, reference shapers). Dev-only: nothing in the estate may depend on it at runtime; it is the measurer, not a layer of the stack. |
| Pattern donor | `audiobook-conformance` (L3) — generates a corpus, cross-checks the estate crates against independent oracles, publishes the numbers. Same shape here; the corpus is fonts, the oracles are fontations/zeno/tiny-skia/vello_cpu/HarfBuzz. |
| Name | `font-conformance` — verified unclaimed (crates.io API 404, 2026-10-17) |
| Deliverable | differential reports + throughput baselines + the hostile-corpus fuzz seeds. **The rasterizer keep/merge verdict ([ADR-0004](../docs/adr/), future) is written from FCN-003's numbers — no verdict exists before the measurement.** |

## §Semantics

font-conformance answers, per estate text crate, one question: *does it agree
with an independent implementation, and what does it cost?* Agreement is
checked differentially (same bytes in, fields/ink/glyphs out, compared);
cost is a criterion baseline whose number lands in the same commit as the
code it measures (standards contract §1 — measure, never assume).

### The corpus

Two kinds of input, one manifest:

- **Real fonts**, SIL OFL licensed, fetched at build time — never committed
  (the burin-doc §1.4 font rule is the estate instinct; the manifest carries
  URL + SHA-256 so a run proves which bytes it measured, mirroring the
  asset-attestation pattern). Start: Noto Sans/Serif/Arabic/Hebrew/Devanagari,
  a variable font (Noto Sans VF), a font with rich GPOS (marks, cursive
  attachment), a mono with ligatures.
- **Hostile synthetic input** — the exact threats `font-shape`'s discipline
  names: NaN and ±inf coordinates, singular transforms, degenerate and
  self-intersecting contours, zero-area quads, million-point subpaths,
  truncated/truncated-then-padded table blobs, lying table offsets. These
  are generated, tiny, and committed — they are code, not assets.

### Differentials

1. **Parse** — `font-parse` views vs `read-fonts`/`skrifa` on the same
   bytes: every field both expose must agree (metrics, cmap mappings,
   outline coordinates, fvar axes). Divergence is a finding against *some*
   parser; the report says which, and the regression test lands in the
   estate crate.
2. **Rasterize** — `font-shape` (`fill_path`/`stroke_path`) vs `zeno`,
   `tiny-skia`, and `vello_cpu`'s sparse-strip CPU path: ink coverage within
   tolerance, bounds within a pixel, and **Err-not-panic for every corpus
   member in every implementation** (a rival's panic is a finding too).
   Throughput per rasterizer per corpus slice is recorded — this is the
   number ADR-0004 needs.
3. **Shape** — `font-compose` vs the HarfBuzz reference: harfrust's repo
   ships HarfBuzz's own conformance expectations; font-conformance runs the
   corpus through both and diffs glyphs/positions/clusters. (font-compose
   *wraps* harfrust, so this proves the bridge and the plan cache, and
   keeps us honest about which layer a bug belongs to.)

## §Requirements

| REQ | Statement | Test |
|---|---|---|
| FCN-001 | Corpus fetched at build time from a SHA-256-attested manifest; no font bytes committed; a run reports exactly which bytes it measured | manifest check + attestation in every report |
| FCN-002 | Parse differential: field agreement `font-parse` ↔ `read-fonts`/`skrifa` over the full corpus; every divergence yields a named regression test | differential suite, red on any unfiled divergence |
| FCN-003 | Raster differential: coverage/bounds tolerances vs `zeno`/`tiny-skia`/`vello_cpu` **plus** per-rasterizer throughput baselines recorded in-commit | differential suite + criterion, numbers in the commit message |
| FCN-004 | Hostile corpus: every entry point of every estate text crate returns Err, never panics; rival panics are reported as findings | fuzz seeds + smoke harness over the synthetic set |
| FCN-005 | Shape differential vs HarfBuzz conformance expectations over the corpus | conformance runner (gates FCO-001 externally) |
| FCN-006 | CI: PR smoke (subset, minutes) + nightly deep run (full corpus); reports land as artifacts, regressions fail the run | workflow, pattern: burin-doc's fuzz.yml smoke/deep split |

## §Cross-references

- [specs/font-compose.md](font-compose.md) — the crate FCN-005 gates.
- `font-shape` — FCN-003's subject; its exact-coverage properties (rect = exactly 255/0/128; triangle ink = ½·b·h) are invariants the differential must not weaken.
- `audiobook-conformance` — the oracle pattern this repo re-instantiates.
- [ADR-0003](../docs/adr/0003-adopt-harfrust-extend-font-stack-in-layers.md) — decision 3 defers the rasterizer verdict to this suite's numbers.
