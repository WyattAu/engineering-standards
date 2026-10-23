# Research note 44: GUI & graphics implementation study

**Sources.** The twelve reference projects of research note 43, this time
read for *implementation*: rendering model, GPU API, text stack, input
model, and the patterns our UI layer (theme-kit, theme-egui, ui-text-edit,
a11y-kit, color-kit) should adopt. File-level reading of zed's GPUI,
slint's compiler/renderers, rerun's re_renderer, vizia's core, cosmic-files'
app, neovide's renderer, nih-plug's GUI adapters.

## The rendering-model taxonomy

**Hybrid immediate/retained, GPU (zed/GPUI).** "Hybrid immediate and
retained mode, GPU accelerated": Metal on macOS, pluggable Linux backends
(wayland/x11) behind a `gpui_platform` feature crate. Applications build
element trees (Div is the HTML-div analog; the element vocabulary is
deliberately small: div, list, uniform_list, canvas, svg, img, text,
animation, deferred, container_query) that are re-evaluated each frame
against retained per-entity state. Two estate-grade patterns live here:
GPUI ships a **headless test platform** (`platform/test`: deterministic
UI tests without a window server), and accessibility is a core module with
its own source file, not an afterthought.

**Compiled declarative DSL, pluggable renderers (slint).** The `.slint`
DSL is compiled by `internal/compiler` into Rust code against a runtime
core (properties, item tree, layout); renderers are swappable crates
(skia, femtovg, software) behind one trait. Text: parley + swash. The
separation means the same UI runs on GPU and embedded software targets.

**Elm/TEA at scale (cosmic-files, sniffnet, the COSMIC stack).** libcosmic
over iced: `fn view(&self) -> Element<Message>` with update/Message:cosmic-files' main app is 6,465 lines in one file and still works, which
is evidence the model scales past where people assume it breaks. Text:
cosmic-text. The COSMIC project maintains cosmic-text itself: it is the
emerging standard for shaping in Rust.

**Immediate mode + data renderer (rerun).** egui for chrome, and a
separate wgpu renderer (`re_renderer`) with a `ViewBuilder` draw-recording
API for the data views. The split: UI framework for panels, custom
renderer for the data: is the pattern for any estate tool that
visualizes heavy content.

**Grid renderer (neovide).** Skia (skia-safe with embedded freetype and
textlayout) drawing a character grid with an animation system
(animation_utils, cursor_renderer) layered on top: proof that
GPU-accelerated text + a separate animation layer composes cleanly.

**Retained widget trees (vizia, fyrox).** vizia: entity tree with
first-class modules for accessibility, animation, events, and binding.
fyrox: a full engine with its own retained UI and GL renderer.

**GUI-adapter pattern (nih-plug).** `nih_plug_vizia`, `nih_plug_iced`:the plugin exposes a parameter model; the GUI framework is a swappable
adapter over it. The plugin never knows which UI renders it.

**Document/canvas (rnote).** GTK4 + cairo: vector ink stored as objects,
rendered to cairo surfaces: the retained document model, opposite end
from immediate mode.

## The text-stack survey (most estate-relevant)

| stack | who | note |
|---|---|---|
| cosmic-text | zed, cosmic-files/COSMIC | shaping + layout + bidi; maintained by System76's ecosystem |
| parley + swash | slint | the Druid-lineage text engine |
| swash | zed, neovide, slint | glyph rasterization over harfbuzz-shaped output |
| skia textlayout | neovide | embedded freetype via skia-safe |
| cairo/pango | rnote | the GTK stack does text |
| font-kit | zed | system font enumeration |

cosmic-text appears in the most projects and is actively maintained by an
ecosystem, not a lone author.

## What the estate's UI layer should adopt

1. **cosmic-text under the text-field layer** (ADR-0006). Shaping, bidi,
   and font fallback are solved there and maintained by an ecosystem. Our
   layer should own the *field semantics* (selection, IME composition,
   validation) and delegate shaping/layout.
2. **Headless test platforms for UI crates** (GPUI's `platform/test`).
   ui-text-edit and theme-kit should be testable without a window server:   deterministic draw-data assertions instead of screenshot diffs. This is
   the difference between a UI crate with CI and one with screenshots.
3. **The GUI-adapter trait** (nih-plug). theme-kit should define the
   theme/parameter model as a trait with egui as the first adapter
   (theme-egui), leaving room for a future iced or raw-wgpu adapter
   without breaking consumers.
4. **Accessibility as a core module** (GPUI, vizia): a11y-kit should
   integrate at the element level, not as a post-hoc tree audit.
5. **Animation as a separate module** (vizia, neovide): curves/easing
   decoupled from renderers, so the same animation data drives egui now
   and any later backend.

## Confirmed: where we are ahead

cargo-deny/audit/vet gates, semver-checks, provenance work, per-repo
fuzz-smoke, the layer model, and the integration hub: none of the twelve
do these. The gap is in *UI implementation depth*, which is exactly where
the estate is youngest; these twelve are the syllabus.
