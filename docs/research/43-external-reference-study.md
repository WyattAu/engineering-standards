# Research note 43: External reference study: 12 flagship Rust projects

**Sources.** Shallow clones (October 2026) of zed-industries/zed,
slint-ui/slint, lapce/lapce, pop-os/cosmic-epoch + cosmic-files, flxzt/rnote,
rerun-io/rerun, fyroxengine/fyrox, GyulyVGC/sniffnet, neovide/neovide,
vizia/vizia, robbert-vdh/nih-plug. Structural extraction only: workspace
topology, CI inventory, dependency-management tooling, testing organization,
release engineering. No code review.

## The comparative matrix

| | members | workflows | [workspace.deps] | nextest | insta | deny/audit | semver-checks | MSRV | release automation |
|---|---|---|---|---|---|---|---|---|---|
| zed | 258 | 49 | yes | yes | yes | no | no | none | 5 channel workflows (stable/nightly) |
| slint | multi | 41 | yes | no | no | no | no | 1.95 | tag workflows, npm publish |
| lapce | 4 | 2 | yes | no | no | no | no | none | tag workflow |
| cosmic-files | 2 | 3 | yes | no | no | no | no | 1.93 | flatpak-heavy, no CI release |
| rnote | 4 | 6 | yes | yes | no | no | no | 1.89 | flathub-heavy |
| rerun | 18 | 53 | yes | yes | yes | no | no | 1.98 | **9 reusable publish workflows + DAG publisher** |
| fyrox | 24 | 1 | no | no | yes | no | no | none | none in-repo |
| sniffnet | 2 | 6 | yes | no | yes | no | no | none | signed installers, PPA, crates.io |
| neovide | 1 | 7 | no | yes | no | no | no | none | frozen-branch release checks |
| vizia | 4 | 4 | yes | no | no | audit only | no | none | none |
| nih-plug | 28 | 6 | no | no | no | no | no | 1.80 | bundler per plugin format |
| **estate (us)** | 1–4/repo | 1–2/repo | n/a | no | no | **yes + vet** | **yes** | declared | hand-ordered publishes |

## Findings that change what we do

### 1. rerun solved our publish problem (adopt)
`scripts/ci/crates.py` publishes a multi-crate workspace in **topological
order** over the dependency DAG, three rate-limited workers, `--dry-run`
mode, and version-bump automation (`version --bump prerelease --exact`).
This is precisely the hand dance we do every release (yesterday:
mp4-core → id3-core → audiobook-core, ordered by hand, published by hand
from a laptop). Adopt the pattern: a `scripts/ci/crates.py` equivalent in
engineering-standards, keyed to our layer graph.

### 2. Supply-chain gates: we are ahead of every reference project
Not one of the twelve runs cargo-deny or cargo-audit (vizia runs audit
only); none run semver-checks; none have a vet-style store; none sign
provenance. Our deny + audit + vet + semver + provenance stack exceeds
the entire reference set. **Do not regress these to "match the big
projects": they are the differentiator.**

### 3. nextest and insta are the mainstream (adopt)
4 of 12 run nextest (zed, rerun, rnote, neovide); 4 use insta snapshots
(zed, rerun, fyrox, sniffnet). Our test job is plain `cargo test`. Swap
rust-kit's test step to cargo-nextest (drop-in, faster, better failure
output) and introduce insta for the serialization/rendering crates
(conformance-adjacent: exact-output pins replace hand-written
assert_eq strings).

### 4. Renovate with discipline beats raw Dependabot (decision needed)
zed's renovate.json: GitHub-action digests pinned, wasmtime grouped,
`dependencyDashboardApproval` (updates wait for a human tick),
Wednesday-scheduled. Our Dependabot waves land Monday and the estate
spends Tuesday absorbing them. Renovate's grouping + approval flow would
turn the wave into a reviewed batch. Policy change: needs a call.

### 5. Profile matrices are load-bearing at scale (adopt selectively)
rerun ships 13 profile variants (bench, web-release, debugging, dev-fast,
each with package overrides); zed overrides codegen-units per package;
lapce has a `fastdev` profile. We have one profile per repo. When a
crate's build times hurt (EvergreenShims' month of red, our miri runs),
a `dev-fast` profile (opt-level 1, debug 1) is the standard tool.

### 6. Reusable release workflows beat per-repo ones (already ours)
slint and rerun converge on `*_reusable.yaml` + thin callers: the same
architecture as our rust-kit.yml. Validation, not change.

### 7. What nobody else does, that we do
fuzz-smoke per repo; the layer model with a CI gate; the estate audit
(182-repo manifest scan); the integration hub composing *published*
artifacts; conformance oracles with differential rivals. The reference
projects have nothing comparable: these are our moat.

## Not found

"glowwave synth": no public project by that name (searched). If it has
a URL, send it. The audio-plugin ground is covered by nih-plug (28
crates, bundler per format: studied).

## Recommended sequencing

1. Topological batch publisher (rerun pattern): retires the hand dance.
2. nextest in rust-kit's test job: drop-in.
3. insta in the serialization crates.
4. Renovate-vs-Dependabot decision.
