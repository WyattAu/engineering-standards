# ADR-0006: the text layer is a text-field layer, not an editing engine

- **Status**: Accepted (2026-10-18)
- **Date**: 2026-10-18
- **Complements**: [ADR-0004](0004-gui-toolchain-semantics-layer-not-toolkit.md) (the semantics layer), [ADR-0005](0005-duplication-is-a-forcing-function-problem.md) (composition as the forcing function)
- **Supersedes**: nothing

## Context

ADR-0004 closed the text stack and left one item open: "No rich-text editing
widget, every editor builds its own." The obvious next move was a
`ui-text-edit` crate. Before writing one, the question that decides the whole
design was: **which problem, exactly?**

Three different products share the name "text editing" in the Rust ecosystem,
and they have different consumers, different licenses, and different
maintenance risk. Confusing them is how a project ends up maintaining a
sixth editing engine nobody asked for.

## The three products, distinguished

1. **A text field.** A name in a box, a mail body, a form value. One caret, one
   selection, no history.
2. **An editing engine.** Helix-class: transactions, a revision-tree history,
   multiple carets, marks, folds, syntax awareness.
3. **A code editor.** An engine plus syntax, LSP, folding, diagnostics, a
   project model.

**The estate needs product 1.** Measured against the four UI surfaces in
ADR-0004 §Context: `chisel-doc` is a PDF editor with a canvas and form panels;
`kestrel` is a mail client with a list and a reading pane; `aileron` is a
tiling web environment; `suture-tui` and `kestrel-tui` are TUIs. **None of them
is a code editor.** A Helix-class engine would have zero consumers on day one.

## The survey

Five candidates, verified against the crates.io API and their sources on
2026-10-18:

| Crate | Ver | Licence | Downloads | What it is | Buffer |
| --- | --- | --- | --- | --- | --- |
| `caretline` | 0.5.0 | MIT AND MPL-2.0 | 162 | Vendored Helix semantics, replayable Elm architecture | Owns a rope |
| `weavatrix-edit` | 0.1.7 | MIT | 1,189 | Edit-plan validation and application | None (`&str` + a set) |
| `rcmd-tui-edit` | 4.69.0 | MIT | 397 | Editor core with ropey, unlimited undo | Owns a rope |
| `ailloli_ui_editor` | 0.1.0-beta.2 | MIT OR Apache-2.0 | 133 | Multi-paragraph editor, tree-sitter | Via `ailloli_ui_text` |
| `text-editing` | 0.2.3 | MIT OR Apache-2.0 | 8,944 | Single line, no dependencies | None |

Four findings changed the decision.

### 1. `caretline` is an excellent specification and a poor dependency

It vendors the real Helix core: `Transaction`/`ChangeSet`/`Change`, a
revision-tree `History`, `Selection` as a set of ranges, `ChangeSet::map_pos`.
That is precisely the semantics an editing engine needs, and it is readable.

It is not a dependency to build on:

- **6 versions in 2 days** (0.1.0 to 0.5.0, 2026-10-07 to 2026-10-09). Five
  major-version moves in 48 hours.
- **162 total downloads, 0 GitHub stars, single author, no CHANGELOG, no
  declared MSRV.** The repository URL changed at 0.4.0.
- **MPL-2.0 entanglement**: `crates/caretline/src/helix/` is vendored Helix
  source. File-level weak copyleft, against a private snapshot with no
  documented upstream sync path.

### 2. `helix-core` is not installable from crates.io

The crate is packaged for publishing (`include = ["src/**/*", "README.md"]`)
but the names on crates.io are `0.0.0` placeholders from 2021-06-02, described
as "a placeholder for the future helix-editor crate". The only route is a git
dependency on an untagged commit, which is what `caretline` did by vendoring.

### 3. Zed is strictly less extractable

`crates/text`, `crates/rope`, and `crates/editor` all inherit
`publish = false` from the workspace root. None are on crates.io. All are
**GPL-3.0-or-later**, and `crates/editor` has a hard `gpui` dependency, so it
is an editor component rather than a headless core.

### 4. `ropey` is about to flip its index model

Ropey 1.6.1 is the last stable (2023-10-18); **2.0.0-beta.1** (2025-08-02) has
685,563 downloads. The 2.x CHANGELOG: "Indexing is now **byte based** rather
than char based", and "the char indexing metric is not enabled by default".

This is the finding that decided the architecture. A crate that exposed `Rope`
in its own types would break its API with that release. A crate that exposes a
**trait** does not.

### The gap, stated precisely

No crate provides selection/transaction/history over an abstract buffer trait
with grapheme coordinates and zero toolkit dependencies. The nearest is
`weavatrix-edit`, which is genuinely buffer-agnostic (2 runtime dependencies,
no rope) but whose own README rules out "mutable document sessions, revision
rebasing, undo, or CRDT state", and which pins to the LSP UTF-16 contract,
which is scalar-correct but can still split a grapheme cluster.

Separately, none of the five is grapheme-correct in its **coordinates**.
`rcmd-tui-edit` has grapheme-aware *motion* but its `Pos.col` is a character
column, so an API caller can still place a caret mid-cluster.
`ailloli_ui_editor` is byte-offset throughout. `text-editing` is char-indexed.

## Decision

1. **Build the text-field layer (product 1), not the engine (product 2).**
   `ui-text-edit` L2: `TextBuffer` trait, `StringBuffer`, `TextField` (one
   caret, one selection, form-field operations), `ComposingField` over
   `input-kit` L1, and an `a11y` feature bridging to `a11y-kit` L1.
   Deliberately absent: multiple carets, transactions, a revision tree, undo,
   folds.
2. **Put the buffer behind a trait because `ropey` 2.0 is coming.** This is the
   one architectural decision the survey forced, and it is also the cheapest
   insurance in the estate: a caller can swap the storage without a single
   caller-side change.
3. **Every offset is a grapheme cluster, inherited from `input-kit`.** Not a
   style choice. Five surveyed crates get the coordinates wrong; a caret that
   can split a flag is a bug users can see.
4. **Do not depend on `caretline`.** Read it as a specification if an engine is
   ever needed, and vendor it at a pinned commit at that time rather than
   taking a crates.io dependency on a crate with five majors in two days and no
   changelog. Revisit if a version with a changelog and a stable API exists.
5. **Ship only after a consumer composes it** (ADR-0005). The composing suite
   was written against a path pin before publication.

## Consequences

- `ui-text-edit` 0.1.0 is published and consumed. 39 tests plus 3 doctests with
  all features, clippy `-D warnings` clean.
- **The composing suite found a bug in the crate the day it was written.** The
  a11y bridge announced the entire field value. A unit test with five
  characters sees nothing wrong; a mail body would be read in full on every
  focus. Truncation is now capped at `MAX_ANNOUNCED_CHARS` and cut on a cluster
  boundary. This is the whole argument for ADR-0005 in one incident: the crate
  passed its own tests and was still wrong.
- **The `a11y-kit` `busy` gap closed in the same wave.** `States::busy` shipped
  in 0.2.0 after the `input_composition` suite proved it was missing, and
  `ui-text-edit`'s bridge is what drives it.
- **A text-field layer is not an engine.** If the estate ever needs
  transactions, undo, or multiple carets, that is a different crate with a
  different consumer, and ADR-0006's finding 4.4 points at how to build it:
  vendor Helix's model at a pinned commit, put the buffer abstraction over it,
  and do not ship a sixth engine next to five.
- The one semantic that is easy to get backwards, and is now documented and
  tested: **a commit replaces the preedit, it does not append to it.** The
  preedit is a display overlay that was never part of the value.