# Research note 46: The text-field landscape: is ADR-0006 already built?

**Sources.** Clones of pop-os/cosmic-text and pop-os/cosmic-edit; file-level
reads of slint's `internal/core/items/text.rs` (2,531 lines) and zed's
`InputHandler` trait; crates.io state for ropey, helix-core,
gpui-component, iced's `text_editor`. Commissioned before committing to
ADR-0006: if someone has already hand-rolled the field-semantics layer,
we learn and adopt instead of building.

## Who has built what

**cosmic-text `Editor`**; the closest to reusable, and the core we
already chose. Action surface: Motion, Escape, Insert, Enter, Backspace,
Delete, Indent/Unindent, Click/DoubleClick/TripleClick/Drag, Scroll.
Change tracking exists (`ChangeItem`/`Change`), and vi-mode drives
undo/redo through `cosmic_undo_2::Commands`. Gaps: **no public
undo/redo API** (the undo machinery is vi-mode-internal), **no IME
preedit modeling** (zero preedit/IME references in src/), **no
validation hooks**, **no accessibility**.

**slint `TextInput`**; the most complete single-file field: 2,531 lines
with preedit text + preedit selection properties, undo/redo stacks
(`UndoItem` with kinds), and the full standard-shortcut surface. The
capability checklist for any field implementation. Bound to slint only.

**zed `InputHandler`**; not an editor; the *adapter trait*: an
NSTextInputClient-shaped interface (selected_text_range, marked_text_range,
text_for_range, replace_text_in_range, set_marked_text; all UTF-16) that
the editor implements so the OS input methods can drive it. This is the
trait shape our per-toolkit adapters should mirror.

**iced `text_editor`**; multi-line editor with Content/Action/Motion/
Selection (the design mirrors cosmic-text's; libcosmic's iced fork shares
lineage), Parser-based syntax highlighting, Catalog theming. Bound to
iced. IME support is platform-level, partial.

**gpui-component (longbridge) 0.8**; 60+ desktop components on GPUI
including Input/TextArea. GPUI-bound.

**helix-core**; the best editing-semantics engine in Rust (transactions,
multi-cursor selection model, rope via ropey); **unpublished** (0.0.0
placeholder on crates.io), workspace-internal.

**ropey 1.6** / lapce-xi-rope; the buffer data structures. cosmic-text's
Buffer already wraps its own; we don't need a separate rope.

## The confirmed gap

Every implementation is toolkit-bound. The shared core (cosmic-text
Editor) lacks public undo/redo, IME composition, validation, and
accessibility. The semantic engines (helix) are unpublished. **Nothing
implements a toolkit-agnostic field-semantics layer.** ADR-0006's target
is vacant, and the survey says the build is "wrap and promote", not
"reinvent":

1. Wrap cosmic-text's `Editor` (shaping/layout/bidi/cursor/selection come
   free; the hard 80%).
2. Promote undo/redo to a public API on top of the existing
   `ChangeItem`/`Change` stream (the machinery is already in-tree).
3. Add IME preedit composition modeled on zed's `InputHandler` (the
   marked-text/composing-state design) and slint's preedit properties.
4. Validation hooks (a `sanitizer`/`validator` callback layer); absent
   everywhere; our differentiator for the estate's forms.
5. AccessKit text-field wiring; absent everywhere.

## Verdict

Build, on cosmic-text; validated by survey rather than assumption. The
landscape research also yields the checklist: slint's 2,531 lines
enumerate the field semantics; zed's `InputHandler` is the IME adapter
shape; cosmic_undo_2 is the undo pattern to promote.
