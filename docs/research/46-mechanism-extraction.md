# Mechanism extraction round: release machinery, pin discipline, MSRV in CI, vendoring anatomy

Date: 2026-10-23. This is the second pass over the corpus cloned for the
external estate study (docs/research/45): not metrics this time, but the
concrete mechanisms behind the numbers, read at the source, with what the
estate already extracted and what remains open. Repos live in
`/home/wyatt/dev/reference/`.

## 1. rerun's batch publisher is already estate tooling

rerun publishes its crate graph through a reusable workflow whose single
publish step is `python scripts/ci/crates.py publish --token ...`: a
topological publisher that walks the dependency graph, publishes in order,
and retries on registry-index propagation. The estate's `scripts/crates.py`
(landed 2026-10-23, round 22) is that mechanism, extracted and reworked for
the estate's exact-pin discipline, with a `--dry-run` the upstream tool
lacks. Verdict: extracted, nothing further to do. The reusable-workflow
wrapper around it is not worth adopting until the estate publishes more
often than it hand-verifies.

Correction to study 45's working notes: rerun does not practice
publish=false hygiene. 114 of its 120 crate manifests declare
`publish = true`; only 6 opt out. The estate publishes its leaf crates and
marks only true infrastructure (estate-site, `publish = false`) and forks
(`crates: []`) as unpublishable. The estate's registry-driven accounting is
more precise than upstream's convention, not less.

## 2. zed's pin-site comment discipline

zed's 541-entry `[workspace.dependencies]` is organized in three commented
sections (workspace member path deps, external crates, and a
`[patch.crates-io]` for forked foundations), and every non-obvious entry
carries its reason at the pin site:

- a `WARNING: if you change this, you must also publish a new version of
  zed-reqwest` on the pinned fork of reqwest, tying the pin to its publish
  obligation;
- a default-features note on `image` explaining that only the AVIF encoder
  is being removed and why the decoder path is unaffected;
- a `# replace this with main when #635 is merged` expiry date on a patch,
  so a pin cannot outlive its justification silently.

The estate's equivalent discipline lives in registry notes and
`supply-chain` review comments, away from the pin. Adopting zed's rule,
"the pin site carries the reason and the expiry", costs one comment per pin
and prevents the classic dead-pin archaeology. The kit template should show
one example of each form.

## 3. MSRV is a CI matrix axis at slint, and absent from rust-kit

slint's `ci.yaml` builds the same matrix twice with `rust_version: "1.95"`
and `rust_version: beta`, so the declared MSRV is verified on every push
rather than documented and hoped for. The estate declares `rust-version` in
every kit crate, and nothing in `rust-kit.yml` compiles against it: the
declarations are currently promises, not checks.

Adopt: an `msrv` job in rust-kit that resolves `rust-version` from the
manifest and runs `cargo check` on that toolchain. Blocked for now: the
rebrand holds unstaged edits to `rust-kit.yml`, and the gate's first loop
should not merge inside someone else's working tree. Tracked here so it
survives the rebrand.

## 4. libcosmic's vendoring anatomy, and why the estate should keep refusing it

libcosmic does not depend on a published iced fork; it vendors iced into the
repository and consumes it as path dependencies (`path = "./iced"`,
`path = "./iced/core"`, and so on), then re-exports upstream features
through its own feature flags (`advanced-shaping = ["iced/advanced-shaping"]`).
The wrapper's public surface is a curated projection of a private tree.

This is the mechanism behind study 45's COSMIC counter-model, and reading
it at the source sharpens the verdict: the path-dep fork gives total control
and zero version friction, and its cost is that every upstream feature must
be manually passed through forever, which is exactly the feature-flag
plumbing visible at the top of libcosmic's manifest. The estate's
extract-and-share doctrine (ADR-0005) publishes the shared thing and makes
consumers pin it; version friction is paid once at publish time instead of
continuously at rebase time. Keep refusing vendoring for estate-owned
foundations. If a third-party foundation ever must be forked, record it as
pdfcraft was (registry entry, `crates: []`, do-not-adapt) and mirror zed's
expiry-comment rule on the path pins.

## 5. llms.txt: none of the flagship projects ship one

A sweep of all 13 clones found no `llms.txt` or `llms-full.txt` artifact and
no workflow producing one. The estate publishes llms.txt per crate and gates
its links nightly (`check-llms-links.py`). This is the clearest place the
estate is ahead of the field: the agent-facing contract the ecosystem has
not standardized yet. Keep the gate; do not wait for the ecosystem to
validate it.

## 6. Duplicate majors: the gate exists, and the baseline is clean

`scripts/check-duplicate-majors.py` now enforces the one-major-per-graph
rule with honest scope classification: a duplicate blocks only when the
repo's own manifests require both majors (the chose-both case, the rusqlite
class); a second major arriving under an upstream requirement is reported
as transitive-only with `--all`, because it is not ours to fix. Eleven-case
self-test.

Fleet baseline on 2026-10-23: zero chose-both graphs. 241 transitive-only
duplicate names across 63 lockfiles, concentrated in the forks and heaviest
consumers (clawdius 30, kestrel 28, estate-integration 16); `syn` 1.x under
old proc-macro stacks and `r-efi` under UEFI targets account for most of
the volume. These disappear when upstreams unify; the gate's job is to keep
the estate from ever adding its own.

Wiring note: the check belongs as an advisory job in rust-kit (every kit
repo's lockfile is present in its checkout). Same rebrand block as section
3; both wire in after the rebrand lands.

## Open from this round

1. rust-kit: MSRV matrix leg (section 3), advisory first loop.
2. rust-kit: duplicate-majors advisory job (section 6).
3. Kit template: pin-site comment examples from section 2.
4. Deferred from study 45: workspace.dependencies centralization for the
   five multi-crate repos, still the largest open item.
