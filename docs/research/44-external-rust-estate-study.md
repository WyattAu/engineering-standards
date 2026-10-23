# External Rust estate study: what flagship Rust projects standardize, and where the estate stands

Date: 2026-10-23. Method: shallow clones (`--depth 1`) of 12 flagship Rust
repositories into `/home/wyatt/dev/reference/`, measured by a metrics script
(manifests, workspace tables, lockfiles, workflows) plus manual reading of the
workspace roots, CI, and crate layout. All numbers below are from the cloned
HEAD on that date; the repos move daily, so treat figures as scale markers,
not exact contracts.

Requested but not found: "glowwave synth" does not exist on GitHub as a Rust
synthesizer. The only repositories matching the name are unrelated (a 0-star
TypeScript app, media and detailing sites). The nearest real Rust projects of
that genre, for a future round: `sinshu/rustysynth` (SoundFont MIDI
synthesizer, pure Rust, zero deps) and `chris-zen/kiro-synth` (modular
synth). Neither was substituted for the requested name; a study must not
quietly study something else.

## The corpus

| repo | rs LOC | manifests | workspace dep entries | lockfile pkgs | why it is here |
|---|---|---|---|---|---|
| [zed](https://github.com/zed-industries/zed) | 1,799,554 | 268 | 541 | 1801 | largest Rust app monorepo; GPUI |
| [rerun](https://github.com/rerun-io/rerun) | 761,985 | 162 | 353 | 1316 | multimodal data SDK, strict versioning |
| [slint](https://github.com/slint-ui/slint) | 396,719 | 110 | 73 | 991 | declarative UI toolkit + compiler |
| [Fyrox](https://github.com/FyroxEngine/Fyrox) | 288,826 | 25 | 0 | (no lock) | game engine, editor split |
| [vizia](https://github.com/vizia/vizia) | 180,282 | 13 | 48 | (no lock) | retained-mode GUI toolkit |
| [lapce](https://github.com/lapce/lapce) | 68,576 | 5 | 49 | 757 | editor; Floem UI framework |
| [libcosmic](https://github.com/pop-os/libcosmic) | 60,986 | 20 | 9 | (no lock) | COSMIC's app toolkit (iced fork) |
| [rnote](https://github.com/flxzt/rnote) | 54,647 | 5 | 66 | 571 | sketch app; engine/app split |
| [nih-plug](https://github.com/robbert-vdh/nih-plug) | 43,757 | 29 | 0 | 721 | VST/CLAP plugin framework |
| [neovide](https://github.com/neovide/neovide) | 37,497 | 2 | 0 | 436 | Neovim GUI |
| [cosmic-files](https://github.com/pop-os/cosmic-files) | 27,652 | 3 | 2 | 914 | COSMIC file manager (app reference) |
| [cosmic-edit](https://github.com/pop-os/cosmic-edit) | 6,706 | 1 | 0 | 906 | COSMIC editor (minimal app reference) |

## Finding 1: version centralization is what every large workspace does, and the estate's multi-crate repos do not

Every workspace at scale keeps one `[workspace.dependencies]` table and has
internal crates consume it with `dependency = { workspace = true }`:
zed 541 entries with 248 of 251 member crates consuming, rerun 353 entries
with 150 consumers, slint 73, rnote 66, lapce 49, vizia 48. The two
counter-examples prove the rule: nih-plug (0 entries; its 29 manifests are
mostly per-example plugin crates) and cosmic-edit (a single crate) are not
workspaces that share versions, because they have nothing to share.

The estate's multi-crate repos (trendkit, healthkit, hw-kit, fetch-kit,
signalkit) have zero `workspace = true` occurrences: each member crate pins
its own versions, so the same external crate can drift between siblings
inside one repo. This is the single highest-value adoption in this study.
The kit template should gain a `[workspace.dependencies]` stanza, and
multi-crate repos should migrate member crates to `workspace = true` for
external deps. Exact pins (`=x.y.z`) stay for estate-internal cross-repos;
centralization governs third-party versions inside a repo.

## Finding 2: `workspace.package` inheritance is the companion practice

rerun inherits `version` from the workspace root in 131 of 162 crates; slint
in 51 of 110; lapce, vizia, and rnote inherit consistently. zed is the
notable exception (literal versions everywhere, but centralized deps). Inheritance
removes the "bump four crates, forget the fifth" class of release error. The
kit template should inherit `edition`, `rust-version`, `license`, and
`repository` from `[workspace.package]`; per-crate `version` stays literal
in the estate, because estate crates release independently on purpose.

## Finding 3: MSRV and edition

Declared `rust-version`: nih-plug 1.80, vizia 1.85, rnote 1.89, cosmic
1.93, slint 1.95, lapce 1.98, rerun 1.98. zed, the largest, declares none.
Edition 2024 is the norm (11 of 12; nih-plug still 2021). The estate already
declares `rust-version` in kit crates and commits `Cargo.lock` everywhere,
which matches the app repos here (apps commit locks; pure library workspaces
Fyrox, vizia, libcosmic do not). No change needed; this is confirmation.

## Finding 4: the estate's gate battery leads the field

None of the 12 reference repos runs `cargo-semver-checks`, `cargo-deny`, or
`cargo-vet` in the workflows on their default branch. The strongest CI seen:
slint (MSRV job, miri, clippy `-D warnings`), zed (miri, nextest, scorecard),
rerun (cargo-hack across features, 50 workflows), neovide (nextest). The
estate runs semver-checks, vet, clippy deny-warnings, a feature matrix, the
estate audit, pin consistency, llms.txt links, and doc-style, advisory or
blocking per LOOP doctrine. Conclusion: keep investing in gates; this is
where the estate is ahead of projects with 10x the headcount, and the gates
are cheap relative to the rebrand-sized migrations they prevent.

## Finding 5: duplicate major versions are endemic; the estate's single-major rule is stricter than the field

Duplicate majors of watchlist crates in committed lockfiles: zed carries
hashbrown x5, rand x5, windows x5, syn x3; rerun hashbrown x5, rand x3;
cosmic-files hashbrown x4; slint hashbrown x4, syn x3. The estate
experienced this concretely with rusqlite (0.32 vs 0.40 cannot coexist in
one graph because of the native link) and now forbids accidental duplicate
majors via the audit plus the sqlite-side split. The reference field shows
that without an explicit rule, duplicates accumulate even in the most
careful codebases. Keep the rule; consider extending the audit from
link-bearing crates to the whole watchlist.

## Finding 6: the testing arsenals worth borrowing

thiserror + anyhow is universal. Beyond that: loom (zed, rerun, cosmic),
miri in CI (zed, slint), proptest (zed), insta snapshots (rerun), criterion
benches (lapce, rerun, zed), arbitrary (slint, rnote, nih-plug). The estate's
suites already run miri and loom on tier-A crates via rust-kit; the gaps are
snapshot testing (insta, a fit for docs-core and theme renderers where the
current style is hand-written expected strings) and property testing
(proptest, a fit for the parsers: sheet-xlsx, a2l-parse, dbc-parse). Advisory;
adopt where a concrete flake or coverage gap appears, not as a blanket rule.

## Finding 7: COSMIC is the counter-model to the estate's composition doctrine

libcosmic is a 61k-LOC fork-and-specialize of iced, maintained permanently by
the COSMIC team, with apps (cosmic-files, cosmic-edit) building exclusively on
the fork. The estate's doctrine (ADR-0005: duplication is a forcing-function
problem; extract and share instead) produces small crates with many exact-pin
consumers. COSMIC shows the fork model's real cost profile: total control of
the toolkit, paid for with a permanent internal maintenance burden and a
wrapper API that exists nowhere upstream. Verdict: keep extract-and-share for
estate-owned code; fork only for vendored third-party foundations where
upstream's release cadence is the blocker, and record every such fork in the
registry (the pdfcraft precedent).

## What to adopt (advisory, in order)

1. `[workspace.dependencies]` in the kit template, and a migration of the
   five multi-crate estate repos onto it (Finding 1).
2. `[workspace.package]` inheritance for edition, rust-version, license,
   repository in the same repos (Finding 2).
3. Audit extension: duplicate-major check across the dependency watchlist,
   not only native-link crates (Finding 5).
4. insta and proptest into the rust-kit arsenal, where a concrete case fits
   (Finding 6).

## What to reject

Flat 250-crate namespaces without tiering (zed's crates/ directory is
alphabetical anarchy that only works with 100+ engineers and a search index;
the estate's L1-L3 layers exist precisely to avoid this). Per-example crates
as versioned members (nih-plug). No-lockfile libraries inside the estate's
composition repos (Fyrox, vizia, libcosmic do this; the estate's apps and
suites need `--locked` reproducibility).
