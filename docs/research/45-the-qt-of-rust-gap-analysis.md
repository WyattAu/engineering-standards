# Research note 45: How far is Rust from "the Qt of Rust"?

**Sources.** Research note 44's twelve-project implementation study; the
wider toolkit landscape as of October 2026 (iced, egui, slint, Dioxus,
Xilem/linebender, GPUI, Makepad, gtk-rs, AccessKit, cosmic-text, parley,
vello); Qt's own feature surface as the measuring stick.

## Defining the target: Qt's five pillars

1. **Widgets** — desktop-grade controls: model/view item views, docking,
   MDI, print support, rich text *editing*.
2. **Graphics** — scene graph, raster fallback, RHI over GL/Vulkan/Metal.
3. **Text** — best-in-class shaping/bidi/IME; QTextDocument rich editing.
4. **Platform integration** — native menus, tray, dialogs, notifications,
   OS conventions on Windows/macOS/Linux/embedded.
5. **Tooling & stability** — Designer, Linguist/i18n, the moc, decades of
   API/ABI stability, LTS.

## Where the ecosystem stands, pillar by pillar

**Graphics — effectively solved (90%).** wgpu is the standard RHI; vello
is the GPU-2D future; skia-safe is the pragmatic present. Nobody needs to
write a renderer from scratch (fyrox and GPUI did, by choice).

**Text shaping/layout — solved (85%); text editing — the sharpest gap
(30%).** cosmic-text (COSMIC/zed-lineage) and parley (linebender) solve
shaping, bidi, and fallback. But *editing* — selection, IME composition,
undo, validation, accessibility for a text field — is hand-rolled by
every project in existence. Even zed built theirs from scratch. No shared
production text-field crate exists. **This is the single deepest gap in
the ecosystem.**

**Widgets — 40%.** iced/slint/egui cover buttons/lists/layouts at roughly
"early Qt" control depth. No Rust-native toolkit has Qt-Widgets-grade
model/view item views, docking, or print. gtk-rs is the escape hatch
(full GTK, but C-shaped, not Rust-idiomatic).

**Platform integration — 80% of the common cases.** winit + muda +
tray-icon + zbus cover windows/menus/tray/DBus; conventions and edge
cases (global shortcuts per-OS quirks, notifications) remain patchwork.

**Tooling & stability — 15%.** No visual designer (slint's preview is the
closest). fluent exists for i18n but is unintegrated. No ABI/LTS story —
Rust substitutes semver discipline, which no toolkit has achieved across
majors.

## Who is positioned to be "the Qt of Rust"

Nobody alone; the realistic outcome is a **federation**: a toolkit shell
(iced with System76 shipping it, or slint with its commercial dual-license
Qt-shaped business) over cosmic-text/parley + vello + AccessKit, with the
widget/editing layers contributed by parties like us. Qt took ~30 years;
the Rust toolkits are 5–8 in with visible convergence.

## The estate's position and play

Our governance stack (deny/audit/vet/semver/provenance, the audit, the
integration hub) exceeds every toolkit project studied — that is the moat
we bring to any collaboration. Our implementation hand is young but aims
at the sharpest gap: **ADR-0006's text-field layer is the missing shared
crate of the entire ecosystem.** Built framework-agnostic (cosmic-text
shaping, adapter-per-toolkit in the nih-plug pattern, a11y-kit wired at
the element level), it is a genuine ecosystem contribution AND the field
our own apps need. That — not rebuilding Qt alone — is the estate's play.

## Sequencing

1. ui-text-edit on cosmic-text, adapter-per-toolkit (the nih-plug
   pattern), AccessKit-wired — the ecosystem-gap crate.
2. theme-kit's trait model as the theming adapter standard.
3. Adopt the winners underneath (egui now; iced/slint for the app shells).
4. Renovate decision + nextest/insta adoptions from research note 43.
