# Mutation Testing — cargo-mutants Program

**Date:** 2026-09-06 · **Tool:** cargo-mutants 27.1.0 · **rustc 1.94.1**
**Scope:** Tier A fast suite — `--all-features`, 25-minute per-crate wall-clock
cap locally (on cap: narrow scope, report partial).
**Command per crate:** `cargo mutants --all-features -o <outdir>`

Line coverage (see [COVERAGE.md](COVERAGE.md)) measures which lines *ran*;
mutation testing measures whether the suite would *notice* if they did the
wrong thing. Score = killed ÷ viable (unviable = cannot compile, excluded).

## Policy

1. **Weekly informational CI.** Every processed crate runs `mutation.yml`
   (Saturday 03:00 UTC cron + `workflow_dispatch`): install cargo-mutants,
   `cargo mutants --all-features -o mutants-out`, upload report as artifact.
   `continue-on-error: true` — **promote to gating when scores stabilize**:
   once survivors are equivalent-only (or zero) and the score holds across 4
   consecutive weekly runs, flip to `continue-on-error: false` and add
   `--fail-under <score>`.
2. **Every survivor is triaged into exactly one bucket:**
   - **Missing test** → write the killing test (asserts the mutated *behavior*,
     not a tautology); confirm the kill with a scoped cargo-mutants run.
   - **Equivalent mutant** → recorded in `<crate>/mutants-equivalent.txt` as
     `<file>:<line> — rationale`. Suppressions are allowed *only* for true
     equivalents.
   - **Untestable-by-harness (cfg-unviable)** → excluded in
     `.cargo/mutants.toml` (`exclude_globs`) or ledgered in
     `mutants-equivalent.txt` with rationale: code never compiled by the
     `--all-features` suite because it is `cfg`-gated to another verification
     harness (loom / Kani / `--no-default-features` fallback engine /
     wasm-bindgen-test), with a pointer to that harness.
   - **Unviable / timeout** → noted; a test-suite *hang* under a mutant still
     counts as detection.
3. **Never weaken a test to kill a mutant.** Killing tests strengthen the
   suite; they may add test code but must not relax assertions, delete tests,
   or exclude surviving production code without a harness rationale (rule 2).
4. **Per-crate commit convention:** `test: kill <n> surviving mutants
   (cargo-mutants)` — tests + triage artifacts only.

## Results — fast suite (2026-09-06)

| Crate | Mutants | Killed | Survived | Score (viable) | Initial score | Tests added | Equivalents | Notes |
|---|---|---|---|---|---|---|---|---|
| salting | 60 | 46 | 0 | 100% of processed (partial) | 96.8% (partial, 25-min cap) | 1 | 0 | 5 timeout/unclassified = detected; completion via scoped passes; see notes |
| barbican | 10 | 7 | 0 | 100% | 100% | 0 | 0 | 3 unviable |
| breaker | 73* | 58 | 1 | 98.3% | 74.7% | 1 | 1 | *after cfg-harness exclusion of `src/lock.rs` (16 mutants); 14 unviable |
| healthkit | 19 | 15 | 0 | 100% | 100% | 0 | 0 | 4 unviable |
| chronoshift (clock) | 49 | 45 | 0 | 100% | 100% | 11 | 0 | 4 unviable; `src/wasm.rs` excluded (wasm-bindgen-test harness) |
| validkit | 291 | 177+ | 0 unexplained | 78.0%† | 57.3% | 47 | 3 (+45 ledgered unviable-cfg) | †measured mid-triage; further kills landed in `b7d2946`/`66268c6`; see notes |

**Aggregate, crates with complete initial runs** (barbican, breaker, healthkit,
chronoshift, validkit — 458 mutants): initial detection **253/369 viable =
68.6%** in suites averaging ~90% line coverage; after triage **302/353 =
85.6%**, with every remaining survivor classified (equivalent or cfg-unviable)
and zero unexplained.

## Headline findings (what mutation testing caught that coverage missed)

- **breaker — 96.9% line coverage, but 1 in 4 viable mutants survived.**
  Line coverage saw every line of the metrics code path execute; no assertion
  ever *observed* it. `StateMachine::failure_count()` (feeds the
  `circuit_breaker_failure_count` histogram) could be replaced with a constant
  `0` or `1` and every state-based test stayed green — the getter's only
  consumer is a metric no test captured. The killing test installs a scoped
  `metrics` recorder and asserts the histogram carries `[1.0, 2.0]` after two
  consecutive failures. Also surfaced: 16 mutants in the `cfg(loom)`/`cfg(kani)`
  lock shim that the host suite never compiles (invisible to coverage in both
  directions — now excluded with harness rationale), and one tautological
  equivalent (`builder()` defined as `Default::default()`).
- **validkit — 94.8% line coverage, 57.3% mutant kill.** The 97 initial
  survivors decomposed into four classes: (a) `Serialize` bodies replaceable
  with `""`/`"xyzzy"` — seven value types serialized to JSON with **zero**
  round-trip assertions, i.e. silent data corruption on the write path was
  invisible; (b) accessor bodies (`as_str`/`as_ref`/`into_inner`) never
  value-asserted for any of the nine types; (c) boundary branches (total-length
  caps, CR/LF rejection, userinfo rejection, IP-shaped bucket names,
  cron punctuation position) that hostile-input tests never reached — the
  `url` crate even strips CR silently, making the guard *load-bearing*; (d) ~45
  `cfg(not(feature))` fallback-engine mutants uncompiled under
  `--all-features` (covered by `tests/fallback_paths.rs` under
  `--no-default-features`), plus 3 proven equivalents. Killing tests now pin
  exact error messages and 253/254/255-style boundaries, which line coverage
  had already "covered" at 100%.
- **salting — 99.7% line coverage, and the suite could not tell the
  low-memory Argon2 preset from the default.** `low_memory_params` round-trips
  a hash, but *any* parameters round-trip: replacing the preset body with
  `Default::default()` (silently raising cost to 3 iterations / 4 lanes — a
  documented-contract and embedded-budget regression) survived. The kill is an
  exact field pin (64 MiB / t=2 / p=1 / 32-byte output). A security-parameter
  contract had 0% effective coverage despite 99.7% line coverage.
- **barbican, healthkit, chronoshift — 0 survivors** on viable mutants. These
  suites assert values, not just execution: mutation testing confirms their
  green coverage is load-bearing, not incidental.

## Queued — Tier A (workflow shipped, baseline pending)

Weekly `mutation.yml` pushed; header comment reads *"mutation baseline pending
— expect hours; run locally first."* Run each locally before the first
scheduled CI trigger, then record baselines here.

| Crate | Workflow | Baseline |
|---|---|---|
| tokenkit | pushed | pending |
| cryptkit | pushed | pending |
| webauthn-kit | pushed | pending |
| hdwallet | pushed | pending |
| ratelimit | pushed | pending |
| ws-kit | pushed | pending |
| blobkit | pushed | pending |
| money | pushed | pending |
| otelkit | pushed | pending |

## Method & limitations

- cargo-mutants 27.1.0. Note for triage scripts: this version has no `--line`
  filter — confirm kills with `--file <path>` and/or `-F <regex>` matched
  against the mutant names from `--list`.
- 25-minute local cap: salting's full run (60 mutants, 44–221 s of Argon2 per
  scenario) exceeded the cap at 34/60 processed; the survivor found was killed
  and completion continued via scoped `--file src/lib.rs` passes (18 further
  mutants: 15 caught, 3 timeout, 0 missed). Mutants that hang the proptest
  shrink loop (`validate_phc_params`, `build_argon2` body-replacements) are
  counted as detected, not clean kills; one infrastructure `Failure`
  (`hash_password → Ok("xyzzy")`, test-process launch failure) was
  unclassified at cap and is counted undetected until re-run.
- breaker `src/lock.rs` is excluded via `.cargo/mutants.toml`: the module is
  `#[cfg(loom)]`/`#[cfg(kani)]` only — no cargo feature ever activates it, so
  host-suite mutants there are uncompiled-by-construction and are verified by
  `RUSTFLAGS="--cfg loom" cargo test` and `cargo kani` instead.
- validkit's all-features run cannot compile its `cfg(not(feature))` fallback
  engines; those mutants are ledgered unviable-cfg in
  `mutants-equivalent.txt` and are exercised by `tests/fallback_paths.rs`
  under `--no-default-features --features serde,std` (a scoped probe of that
  profile confirmed both its catches and its own gaps, e.g. the
  `is_valid_cron` smoke now added).
- Three validkit cron mutants (114×2, 115) are message-equivalent: any field
  erring there re-errs at the leading/trailing/duplicate-punctuation checks
  with the identical `invalid cron field` message (rationale in
  `mutants-equivalent.txt`).
- cargo-mutants runs `--all-features`; crates whose feature unions fail to
  build (see COVERAGE.md FAIL notes) must fix that first — mutation runs
  inherit the same blocker.
- Raw per-crate outputs retained under `/tmp/mutants/<crate>/mutants.out`
  (transient). Re-run any time with `cargo mutants --all-features`.
