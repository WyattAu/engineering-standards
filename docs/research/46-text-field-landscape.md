# Research note 46: The text-field landscape: is ADR-0006 already built?
**cosmic-text `Editor`**; the closest to reusable, and the core we
**slint `TextInput`**; the most complete single-file field: 2,531 lines
**zed `InputHandler`**; not an editor; the *adapter trait*: an
text_for_range, replace_text_in_range, set_marked_text; all UTF-16) that
**iced `text_editor`**; multi-line editor with Content/Action/Motion/
**gpui-component (longbridge) 0.8**; 60+ desktop components on GPUI
**helix-core**; the best editing-semantics engine in Rust (transactions,
multi-cursor selection model, rope via ropey); **unpublished** (0.0.0
**ropey 1.6** / lapce-xi-rope; the buffer data structures. cosmic-text's
   free; the hard 80%).
4. Validation hooks (a `sanitizer`/`validator` callback layer); absent
5. AccessKit text-field wiring; absent everywhere.
Build, on cosmic-text; validated by survey rather than assumption. The