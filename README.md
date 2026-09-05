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
- dependabot weekly. cargo-vet audits for Tier A (pilot).
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

## Repo Layout

- `.github/workflows/rust-kit.yml` — shared reusable CI (the gate matrix)
- `templates/deny.toml` — dependency governance config
- `templates/SECURITY.md`, `templates/THREAT-MODEL.md`,
  `templates/REQUIREMENTS.md`, `templates/CHANGELOG.md`
- `templates/dependabot.yml`
- `scripts/release.sh` — release automation
- `scripts/apply-standards.sh` — bulk-apply templates to a kit repo
