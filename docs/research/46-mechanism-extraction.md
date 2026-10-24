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

## 7. Profile matrices: evaluated and rejected, with the measurement

rerun ships 13 cargo profiles (bench, web-release, debugging, dev-fast,
each with package overrides) and zed overrides codegen-units per package;
study 43 flagged this as adopt-selectively. The estate's heaviest consumer
measured: `cargo test` over estate-integration's 54 suites runs 20 seconds
wall, dominated by per-target linking (54 test binaries) rather than
dependency execution. The rerun-style lever, `opt-level = 2` on
dependencies, makes every dependency rebuild slower to speed up test
execution that is already trivial, and does not touch link time at all.
Neither condition that makes rerun's profiles pay (minutes-long dev builds,
simulation-heavy test execution) holds in the estate. Rejected on the
measurement; revisit if a suite ever runs compute over large inputs.

Related measurement while there: kit CI already runs `cargo nextest run`
(rust-kit.yml), so the local 20-second loop is a development convenience,
not the gate path.

## 8. Dependency-update bots: 3 of 13, and the strictest toolkit opts out

Only lapce and slint run dependabot and zed runs renovate; the other ten
flagships update dependencies by hand. slint's dependabot covers
github-actions, uv, and npm but not cargo: the strictest toolkit in the
corpus does not let a bot touch its Cargo.tomls. zed's renovate is
human-gated (`dependencyDashboardApproval`), batches on a schedule
(Wednesday after 3pm), groups monorepo ecosystems (serde, wasmtime), and
pins action digests.

The estate's template already covers cargo weekly with grouped
minor-and-patch plus github-actions, which is more than slint does, and
the estate's exact-pin discipline adds what no bot provides: every newer
publication is caught by the audit's drift check and landed with the
composition suites run against it (today: accessctl 0.1.1, comfyui-kit
0.2.2, json-envelope 0.1.1, report-kit 0.2.1, all bumped with 434 tests
green). Nothing to adopt; the estate's loop is the stricter bot.

## Open from this round

1. rust-kit: MSRV matrix leg (section 3). Status: the check now exists as
   `scripts/check-msrv.py` (missing/non-canonical block; above-floor is
   informational; forks, orphans, and dormant repos are exempt as upstream
   trees). Baseline: 57 estate-authored repos declare rust-version, all
   canonical at 1.85, with five repos legitimately above floor and listed.
   Wiring into rust-kit is blocked by the rebrand's unstaged rust-kit.yml
   edits.
2. rust-kit: duplicate-majors advisory job (section 6). Same wiring block.
3. Kit template: pin-site comment examples from section 2; landed as
   `templates/Cargo.toml.workspace` with the workspace stanza.
4. Deferred from study 45, with its correction applied: workspace
   centralization now applies to trendkit (in flight by its maintainer)
   and to the kit template for any repo that grows a second crate.
   signalkit is the in-estate reference implementation.
5. process: research-note numbering collided twice in one day (two
   independent 44s, then two 45s and two 46s). Distinct slugs keep the
   files findable, but the loop should either allocate numbers centrally
   or drop the numeric prefix; pick one at the next loop review.
6. process, measured 2026-10-24: a continuously publishing round makes
   continuous drift-draining impossible. The day's waves went 15 -> 27
   -> swept to 4 -> back to 9 -> swept to 2 -> back to 9 within hours;
   every sweep was overtaken before its commit landed. The audit treats
   drift as a reported work item and exits 0, and the composition suites
   stay green on their pinned set, so nothing is broken while the queue
   stands. The closing step of a publishing round should be one pin-bump
   sweep against the final state, which converges in a single pass;
   draining mid-round is motion without progress.
