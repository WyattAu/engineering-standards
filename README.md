# WyattAu Engineering Standards

Production engineering standards for the WyattAu kit ecosystem, modeled on
FAANG platform practices, defence-grade traceability, and ECN/HFT latency
discipline.

## The Gate Matrix

Every kit repository runs this matrix via the shared CI workflow:

```yaml
jobs:
  quality:
    uses: WyattAu/engineering-standards/.github/workflows/rust-kit.yml@main
    with:
      tier: a        # a | b | c — selects coverage threshold + lint depth
```

| Gate | Tier A | Tier B | Tier C |
|---|---|---|---|
| build `--locked` (all-features + no-default-features) | ✅ | ✅ | ✅ |
| test `--all-features` | ✅ | ✅ | ✅ |
| clippy `-D warnings` | ✅ + pedantic | ✅ | ✅ |
| `unwrap_used` / `indexing_used` / `panic` denied | ✅ | — | — |
| fmt `--check` | ✅ | ✅ | ✅ |
| cargo-deny (advisories / licenses / bans) | ✅ | ✅ | ✅ |
| cargo-audit (scheduled weekly) | ✅ | ✅ | ✅ |
| llvm-cov | ≥90% | ≥80% | ≥70% (informational until 2026-10) |
| cargo-semver-checks | ✅ on version diff | ✅ | ✅ |
| criterion baseline regression | ✅ (latency-relevant) | optional | — |
| loom (`--cfg loom` job) | ✅ (concurrency primitives) | — | — |
| miri (pure-logic modules) | ✅ nightly job | — | — |
| wasm32 check | ✅ if wasm claimed | — | — |
| thumbv7em check (`embedded: true`) | ✅ if no_std claimed | ✅ if no_std claimed | ✅ if no_std claimed |

## no_std / Embedded

Leaf crates claim `no_std` when they build core-only (or core + `alloc`)
with `--no-default-features`. The embedded gate is the shared workflow's
`embedded: true` input:

```yaml
jobs:
  quality:
    uses: WyattAu/engineering-standards/.github/workflows/rust-kit.yml@main
    with:
      tier: c
      embedded: true   # adds cargo check --target thumbv7em-none-eabihf --no-default-features
```

Pattern: `#![cfg_attr(not(feature = "std"), no_std)]` + `extern crate alloc`,
with a `std` feature (default-on) for std-bound surface area — gate whole
modules behind it rather than silently degrading behavior (e.g. webhookkit
gates timestamp/replay/Stripe verification, which need a wall clock or std
mutex). `alloc` has no `HashMap`; use `hashbrown` with `default-hasher`.
Targets without 64-bit atomics (thumbv7em, Armv7-M) cannot use
`AtomicI64`; use `core` atomics on 64-bit-capable targets and a
critical-section fallback elsewhere (see chronoshift's `MockClock`).

### Audit results (2026-09-06)

| Crate | Status | Notes |
|---|---|---|
| validkit | ✅ ready | already `no_std`; passes thumbv7em check |
| error-codes (errcode) | ✅ ready | already `no_std` |
| error-classify (app-error) | ✅ ready | already `no_std` |
| typed-id | ✅ ready | already `no_std` |
| chronoshift (clock) | ✅ fixed | time → `std` feature gates `SystemClock`; MockClock uses critical-section fallback on non-64-bit-atomic targets |
| delta-kit | ✅ fixed | alloc-only fixes (`hashbrown::HashMap`); zstd strategy stays std-gated (`zstd` implies `std`) |
| webhookkit | ✅ fixed | stateless verify/parse core-only; timestamp/replay/stripe gated behind `std` |
| http-error (http-errors) | ✅ fixed | pure `#![no_std]` + alloc; unused deps removed |
| json-envelope | ✅ fixed | pure `#![no_std]` + alloc; `axum` adapter now a real optional dep |
| simd-tokenizer | ✅ fixed | SWAR estimator core-only; `tiktoken` implies `std` |
| model-router | ⚠ std-bound | `std::sync::Mutex` in `CostTracker` — fixable via spin/critical-section lock swap (follow-up) |
| cas-kit | ⚠ std-bound | genuinely std-bound: filesystem blob store (`fs`, `Path`, `tempfile`) |

## Policies

### 1. Versioning & Release (semver discipline)

- All crates use **semver**. Pre-1.0: breaking = minor bump.
- `cargo-semver-checks` runs on every version diff; a breaking change without a
  matching version bump **fails CI**.
- **No publish without**: green gate matrix, `CHANGELOG.md` entry for the
  version, git tag `v<version>` matching `Cargo.toml`.
- Release procedure: `scripts/release.sh <crate-dir> <version>` — bump,
  changelog check, dry-run, semver-checks, tag, publish, registry verify.
- MSRV floor: **1.85**. Exceptions require an entry below:
  - `tantivy-helper` — 1.86 (tantivy 0.26 requirement)

#### Release provenance

Releases carry a provenance note so any published artifact can be traced to
source commit, toolchain, and artifact hash:

- `scripts/verify-reproducible.sh <crate-dir>` — two from-scratch
  `--release --locked` builds through identical sanitized paths, compared by
  SHA-256 of every artifact. Results in `REPRODUCIBILITY.md`. (Caveat:
  verifies same-machine determinism, not cross-machine reproducibility.)
- `.github/workflows/attest.yml` — workflow_dispatch per crate: builds from
  the kit repo ref, emits `SHA256SUMS` + `provenance/<crate>-<version>.json`
  (`{crate, version, commit, toolchain, hash, ...}`), commits them here, and
  attempts GitHub build attestation (best-effort; needs id-token perms).
- A release should only be published once its provenance note exists for the
  tagged commit.

### 2. Panics & Error Handling (defence-grade failure modes)

- `unwrap()` and bare `expect()` are **denied in non-test code** (Tier A via
  lint, all tiers via review). Legitimate invariants use
  `.expect("INVARIANT: <why this cannot fail>")` with a justification comment.
- Every public fallible function returns `Result` with a crate-owned error
  type (`thiserror`). Documented failure modes in doc comments are part of the
  API contract (`#[deny(missing_docs)]` enforced ecosystem-wide).
- No `std::process::exit`, no swallowing errors with `let _ =` on `Result`.

### 3. Concurrency Verification

- Shared mutable state uses either loom-compatible primitives behind
  `#[cfg(loom)]` type shims, or documented CAS loops.
- Concurrency primitives (Tier A) carry loom models: minimum 2 interleaving
  scenarios per invariant. Loom models must be proven non-vacuous (a seeded
  race must be caught).
- DashMap/tokio internals are trusted; the crate's own atomic discipline is
  not.

### 4. Input Parsing (fuzz policy)

- Every public function taking `&str`/`&[u8]` from an untrusted source gets a
  `cargo-fuzz` harness asserting **Err-not-panic**.
- Fuzz harnesses cap input size and resource amplification (decompression
  bombs, Argon2 cost params) so fuzz runs stay fast.
- CI smoke-runs fuzz harnesses (short budget); deep runs are manual.

### 5. Performance (ECN/HFT discipline)

- Latency-relevant crates publish **measured P50/P99** in their README
  (benchmark: hardware, date, numbers) — claims without numbers are removed.
- Criterion baselines are committed on `main`; CI fails on regression >20%
  for P99 latency benches.
- Hot paths are allocation-profiled (dhat). "Zero-alloc" claims require
  proof in the bench suite.
- **Determinism**: decision paths (ordering, matching, routing) use
  `BTreeMap`/total-order types, never `HashMap` iteration order. Proptest
  generators are seeded where reproducibility matters.

### 6. Security (defence traceability)

- Security-critical crates (Tier A crypto/auth subset: webauthn-kit, cryptkit,
  salting, tokenkit, multi-chain-wallet, blobkit) carry:
  - `SECURITY.md` (disclosure path)
  - `THREAT-MODEL.md` (STRIDE per public surface)
  - `REQUIREMENTS.md` with numbered requirements (`REQ-<crate>-NNN`)
  - Doc-comment `REQ-` IDs + a traceability matrix (requirement → test fn)
  - Constant-time audit note (where secret-dependent branching exists)
- All crates: `SECURITY.md` with a disclosure contact.

### 7. Dependencies (supply chain)

- `deny.toml` in every repo: advisories `deny`, licenses allow-list
  (MIT/Apache-2.0/BSD/ISC/Unicode/Zlib), bans on duplicate versions (warn).
- dependabot weekly. cargo-vet audits rolled out to all Tier A repos
  (`supply-chain/` bootstrapped from crates.io/registry peer audits — mozilla,
  google, isrg, bytecode-alliance, embark-studios, fermyon, zcash; per-repo
  `vet.yml` runs weekly + on PR, non-blocking until exemption backlog is
  burned down).
- Vendoring is a deliberate act: vendored copies get a drift-check script
  (see ecom-engine `scripts/check_vendor_drift.sh` pattern).

### 8. Documentation

- `#![deny(missing_docs)]` everywhere; every public item documented; doc
  examples must compile (doctests are tests).
- README minimum: one-line value prop, install, working example, feature
  table, perf numbers if latency-relevant, license.

## Tier Definitions

- **Tier A — Security-critical / load-bearing (14)**: tokenkit, cryptkit,
  salting, webauthn-kit, multi-chain-wallet, barbican, validkit, breaker,
  throttle-kit, ws-kit, blobkit, decimal-money, healthkit, otelkit
- **Tier B — Flagship infra (10)**: actor-kit, cas-kit, eventbus-kit,
  cache-pal, fetchkit, media-kit, docs-pipeline, axum-stack, geo-kit, mailkit
- **Tier C — Long tail**: everything else

## Adopting the Standards

```yaml
# .github/workflows/ci.yml in your kit repo:
jobs:
  quality:
    uses: WyattAu/engineering-standards/.github/workflows/rust-kit.yml@main
    with:
      tier: a
      all-features: true
```

Then delete repo-local duplicated CI. Repo-specific jobs (looms, wasm,
benches) live alongside the shared call.

### Node/TS repositories (astro-solidjs, starlight, ts-package, ...)

Proportionate gate matrix via the shared Node workflow — locked install,
typecheck, lint, build, test:

```yaml
# .github/workflows/ci.yml in your Node/TS repo:
jobs:
  quality:
    uses: WyattAu/engineering-standards/.github/workflows/node-ci.yml@main
    with:
      package-manager: bun   # bun | npm
```

Each script the flags enable (`typecheck`, `lint`, `build`, `test`) must exist
in `package.json`. Commit your lockfile (`bun.lock` / `package-lock.json`) so
the frozen install stays reproducible. `templates/dependabot-npm.yml` covers
the npm ecosystem.

Scaffolds born green: `forgeyard init` (WyattAu/forgeyard) produces repos that
pass this matrix on first push.

## Repo Layout

- `.github/workflows/rust-kit.yml` — shared reusable CI (the Rust gate matrix)
- `.github/workflows/node-ci.yml` — shared reusable CI (Node/TS gate matrix)
- `.github/workflows/attest.yml` — per-crate release provenance (dispatch)
- `templates/deny.toml` — dependency governance config
- `templates/SECURITY.md`, `templates/THREAT-MODEL.md`,
  `templates/REQUIREMENTS.md`, `templates/CHANGELOG.md`
- `templates/dependabot.yml` (cargo), `templates/dependabot-npm.yml` (npm)
- `scripts/release.sh` — release automation
- `scripts/verify-reproducible.sh` — same-machine build determinism check
- `REPRODUCIBILITY.md` — reproducibility method, caveat, and results
- `provenance/` — committed release provenance notes + SHA256SUMS
- `scripts/apply-standards.sh` — bulk-apply templates to a kit repo
