# theme-kit — the typed token contract (SPEC, implemented M1)

> **Status: IMPLEMENTED + PUBLISHED (M1, 2026-10-18).** `theme-kit` 0.1.0 is
> live on crates.io (`github.com/WyattAu/theme-kit`) — 16 tests + doctest,
> clippy `-D warnings` clean, estate dep `color-kit` (L0) only. Dogfooded by
> `theme-egui` 0.1.0 (published), whose per-field byte-identity test is
> THM-008's contract. Deviations from this spec, recorded: TOML sources are not yet
> accepted (DTCG JSON only — the native interchange); `resolve()` returns
> `Option` rather than panicking on an unset role; the VS Code emitter
> carries the load-bearing chrome slots, not the full 1049-slot mapping
> (emitter work, not crate work). The gate rejected its own first test
> fixture (border `#6e7681` at 2.31:1 under the 3:1 graphic edge) — the
> fixture was corrected, not the gate.
> `REQ-THM-NNN` tags are the traceability anchors the implementation must cite.

**Layer:** L1 — substrate · **REQs:** 9 (THM-001…009) · **Deps:** `color-kit` (L0), `serde`, `toml` · **no_std:** leaning (core data model), std for emitters · **Date:** 2026-10-18

| Field | Value |
|---|---|
| Layer | **L1 — substrate.** The only cross-L2 coupling in the UI family: if the PDF editor, the mail client, the browser overlay, and the TUIs resolve the same `Role::Surface` to the same RGBA, the design system is real regardless of renderer (ADR-0004 §2). |
| Manifest declaration | `[package.metadata.layers] tier = "L1"` at repo creation |
| Estate deps | `color-kit` (L0) only. L0 zero-dep mandate holds for color-kit; theme-kit's ceiling is L1 ≥ L0. |
| External deps | `serde` + `toml` (DTCG source), nothing else. **No toolkit dependency in the core** — toolkit adapters (egui/ratatui/Slint/Leptos) are separate one-file L2 crates, not features. |
| Donor | `shroom-theme` (TS/JS: color-science.js, wcag-contrast.js, 1049 tokens, 7 variants, 9 exporters) and `pediment` (TS: token schema in production across Astro+Solid+Starlight sites). Both stay in TS as *consumers* of the Rust core, not owners of the science. |
| Name | `theme-kit` — verified unclaimed (crates.io API 404, 2026-10-18) |

## §Semantics

theme-kit is a **token graph + gate + emitters**. The graph is a fixed
semantic vocabulary (role → semantic → component → state); the gate is the
accessibility contract; the emitters are data-only transforms. No CSS
runtime, no widget, no renderer — the layers below and above must stay
possible without it.

### One graph, four lowerings

```
role (fg, bg, surface, accent, warn, error, muted, selection, border…)
  → semantic pair (on_surface / surface, …)   ← the contrast-gated edge
  → component tokens (button.primary.bg, …)
  → state overlays (hover/focus/active/disabled — alpha composited, never a new authored colour)
```

Authored colours exist only at the role layer. Everything else is derived
(references, modes, composition) so the same palette cannot drift between a
web page and a TUI cell.

### The contrast gate is the point

Every semantic pair is **WCAG 2.1 AA checked at build time** (THM-003), and
component ranks are **lightness-ordered via the APCA-Lc computation in
`color-kit`** (THM-004). A theme that fails does not ship a warning — the
build fails and prints the offending pair. No Rust theme crate does this
today (measured Oct 2026: ~30 dead `*-theme` crates, zero gates, no DTCG
implementation at all).

### Variants are derived, never hand-authored

The seven shroom variants (dark, light, high-contrast, monochrome, and the
three dichromat adaptations) are *derivation modes* over one seed palette
(THM-005/006): lightness targeting for light/dark, contrast maximisation for
high-contrast, channel projection for monochrome, Brettel/Viénot simulation
for CVD — each derived variant **asserts rank preservation under simulation**
(the property shroom-theme discovered the hard way: contrast against a
background and CVD separation are different properties).

### Data-only emitters

The core emits: DTCG 2025.10 JSON (round-trippable), CSS custom properties,
VS Code/TextMate themes, and ANSI-16/256 palettes. Toolkit lowering is
adapter crates (THM-008) whose property test is *identical resolved RGBA per
role across every adapter* — the test that makes four stacks one design
system.

## §API sketch

```rust
// features: default = std (emitters) · core data model is no_std-capable

/// REQ-THM-001/002: the fixed role vocabulary. Authored colours enter here.
pub enum Role { Surface, SurfaceRaised, OnSurface, OnSurfaceMuted, Accent,
               OnAccent, Warn, Error, Success, Selection, Border, FocusRing, … }

/// REQ-THM-001: DTCG 2025.10 in and out (groups, aliases `$ref`, modes).
pub struct TokenGraph { /* resolved: Role → Palette; modes: light/dark/… */ }

impl TokenGraph {
    pub fn from_dtcg_json(src: &str) -> Result<Self, ThemeError>;
    pub fn to_dtcg_json(&self) -> String;
    pub fn resolve(&self, role: Role) -> color_kit::Rgba;   // deterministic (THM-009)
}

/// REQ-THM-005/006: derive a variant from this graph's seed palette.
pub enum Variant { Light, Dark, HighContrast, Monochrome, Cvd(CvdKind) }
pub fn derive(&self, variant: Variant) -> Result<TokenGraph, ThemeError>;

/// REQ-THM-003/004: the gate. Every pair and rank checked; failure names
/// the offending pair and the measured numbers — no silent passes.
pub fn audit(&self) -> Result<Audit, ThemeError>;

/// REQ-THM-007: data-only emitters (trait for custom targets).
pub trait Emitter { fn emit(&self, g: &TokenGraph) -> Result<String, ThemeError>; }
pub struct CssVars;  pub struct DtcgJson;  pub struct VsCodeTheme;
pub struct Ansi16;   /* + 256-colour quantisation via color-kit */
```

`color_kit` (L0, specced next) owns: Oklab/OkLCH, WCAG 2.1 AA ratio,
APCA-Lc (neutral name — brand constraints), Brettel/Viénot CVD simulation,
gamut mapping. theme-kit owns nothing numeric.

## §Requirements

| REQ | Statement | Test |
|---|---|---|
| THM-001 | DTCG 2025.10 parse/resolve/serialize round-trips byte-stably (aliases, groups, modes) | property round-trip; golden fixtures from the pediment token set |
| THM-002 | Roles are a closed enum; unknown authored keys are a typed error (no ad-hoc colours past the role layer) | property: generated token sets only resolve via roles |
| THM-003 | Every semantic pair meets WCAG 2.1 AA; failure = build error naming pair + measured ratio | negative fixture (the shroom high-contrast case) + gate test |
| THM-004 | Component lightness ranks are APCA-Lc ordered (warn/err/surface separation ≥ declared deltas) | rank assertions per component over all variants |
| THM-005 | CVD variants preserve semantic rank under Brettel/Viénot simulation — the dichromat collision check | simulation over all pairs; the deuteranopia case is the fixture |
| THM-006 | Light/dark derive from one seed via lightness targeting; high-contrast maximises AA; monochrome projects channels | derivation determinism (same seed → same bytes, THM-009) |
| THM-007 | Emitters produce DTCG JSON, CSS vars, VS Code/TextMate, ANSI-16/256 from one graph; custom emitters via trait | golden outputs; a VS Code theme round-trips through the emitter |
| THM-008 | Adapter crates (egui `Visuals`, ratatui `Style`, Leptos/CSS vars, Slint) resolve identical RGBA per role | cross-adapter property test in the dogfood repo |
| THM-009 | Deterministic serialization (stable ordering, fixed float formatting) — the attestation surface | sha256-stability across runs and feature combinations |

## §Cross-references

- [specs/color-kit.md](color-kit.md) — L0 numeric core (next spec; THM depends on it entirely).
- [specs/font-compose.md](font-compose.md), `font-shape` — the other estate-owned L0/L2 the UI stack sits on.
- `shroom-theme` (TS) — the donor of the colour science and the 7-variant shape; becomes a consumer (its JS pipeline retires into emitters).
- `pediment` (TS) — token schema in production; `hosting-dashboard` currently *vendors* its `tokens.css`; THM-007 closes that loop.
- ADR-0004 §2 — why this is L1 and why adapters are L2.
- Wave 2 `a11y-kit` — consumes `audit()`; the a11y tree gate and the token gate are one CI story.
- Dogfood (est): `chisel-doc` egui themes · kestrel + aileron + suture-tui palettes · leptos-* CSS vars · `hosting-dashboard`/starlight sites · Tachyon.
