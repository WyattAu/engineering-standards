# ADR-0004: the GUI toolchain is a semantics layer, not a toolkit

- **Status**: Accepted (2026-10-18): owner ratified on the record; M1 implemented and published the same day
- **Date**: 2026-10-18
- **Complements**: [ADR-0003](0003-adopt-harfrust-extend-font-stack-in-layers.md) (text stack), Wave 2 `a11y-kit` (unchanged, now sequenced first-class)
- **Supersedes**: nothing

## Outcome record (added 2026-10-18, post-publication)

The M1 slice of this ADR is **built, tested, published, and dogfooded**:

| Crate | Layer | crates.io | Tests | Role |
| --- | --- | --- | --- | --- |
| `color-kit` | L0 | 0.1.0 | 15 + doctest, `no_std` ✓ | colour science leaf (adopted color-kit spec) |
| `theme-kit` | L1 | 0.1.0 | 16 + doctest | token contract + build-failing WCAG gate (adopted theme-kit spec) |
| `a11y-kit` | L1 | 0.1.0 | 11 + doctest | semantic node model + headless tree audit (the keystone) |
| `theme-egui` | L2 | 0.1.0 | 7 + doctest | **first cross-stack dogfood** (egui `Visuals` lowering, THM-008) |
| `tui-actions` | L2 | 0.1.0 | 12 + doctest | input layer consolidating three TUIs' keymaps |
| `docs-core` | L2 | 0.1.0 | 11 + 9 `bun` | docs pipeline + astro-island-compatible emission |
| `font-conformance` | L3 | (unpublished, dev-only) | 5 | differential oracle: found the `font-shape` hang |

Registry bookkeeping done: `docs/layers.md` (173 crates), `estate.yml`,
`scripts/estate-crates.txt` (175), and `scripts/estate-tiers.json` (174) all
carry the new tiers, and `scripts/check-layers.py` now **enforces** the
direction (`theme-kit` L1 → `color-kit` L0; `theme-egui` L2 → both) rather
than running in rollout mode.

Decisions 4–6 of this ADR (TUI consolidation, docs consolidation, and the
explicit out-of-scope list) remain **unimplemented proposals**: recorded
here so the record shows what was ratified versus what is still roadmap.

## Context

The estate runs **four** Rust GUI stacks and **three** custom design systems
before any of them are kits:

| Surface | Stack |
| --- | --- |
| `chisel-doc` (PDF editor) | egui + eframe + vello (0.36/0.37) |
| `kestrel` (mail) | ratatui (TUI) + Slint (GUI shell) |
| `aileron` (tiling web env, 57K LOC) | wry/WebKitGTK + Leptos-WASM + Lua |
| `suture-tui`, `kestrel-tui` | ratatui |
| `pediment` (TS) | Astro+Solid+Starlight design tokens ("Spatial Materialism") |
| `shroom-theme` (TS/JS) | 1049 tokens, WCAG 2.1 AA, APCA separation, CVD dichromat simulation, 7 variants, 9 export formats |
| `Tachyon` (Rust, 16 crates) | Markdown→HTML, SSG, JIT dev server, CRDT, Tantivy search, KaTeX: an Astro replacement already exists |

The ask: "a Qt-alternative in Rust with none of the bad practices." Four
stacks and three design systems is not a toolkit: it is duplicated
semantics with no shared layer.

## The measurement

Verified Oct 17–18, 2026 (crates.io/docs.rs/GitHub + research sweep):

1. **The lower half is solved and adopted.** wgpu 30, winit 0.30, parley
   0.11 + fontique, harfrust 0.14, skrifa/swash, icu4x 2.2, taffy 0.12,
   accesskit 0.25.1: every stack already sits on these or equivalents. The
   text layer is consolidating *around our own stack's opinions*: parley
   landed in Slint/floem/Bevy; egui took harfrust/skrifa/vello but kept its
   own layout ("consume the bricks, own the wall": their stated reason).
2. **The upper half is unfunded.** No native print dialog exists in Rust on
   any platform. No rich-text editing widget: every editor builds its own.
   Docking = `egui_dock`/`egui_tiles` (third-party, one framework). Native
   menus/tray on Linux require a GTK thread: and tauri-apps owns
   `tao`, `muda`, `tray-icon`, `global-hotkey` (any non-Tauri tool sits on
   the WebView vendor's crates). The only declarative-UI *language* in Rust
   is Slint's `.slint` DSL: GPL/commercial tri-license, not shareable.
3. **The structural blocker is semantics, not widgets.** Five incompatible
   answers to signal/slot (immediate egui, Elm iced, fine-grained floem/
   gpui, dataflow xilem, DSL Slint) ⇒ any L2 control layer written today is
   a rewrite when the semantics question resolves. Only Slint ships SemVer;
   GPUI's tags literally follow Zed's version numbers; egui/iced/xilem break
   majors freely. Qt's moat was ABI stability **plus** a language boundary
   (QML): no pure-Rust project has either.
4. **AccessKit is the keystone and runs on one person's spare time**
   (42/58 commits since Mar 2026; no web adapter; iced absent; Zed ships a11y
   disabled). Nobody will fund it.
5. **Theming is the widest Rust hole.** egui `Visuals` = ~60 flat colors, no
   token layer; ratatui `Style` is flat, no theme abstraction; iced derived
   Oklch palettes in-tree and never extracted them. 30+ dead `*-theme`
   crates on crates.io (20–230 dl each): the concept rebuilt 30×, none
   converge. **No Rust DTCG implementation exists** (spec stable CR
   2025-10-28; the two ports are 0★). No crate *fails a build* on a WCAG
   contrast violation. APCA: `apca-w3` port at 396 dl; `perceive-color`
   (29K dl) is a five-day-old single-maintainer repo: and the APCA name
   carries brand/trademark constraints (Limited W3 License). Port the math;
   never brand a crate "APCA".
6. **The TUI seams are the estate's own duplication.** ratatui 0.30 split
   (`ratatui-core` 0.1.2 for widget authors) but `WidgetRef` still unstable
   (no stable composition layer), 13 widgets, no theme abstraction; upstream
   *reserved* `ratatui-keymap`/`-hotkeys`/`-picker` at 0.0.0 and shipped
   nothing; style/color are unassertable in tests (ratatui#1402). Meanwhile
   kestrel-tui, suture-tui and aileron each hand-roll keymaps, help panels,
   command palettes and palettes.
7. **The docs side already has its alternative: Tachyon (16 Rust crates).**
   The ecosystem gap is not an SSG (mdbook/Zola/Zensical/Pagefind all
   exist); it is that **Leptos/Dioxus islands are Rust/WASM-only**: no
   astro-island-compatible protocol exists to hydrate the estate's SolidJS
   islands from a Rust shell. That shim is the strategic seam.

## Decision

**Do not build a toolkit. Build the semantics layer.** The "Qt-alternative"
is scoped to **L1 substrate + L2 domain, ~10 crates, four L3 toolkits
unchanged**: not widgets+rendering+DSL+designer (that is a multi-year
moonshot competing with Slint's DSL and COSMIC's shipped proof).

1. **Adopt the bricks (L0, external, pinned, never forked):** wgpu, winit,
   parley/fontique, harfrust, skrifa/swash, icu4x, taffy, accesskit, arboard,
   rfd. Our font stack (`font-parse/model/shape` + `font-compose` per
   ADR-0003) is the one L0 we own, and it is the opinion everyone else
   converges on.
2. **Own the semantics (L1, cross-stack):**
   - **`color-kit`** (L0): Oklab/OkLCH, WCAG 2.1 AA contrast, APCA-Lc
     lightness, Brettel/Viénot CVD simulation, gamut mapping: a Rust port of
     shroom-theme's `color-science.js` + `wcag-contrast.js`.
   - **`theme-kit`** (L1): the typed token contract (role → semantic →
     component → state), DTCG 2025.10 in/out, variant derivation (the shroom
     7), the **contrast gate** (build fails on an AA violation), data-only
     emitters (CSS vars, DTCG JSON, VS Code/TextMate, ANSI-16). Spec:
     [specs/theme-kit.md](../../specs/theme-kit.md).
   - **`a11y-kit`** (L1): AccessKit wrapper: semantic node model, role/
     state/relation recipes, kittest-style tree gate. Wave 2, now first-class.
   - **`input-kit`** (L1): typed action/keymap/gesture resolution shared by
     TUI *and* GUI (the one place command-palette/keymap/help logic lives).
3. **Own the domain controls as traits (L2), four L3 impls:** egui
   (`chisel-doc`), Slint (`kestrel`), Leptos-WASM (`aileron`,
   `hosting-dashboard`), ratatui (TUIs). Rule: **no L1/L2 crate names a
   toolkit**; L2 defines `RenderAdapter`/`TextSink`/`A11ySink`/`ShellAdapter`
   traits, L3 supplies impls. Adapters are one-file crates whose property
   test is *same role → same RGBA across all four*.
4. **The TUI kit is consolidation, not invention:** `tui-actions`,
   `tui-search` (FuzzyList widget over `nucleo-matcher`), `tui-harness`
   (snapshot with **style/color** assertions: closing ratatui#1402 for us),
   adopting `ratatui-core` + `tui-input`/`edtui` + first-party `tui-*` 0.7.x.
   Dogfood: kestrel-tui, suture-tui, aileron.
5. **The Astro/Starlight alternative is consolidation too:** one docs core
   (Tachyon + `docs-pipeline` + `pediment` tokens + the 8 `starlight-*`
   plugins converge behind it); islands via an **astro-island-compatible
   custom element + 1–2 KB JS shim** so the SolidJS stack survives; adopt
   Pagefind (search), `latex2mathml` (math), D2 (diagrams). Build **no**
   search indexer, KaTeX port, or Mermaid port.
6. **Explicitly out of scope:** native print dialog (shell to OS viewer),
   QML-style DSL, designer tooling, 3D, a11y web adapter, GTK as a
   dependency.

## Consequences

- New crates (names verified unclaimed on crates.io, 2026-10-18):
  `color-kit` (L0), `theme-kit` (L1), `a11y-kit` (L1), `input-kit` (L1),
  `tui-actions`/`tui-search`/`tui-harness` (L2), docs-core (L2), plus the
  island shim (JS). `color-core` and `tui-kit` are taken on crates.io:   avoided.
- **First dogfood wins visible immediately:** `theme-kit`'s CSS/DTCG/VS Code
  emitters replace shroom-theme's JS pipeline (same 1049 tokens, one
  implementation, Rust-gated) and let `hosting-dashboard` drop its
  *vendored* `tokens.css` in favour of `@pediment/tokens` once pediment
  publishes: the emitter closes that loop.
- **Licensing/brand:** port APCA math under a neutral name; never ship the
  term "APCA" in crate names, docs, or marketing. Tiny-skia/vello/tao/muda
  stay externals.
- The honesty of the horizon: L1+L2 ≈ 10 crates buys Qt-class *coherence*
  across four stacks; a *toolkit* with a DSL and stable APIs remains the
  multi-year moonshot this ADR deliberately does not promise.
