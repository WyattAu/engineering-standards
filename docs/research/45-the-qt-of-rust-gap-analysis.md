1. **Widgets**; desktop-grade controls: model/view item views, docking,
2. **Graphics**; scene graph, raster fallback, RHI over GL/Vulkan/Metal.
3. **Text**; best-in-class shaping/bidi/IME; QTextDocument rich editing.
4. **Platform integration**; native menus, tray, dialogs, notifications,
5. **Tooling & stability**; Designer, Linguist/i18n, the moc, decades of
**Graphics; effectively solved (90%).** wgpu is the standard RHI; vello
**Text shaping/layout; solved (85%); text editing; the sharpest gap
shaping, bidi, and fallback. But *editing*; selection, IME composition,
undo, validation, accessibility for a text field; is hand-rolled by
**Widgets; 40%.** iced/slint/egui cover buttons/lists/layouts at roughly
**Platform integration; 80% of the common cases.** winit + muda +
**Tooling & stability; 15%.** No visual designer (slint's preview is the
closest). fluent exists for i18n but is unintegrated. No ABI/LTS story -
integration hub) exceeds every toolkit project studied; that is the moat
our own apps need. That; not rebuilding Qt alone; is the estate's play.
   pattern), AccessKit-wired; the ecosystem-gap crate.