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

### Status update (2026-09-26)

- **Gate adoption complete (2026-09):** every kit repository in the estate now
  runs the shared `rust-kit.yml` matrix via one reusable-workflow call —
  including the newest wave: metrics-kit, config-kit, idempotency-kit,
  outbox-kit, percentile-kit, chaos-kit, telemetry-init, worker-kit.
- **cargo-vet enforcement is live:** the shared workflow's `vet` job
  (`cargo vet --locked`) fails CI on unaudited dependencies; kit repos carry a
  committed `supply-chain/` and `Cargo.lock`.
- **Registry additions:** the 8 kits above are now on crates.io and listed in
  KITS.md and the site's crates page (63 published kits). Corrections:
  `fetchkit` publishes as `fetch-kit` (superseding `resilient-fetch`);
  `testkit` remains repo-only (not yet published).

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
- dependabot weekly. cargo-vet audits are **enforcing** via the shared
  workflow's `vet` job (`cargo vet --locked`, installed with
  `taiki-e/install-action`): every kit repo must carry a committed
  `supply-chain/` plus a committed `Cargo.lock` (`--locked` requires it —
  cargo-vet never generates one). New repos: run `cargo vet init` to
  bootstrap `supply-chain/` from crates.io peer audits (mozilla, google,
  isrg, bytecode-alliance, embark-studios, fermyon, zcash) —
  `scripts/apply-standards.sh <repo>` does it automatically. Burn down any
  exemption backlog surfaced by `cargo vet` before it turns the gate red.
- Vendoring is a deliberate act: vendored copies get a drift-check script
  (see ecom-engine `scripts/check_vendor_drift.sh` pattern).
- Allow-list additions are ratified by PR: each new SPDX id lands in
  `templates/deny.toml` with a one-line rationale naming the dependency that
  requires it and a precedent repo that already accepts it.

### 8. Documentation

- `#![deny(missing_docs)]` everywhere; every public item documented; doc
  examples must compile (doctests are tests).
- README minimum: one-line value prop, install, working example, feature
  table, perf numbers if latency-relevant, license.

### 9. Naming & Repo Identity

- Repo name and published crate name are **identical** (no lookup tables).
- Names follow the estate taxonomy: `{domain}-{concern}` for domain stacks,
  `{concern}-kit` (hyphenated) for cross-cutting infrastructure, short names
  for unique primitives, product names for products.
- The full rules, the decision flowchart, the grandfathered-name list, and
  the pending repo-rename commands live in
  [`docs/naming-convention.md`](docs/naming-convention.md) — authoritative
  for every naming decision.

## Tier Definitions

- **Tier A — Security-critical / load-bearing (14)**: tokenkit, cryptkit,
  salting, webauthn-kit, multi-chain-wallet, barbican, validkit, breaker,
  throttle-kit, ws-kit, blobkit, decimal-money, healthkit, otelkit
- **Tier B — Flagship infra (10)**: actor-kit, cas-kit, eventbus-kit,
  cache-pal, fetch-kit, media-kit, docs-pipeline, axum-stack, geo-kit, mailkit
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

## The Estate Manifest

`estate.yml` is the registry of record for the estate: **181 repos**,
classified by area (`auth` `net` `obsv` `money` `data` `conc` `ui` `dx`
`docs` `infra` `app` `research` `personal`) and status, with the
crates.io packages each repo publishes.

```sh
python3 scripts/estate-audit.py          # full report; exit 1 on schema errors
python3 scripts/estate-audit.py --json   # machine-readable findings
python3 scripts/estate-audit.py --sync   # refresh the generated _seen blocks
```

Status is a claim about *proof*, not about activity:

| status | meaning |
|---|---|
| `core` | published **and** dogfooded — a consumer suite exact-pins one of its crates |
| `support` | published, active, not yet composed by any suite |
| `orphan` | published, neither composed nor recently active |
| `dormant` | no meaningful activity; superseded or shelved |
| `template` / `fork` / `personal` / `infra` | scaffolding, upstream forks, private repos, CI-only |

The audit enforces four invariants, and fails CI on any of them:

1. every repo under the account has exactly one manifest entry
2. every published crate is claimed by exactly one repo (no unclaimed
   packages, no double-claimed ones)
3. a `core` status means some consumer suite exact-pins one of its crates
4. an exact pin matches what crates.io currently serves

Beyond the schema it reports three classes of drift, which is what actually
keeps 181 repos honest:

- **pin drift** — a consumer tests an artifact nobody ships any more. This
  is not hypothetical: the audit's first run found **17 stale pins** in
  `estate-integration`, including a held-back `outbox-kit` whose newer
  release `ledger-kit` cannot consume. Holds are recorded in
  `pins_held:` with the reason and the ask, so "held on purpose" is
  distinguishable from "nobody noticed".
- **coverage debt** — a published crate no suite composes (53 at last
  count). Each round of `estate-integration` suites exists to retire some
  of this.
- **dormancy** — a repo whose status claims activity its push history does
  not support.

## Repo Layout

- `docs/naming-convention.md` — estate naming convention: the 6 rules,
  decision flowchart, domain-stack template, grandfathered names, and repo
  rename procedure
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
- `estate.yml` — the estate manifest: one entry per repo (area, status,
  published crates, supersession pointers) plus any deliberately-held pins
- `scripts/estate-audit.py` — verifies the manifest against GitHub,
  crates.io, and consumer pin sets; reports pin drift, coverage debt and
  dormancy, and fails on schema violations (`.github/workflows/estate-audit.yml`)
---

## Omni template estate

The [Omni templates](https://github.com/WyattAu?tab=repositories&q=omni-template)
are thin per-language scaffolds that consume these shared gates (rust-kit,
node-ci, python-kit, go-kit, haskell-kit) and ship housekeeping pre-baked.
The contract every template satisfies — and the coverage-tier table — lives
in [OMNI-CORE.md](OMNI-CORE.md). `apply-standards.sh` (+ per-language
variants `apply-standards-python.sh`, `apply-standards-go.sh`,
`apply-standards-haskell.sh`) remain the idempotent re-application path for
derived repos.

### Branch protection recipes (recommended per template)

| Check | R / Rust | TS | Python | Go | Haskell | C++ | Flutter | Infra/Dotfiles |
|---|---|---|---|---|---|---|---|---|
| quality (reusable gate) | rust-kit tier a | node-ci | python-kit | go-kit | haskell-kit | test.yml | reusable-analyze | lint |
| contract | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| devcontainer (image) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| msrv / matrix leg | ✅ (1.85) | — | ✅ (3.12+) | ✅ (oldstable) | ✅ (9.6/9.8) | — | — | — |
| e2e / fuzz / size budgets | fuzz+bench | ✅ playwright | — | ✅ fuzz | — | — | — | plan |

Recipe: require the `quality` + `contract` checks, require 1 approval
(self-owned repos: disable), require linear history, allow the marked
experimental legs to fail.

### Keeping the estate leading

The estate runs a monthly improvement loop against the market:

- [LOOP.md](LOOP.md) — the loop itself (survey → matrix diff → implement →
  test → publish) and its log, plus the advisory-to-gate graduation policy.
- [COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md) — feature-by-feature
  matrix against the leading templates per language, with the backlog.
- [PITFALLS.md](PITFALLS.md) — failure modes already paid for (Dependabot
  misreading toolchain refs, TypeScript 7 vs `astro check`, GHCR feature 401s,
  `mkdocs gh-deploy` vs workflow-built Pages, advisory-job semantics).

New gates land **advisory** for one loop, then graduate to blocking once the
whole loop has been green or triaged in writing.
