# ADR-0005: estate duplication is a forcing-function problem, not a layering problem

- **Status**: Accepted (2026-10-18)
- **Date**: 2026-10-18
- **Complements**: [ADR-0004](0004-gui-toolchain-semantics-layer-not-toolkit.md) (the semantics layer this ADR arranges), [ADR-0003](0003-adopt-harfrust-extend-font-stack-in-layers.md) (the font stack)
- **Supersedes**: nothing

## Context

The question put to this ADR was: *why does `polyfont-*` duplicate `font-*`? Was
dogfooding missing? Do the dependency management and architecture make sense?*

The prior working note on this question was partly wrong. This ADR replaces it
with what the sources actually say.

## Measurement 1: the name collision is a false friend

`polyfont-parse` does not parse fonts. Its registry description is
`"Tree-sitter-based token parsing for polyfont"` and its keywords are
`font, syntax-highlighting, textmate, tree-sitter`
(crates.io API, `polyfont-parse`, read 2026-10-18).

`estate.yml` describes the family as `"Multi-font editor plugin family
(9 crates)"` at `status: dormant`, `last_push: "2026-10-02"` (`estate.yml`,
`polyfont` block).

So the two words "font" mean different things in the two families:

| Family | What a "font" is | Crate |
| --- | --- | --- |
| `polyfont-*` | a typeface chosen per TextMate scope in a **code editor** | `polyfont-parse` (tree-sitter), `polyfont-scope` (TextMate), `polyfont-themes` (theme registry) |
| `font-parse` / `font-model` / `font-shape` | an **SFNT/OTF binary** being read, shaped, and rasterised | `font-parse`, `font-model`, `font-shape` |

Conclusion: **`polyfont-parse` and `font-parse` are not duplicated work.** One
is a syntax highlighter; the other is a font file reader. The apparent overlap
is a name collision across two different problem domains.

Two genuine adjacencies remain, and neither is a duplication to be deleted:

- `polyfont-fonts` (system font discovery, `fontdb`) overlaps
  [fontique](https://github.com/servo/fontique), which ADR-0003 already
  adopted as the estate's L0 font discovery. Resolution: use fontique, do not
  maintain a second discovery path.
- `polyfont-render` (GPU multi-font compositing) and `font-shape` (analytic
  coverage rasterisation) serve different layers. Resolution: keep both, and
  let `font-shape` sit underneath whatever composites.

**Decision**: `polyfont` stays `dormant`. It is not a consolidation target.
Any future revival must build on fontique and `font-shape`, not beside them.

## Measurement 2: the duplication that is real

The estate's `area: ui` contains 29 repos. Measured against `estate.yml`
(2026-10-18), the real duplication is three design systems and three keymaps:

| Overlap | Instances | Collapsed by | State |
| --- | --- | --- | --- |
| Design tokens | `shroom-theme` (1049 tokens, dormant), `pediment` (Starlight "Spatial Materialism"), `chisel-doc` `crates/ui-egui/src/theme.rs` (764 lines of hand-picked hex) | [`theme-kit`](https://github.com/WyattAu/theme-kit) + [`theme-egui`](https://github.com/WyattAu/theme-egui) | built, published 0.1.0, dogfooded 2026-10-18 |
| Input/keymaps | `suture-tui`, `kestrel-tui`, `chisel-doc` each own a keymap | [`tui-actions`](https://github.com/WyattAu/tui-actions) | built, published 0.1.0, not yet composed |
| Docs pipeline | `Tachyon` (16 crates), `starlight-kit`, `homebite_docs` | [`docs-core`](https://github.com/WyattAu/docs-core) | built, published 0.1.0, not yet composed |

The `chisel-doc` column is the one that made this measurable. Before
dogfooding, `theme.rs` was 764 lines of `Color32` literals with no gate. After
(`commit 5c9e7fac`), the design-system roles are
`crates/ui-egui/src/chisel-{light,dark}.tokens.json`, audited by `theme-kit`,
and the test `theme_palette::tests::every_gate_finding_is_triaged` recorded
three findings that no previous tooling could see:

| Finding | Measured | Reference |
| --- | --- | --- |
| `border` on `surface` | 1.23 to 1.39:1 (needs 3:1) | light, dark, and every dichromat variant |
| `success` on `surface` | 4.45:1 under protanopia (needs 4.5) | unprojected 5.44:1 |
| `error` on `surface` | 4.29:1 under protanopia (needs 4.5) | unprojected 7.03:1 |

Those numbers were in the shipped product and no gate reported them. That is
the cost of having no token contract.

## Measurement 3: the root cause

The layers were never the problem. The **missing forcing function** was.

`estate-integration` is the estate's composition suite. Measured 2026-10-18:

| Quantity | Value |
| --- | --- |
| Dependency declarations | 112 |
| Distinct `tests/*.rs` suites | 27 |
| Estate crates with a named suite | 63 |
| Crates flagged `published, never composed by a consumer suite` | 14 |

The 14 are: `a11y-kit`, `color-kit`, `contact-miner`, `docs-core`, `dsp-core`,
`font-parse`, `geo-kit`, `model-router`, `simd-tokenizer`, `tantivy-helper`,
`theme-egui`, `theme-kit`, `tui-actions`, `validkit-derive`. Every one of the
six crates published under ADR-0004 is on that list.

`scripts/estate-audit.py:393` emits that finding on every run. It has been
emitting it, correctly, for the whole life of the flag. **Nobody acted on it,
because a red finding with no forcing function attached is a log line, not a
blocker.** The gate was not lying. Nothing was downstream of it.

Corroborating evidence from the same period: `font-shape` shipped with a
silent hang in `add_band` (an unclamped column walk in
`font-shape/src/raster.rs`). It was found only by `font-conformance`, written
later precisely because nothing consumed `font-shape`. A crate that nothing
composes is a crate nobody runs.

## Decision

1. **Composition is the forcing function, and it is a release gate.** A crate
   in `status: core` must be composed by a named suite in
   `estate-integration`, and `scripts/estate-audit.py` must fail the build,
   not print. Promotion from `support` to `core` requires the suite; that is
   the definition of `core` at `scripts/estate-audit.py:83`.
2. **A new kit does not land until a consumer composes it.** ADR-0004's six
   crates are `status: support` for exactly this reason. `chisel-doc` was the
   first consumer, and it is what turned `theme-kit` from a published artifact
   into a measured gate.
3. **Do not fork renderers or toolkits.** ADR-0004 stands. Where an existing
   toolkit is adequate, the estate ships a semantics layer above it.
4. **Serialized semantics are the stability boundary.** The tokens
   (DTCG), the a11y tree, the keymap grammar, and the docs intermediate are
   the contracts that survive a toolkit change. Toolkit types are not: the
   `theme-egui` incident recorded in `ADR-0004` and repeated here is the
   proof. `theme-egui` was published against `egui = ">=0.36, <0.38"`; Cargo
   resolved that to 0.37 for a consumer pinning 0.36, putting **two `ecolor`
   versions** in one graph so `Visuals` stopped type-checking. Adapters are
   version-coupled to one toolkit major and must pin it exactly. The tokens
   carry no toolkit coupling at all, which is why `chisel-doc` dogfooded
   `theme-kit` and placed roles itself.

## Consequences

- `chisel-doc` now depends on `theme-kit` and `color-kit` (commit `5c9e7fac`).
  Its palette is gated, and three real contrast findings are on the record with
  measured ratios and written dispositions.
- `theme-kit` and `color-kit` can now be promoted to `core` once the gate in
  item 1 ships. `theme-egui` cannot until `chisel-doc` moves to egui 0.37; it
  waits on a consumer, not on a version bump.
- `docs-core` and `tui-actions` remain `support`. Their next step is a named
  suite, not more features.
- `polyfont` stays dormant and is removed from any consolidation plan.
  `polyfont-parse` is not a font parser and never was.
- The remaining `area: ui` gap is text editing. No crate in
  `scripts/estate-crates.txt` provides text editing or an input abstraction;
  `input-kit` and `ui-text-edit` are unowned. Both must compose before they
  publish, or they will land as two more entries on the 14-item list above.