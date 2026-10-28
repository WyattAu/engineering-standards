# Headless UI testing: how GPUI tests a window system without windows, and where the estate already qualifies

Date: 2026-10-28. Source: zed's `crates/gpui` read at clone HEAD
(`/home/wyatt/dev/reference/zed`), plus an empirical run of the estate's
three UI crates with the display environment stripped. This closes the
"headless test platforms" item the GUI study (docs/research/44-gui)
recommended; the recommendation turns out to be already satisfied by
construction, and the interesting part is zed's mechanism for the day the
estate needs draw assertions.

## GPUI's mechanism, read at the source

GPUI embeds the window system inside the widget tree, so it cannot simply
avoid a platform: instead it makes the platform an injectable fake.

1. **A complete in-memory platform.** `TestPlatform` implements the full
   `Platform` trait -- dispatcher, display geometry, window construction,
   even a screen-capture source (`platform/test/{platform,window,
   display,dispatcher}.rs`). Application code cannot tell it from the real
   one, because it enters through the same trait.
2. **A mode, gated out of production.** `GpuiMode::Test { skip_drawing }`
   is compiled under `#[cfg(any(test, feature = "test-support"))]`; the
   `test-support` feature carries the fakes so release builds never do.
3. **Simulated input as first-class API.** `TestContext` (1,548 lines)
   synthesizes keystrokes, mouse events, and menu interactions, then
   flushes effects deterministically -- tests assert on state after an
   explicitly driven event loop, never on wall-clock timing.
4. **Draw-data assertions instead of screenshots.** `VisualTestContext`
   (485 lines) records the primitives a frame would paint and lets tests
   assert on that record. No pixels, no compositing, no display. This is
   the design that makes "the button rendered in the right place" a
   deterministic `assert_eq!`.

## The estate's measured position

All three UI-family crates ran their full suites with `DISPLAY` and
`WAYLAND_DISPLAY` stripped:

| crate | tests display-less | window-system deps |
|---|---|---|
| ui-text-edit | 44 passed, 0 failed | none (`input-kit` + optional `a11y-kit`) |
| theme-kit | 16 passed, 0 failed | none (`color-kit`, serde) |
| theme-egui | 7 passed, 0 failed | `egui >=0.36, <0.38` with `default-features = false` |

The headline: **the estate's UI layer is already headless by
construction**, which is what ADR-0004's layer rule was for. The
toolkit-shaped dependency exists only in the adapter crate
(`theme-egui`), and even there `default-features = false` keeps the
windowing backends out of the graph. CI runners have no display anyway,
so every green run in this estate's history has been a headless run.

The GUI study's recommendation #2 ("ui-text-edit and theme-kit should be
testable without a window server") is therefore already true; the study's
real contribution was the second half of its own sentence: deterministic
draw-data assertions instead of screenshot diffs.

## What to adopt, and when

Nothing for the existing crates. Two rules for the future:

1. **Any estate crate that embeds a real toolkit keeps it behind an
   adapter crate**, as theme-egui does for egui and ADR-0004's
   "no L1/L2 crate names a toolkit" clause already requires. The adapter
   is the narrow, deliberate exception.
2. **If a future adapter needs draw assertions, the GPUI
   VisualTestContext is the template**: record the primitives the frame
   would paint, assert on the record. What is explicitly not adopted is
   screenshot testing (neovide's approach): it requires a display or an
   expensive virtual one, and its diffs break on font rasterization
   changes that are not regressions.

## Follow-up

The GPUI examples under `crates/gpui/examples/testing.rs` and
`example_tests.rs` are the shortest end-to-end demonstrations of the
harness; consult them when the first draw-asserting adapter test is
actually written, rather than translating from this summary.
