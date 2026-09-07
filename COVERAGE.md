# Coverage Audit — October Coverage-Gate Data

**Date:** 2026-09-05 · **Tool:** cargo-llvm-cov 0.8.7 (llvm-cov, summary-only, `--all-features`) · **rustc 1.94.1**
**Scope:** all 56 Rust kit repos — **no pending crates**; every repo was run.
**Command per repo:** `cargo llvm-cov --summary-only --all-features` · thresholds per charter: **A ≥ 90 / B ≥ 80 / C ≥ 70** (Tier C informational until 2026-10).

Status legend: **PASS** ≥ threshold · **GAP** measured, below threshold (deficit in pts) · **FAIL** run failed before a coverage number existed.
`PASS*` = passed threshold, but has a flaky/failing property test that must still be fixed (see FAIL & Flakes).

## Hard-gate readiness (2026-09)

**Date:** 2026-09-07 · **Tool:** cargo-llvm-cov 0.8.7, `--summary-only --all-features` · same thresholds.

Tier A gap-closing sprint: the 3 GAP crates (barbican, hdwallet, blobkit) were closed with real
behavioral tests (signature recovery, error-path, wire-format assertions); the 3 previously-PASS
crates (tokenkit, cryptkit, ws-kit) were re-measured and hold. All closed crates pass the full
gate (check / test / clippy `-D warnings` / fmt) and are committed + pushed.

| Crate | Tier | Line % (2026-09-05) | Line % (2026-09-07) | Missed/Total | Δ | Status |
|---|---|---|---|---|---|---|
| salting | A | 99.7 | 99.7 * | 1/308 | +9.7 | PASS* — flaky proptest still outstanding |
| hdwallet | A | 83.6 | **98.0** | 18/910 | +8.0 | **READY** |
| breaker | A | 96.9 | 96.9 | 21/668 | +6.9 | PASS |
| cryptkit | A | 95.4 | 95.4 | 9/196 | +5.4 | PASS — re-measured, holding |
| webauthn-kit | A | 94.8 | 94.8 | 92/1780 | +4.8 | PASS |
| tokenkit | A | 92.8 | **96.7** | 19/582 | +6.7 | **READY** — re-measured, improved |
| ws-kit | A | 91.9 | 91.9 | 81/997 | +1.9 | PASS — re-measured, holding (incl. new origin.rs tests) |
| blobkit | A | 83.5 | **92.9** | 72/1018 | +2.9 | **READY** (exceptions documented in blobkit `COVERAGE-NOTES.md`) |
| barbican | A | 49.4 | **98.1** | 3/156 | +8.1 | **READY** |
| otelkit | A | 78.6 | 78.6 | 87/407 | −11.4 | GAP (~7 tests) |
| validkit | A | 76.8 | 76.8 | 203/876 | −13.2 | GAP (~17 tests) |
| healthkit | A | 76.3 | 76.3 | 64/270 | −13.7 | GAP (~5 tests) |
| money | A | 74.5 | 74.5 | 127/498 | −15.5 | GAP (~11 tests) |
| ratelimit | A | — | — | — | — | **FAIL** — failing proptest still blocks measurement |

\* salting number not re-measured this pass; the flaky `fuzz_edited_params_are_classified`
proptest (seed persisted in `proptest-regressions/`) must be fixed before October regardless.

**blobkit note:** during gap-closing, a latent bug was found and fixed in hdwallet (not blobkit):
`hdwallet::eth::sign_eth_transaction` declared a 12-field RLP list but appended 11 (missing the
empty access_list), so the function panicked unconditionally — it had never been executed (0%
coverage). Fixed with the tests that exercise it.

### Verdict: Tier A is **NOT READY** — 9/14 at threshold

- **Ready (9):** salting, breaker, cryptkit, webauthn-kit, tokenkit, ws-kit, hdwallet, blobkit, barbican.
- **Remaining work (5):** ratelimit (proptest triage — *blocking*, cheapest first), healthkit (~5
  tests), otelkit (~7 tests), money (~11 tests), validkit (~17 tests). Roughly 40 focused tests
  plus one property-test triage put the tier at 14/14. salting's flaky proptest must also be
  stabilized (test-gate violation, independent of its 99.7% number).

## Results

| Crate | Tier | Line % | Missed/Total lines | Δ vs threshold | Status |
|---|---|---|---|---|---|
| salting | A | 99.7 | 1/308 | +9.7 | PASS* |
| breaker | A | 96.9 | 21/668 | +6.9 | PASS |
| cryptkit | A | 95.4 | 9/196 | +5.4 | PASS |
| webauthn-kit | A | 94.8 | 92/1780 | +4.8 | PASS |
| tokenkit | A | 92.8 | 38/530 | +2.8 | PASS |
| ws-kit | A | 91.9 | 81/997 | +1.9 | PASS |
| hdwallet | A | 83.6 | 149/909 | −6.4 | GAP |
| blobkit | A | 83.5 | 127/770 | −6.5 | GAP |
| otelkit | A | 78.6 | 87/407 | −11.4 | GAP |
| validkit | A | 76.8 | 203/876 | −13.2 | GAP |
| healthkit | A | 76.3 | 64/270 | −13.7 | GAP |
| money | A | 74.5 | 127/498 | −15.5 | GAP |
| barbican | A | 49.4 | 79/156 | −40.6 | GAP |
| ratelimit | A | — | — | — | **FAIL** |
| cas-kit | B | 94.9 | 60/1175 | +14.9 | PASS |
| media-kit | B | 94.1 | 59/992 | +14.1 | PASS |
| geo-kit | B | 90.0 | 94/942 | +10.0 | PASS |
| docs-pipeline | B | 86.5 | 289/2148 | +6.5 | PASS |
| eventbus | B | 85.9 | 104/739 | +5.9 | PASS |
| fetchkit | B | 82.3 | 110/623 | +2.3 | PASS |
| actor-kit | B | 81.4 | 690/3703 | +1.4 | PASS |
| cachekit | B | 79.7 | 113/556 | −0.3 | GAP |
| mailkit | B | 75.0 | 176/705 | −5.0 | GAP |
| axum-stack | B | 38.8 | 85/139 | −41.2 | GAP |
| billing-kit | C | 100.0 | 0/49 | +30.0 | PASS |
| http-error | C | 100.0 | 0/11 | +30.0 | PASS |
| json-envelope | C | 100.0 | 0/12 | +30.0 | PASS |
| paginate | C | 100.0 | 0/119 | +30.0 | PASS |
| errcode | C | 97.7 | 6/265 | +27.7 | PASS |
| crdts-kit | C | 97.3 | 12/440 | +27.3 | PASS |
| simd-tokenizer | C | 96.5 | 10/285 | +26.5 | PASS |
| api-types | C | 95.8 | 8/191 | +25.8 | PASS |
| envstack | C | 94.7 | 63/1184 | +24.7 | PASS |
| model-router | C | 92.9 | 32/453 | +22.9 | PASS |
| shared-state | C | 92.8 | 15/208 | +22.8 | PASS |
| delta-kit | C | 88.9 | 63/569 | +18.9 | PASS |
| leptos-macro | C | 87.7 | 16/130 | +17.7 | PASS |
| pid-manager | C | 85.7 | 10/70 | +15.7 | PASS |
| retry-backoff | C | 85.5 | 25/172 | +15.5 | PASS |
| graceful | C | 81.8 | 39/214 | +11.8 | PASS |
| typed-id | C | 80.6 | 6/31 | +10.6 | PASS |
| flag-kit | C | 80.2 | 126/636 | +10.2 | PASS |
| oauth-toolkit | C | 76.5 | 332/1411 | +6.5 | PASS |
| auditlog | C | 76.3 | 135/570 | +6.3 | PASS |
| tantivy-ext | C | 57.9 | 207/492 | −12.1 | GAP |
| leptos-capital-markers | C | 56.6 | 59/136 | −13.4 | GAP |
| leptos-map-search | C | 55.8 | 140/317 | −14.2 | GAP |
| leptos-crypto-ws | C | 55.9 | 86/195 | −14.1 | GAP |
| leptos-stale-indicator | C | 46.9 | 52/98 | −23.1 | GAP |
| leptos-sparkline | C | 36.4 | 157/247 | −33.6 | GAP |
| accessctl | C | 31.1 | 177/257 | −38.9 | GAP |
| testkit | C | 26.4 | 53/72 | −43.6 | GAP |
| app-error | C | — | — | — | **FAIL** |
| clock | C | — | — | — | **FAIL** |
| poolkit | C | — | — | — | **FAIL** |
| leptos-leaflet | C | — | — | — | **FAIL** |

## Summary

| Tier | Crates | PASS | GAP | FAIL | At/above threshold today |
|---|---|---|---|---|---|
| A (≥90) | 14 | 6 | 7 | 1 | 43% |
| B (≥80) | 10 | 7 | 3 | 0 | 70% |
| C (≥70) | 32 | 20 | 8 | 4 | 63% |
| **Total** | **56** | **33** | **18** | **5** | **59%** |

### GAP crates by deficit (largest first), with rough test estimate

Estimate ≈ missed_lines ÷ 12 (one focused test typically closes 10–15 lines). Treat as order-of-magnitude.

| Crate | Tier | Deficit | Missed lines | ~Tests to close |
|---|---|---|---|---|
| testkit | C | −43.6 | 53 | ~4 |
| axum-stack | B | −41.2 | 85 | ~7 |
| barbican | A | −40.6 | 79 | ~7 |
| accessctl | C | −38.9 | 177 | ~15 |
| leptos-sparkline | C | −33.6 | 157 | ~13 |
| leptos-stale-indicator | C | −23.1 | 52 | ~4 |
| money | A | −15.5 | 127 | ~11 |
| leptos-map-search | C | −14.2 | 140 | ~12 |
| leptos-crypto-ws | C | −14.1 | 86 | ~7 |
| healthkit | A | −13.7 | 64 | ~5 |
| leptos-capital-markers | C | −13.4 | 59 | ~5 |
| validkit | A | −13.2 | 203 | ~17 |
| tantivy-ext | C | −12.1 | 207 | ~17 |
| otelkit | A | −11.4 | 87 | ~7 |
| blobkit | A | −6.5 | 127 | ~11 |
| hdwallet | A | −6.4 | 149 | ~12 |
| mailkit | B | −5.0 | 176 | ~15 |
| cachekit | B | −0.3 | 113 | ~1–2 (only ~2 lines over) |

## FAIL reasons

| Crate | Tier | Reason |
|---|---|---|
| ratelimit | A | Property test `prop_adversarial_chain_matches_oracle` (tests/client_ip.rs:697) fails: adversarial `X-Forwarded-For` chain disagrees with the resolution oracle. Blocks `cargo test`; no coverage produced. Genuine gate blocker — needs bug-vs-flaky-property triage. |
| app-error | C | `--all-features` build break: `error-classify` src/lib.rs calls `.kind()` on `&CommonError` without `use crate::AppError;` — code does not compile under the all-features cfg union. |
| clock | C | Broken test target: package is `chronoshift` but `tests/integration.rs:1` does `use clock::…` → unresolved crate; integration test target has never compiled. |
| poolkit | C | `--all-features` dep conflict: activates sqlx `sqlite`/`unbundled`; `sqlx-sqlite 0.8.6` references `sqlite3_serialize`/`sqlite3_deserialize`/`sqlite3_prepare_v3` absent from the selected `libsqlite3-sys` build. Feature matrix needs fixing (pick bundled, or exclude conflicting feature pair). |
| leptos-leaflet | C | Test failure: `test_layer_state_custom` panics (tests/comprehensive_test.rs:90). Real failing test. |

**PASS\* flake:** salting — `proptest fuzz_edited_params_are_classified` (src/lib.rs:292) failed on re-run (seed persisted to `proptest-regressions/lib.txt`); clean run measured 99.7%. The 90% number is real; the flaky property still needs fixing before October.

All five FAILs violate the *test* gate (`test --all-features` must be green), independent of coverage — they block the October flip regardless of thresholds.

## Recommendation

### 1. Close before October (cheap, high-value)

- **cachekit (B, −0.3)** — one or two tests. Do immediately; makes Tier B 8/10.
- **barbican (A, −40.6)** — only 79 missed lines in a 156-line crate; ~7 tests. Cheapest big Tier A win.
- **hdwallet (A, −6.4, ~12 tests)** and **blobkit (A, −6.5, ~11 tests)** — moderate; plausible in a sprint.
- **otelkit (A, −11.4, ~7)** and **healthkit (A, −13.7, ~5)** — small absolute line counts.
- **ratelimit (A)** — fix or correctly-tighten the failing proptest first, then measure; likely lands high given 34 other IP-resolution tests pass.
- Stretch: **money (A, ~11 tests)**, **validkit (A, ~17 tests)** — doable but the largest Tier A test-writing lift.

That path puts Tier A at 12–13/14 by October (only validkit or money at risk), Tier B at 8/10.

### 2. Threshold adjustment candidates (honest rationale)

- **leptos-\* GAP crates (sparkline, stale-indicator, map-search, crypto-ws, capital-markers):** coverage is measured on the host target; wasm-bindgen/`js-sys`/DOM interop lines structurally cannot execute outside a browser, so the host-measured ceiling sits below 70 for glue-heavy crates. Recommend: keep them at Tier C *informational* past October until coverage is measured through a `wasm-bindgen-test` + headless-browser harness, or exclude `#[cfg(target_arch = "wasm32")]` interop modules from the denominator. Adjusting the threshold for these is measurement-limitation-driven, not effort-driven.
- **testkit (C, 26.4%):** utility crate, 72 lines, ~4–5 tests to close. It is cheap — recommend closing it rather than adjusting; if it is deliberately a "test-support" crate, consider exempting *test-support* crates from the gate explicitly instead of special-casing this one.
- **axum-stack (B, 38.8%, 139 lines):** tiny crate, badly undertested — but it is Tier B, where the gate is hard. Either write the ~7 tests before October or honestly demote to Tier C until it matures; do not lower B to 70.
- **No threshold change warranted:** accessctl (−38.9), tantivy-ext (−12.1) — real debt, keep 70%, schedule post-October work.

### 3. FAIL fixes required for October (blocking, any tier)

app-error (missing import), clock (rename test imports to `chronoshift` or add `lib name`), poolkit (fix sqlite feature unification), leptos-leaflet (fix or quarantine `test_layer_state_custom`), ratelimit (triage proptest), salting (stabilize flaky proptest).

## Method & limitations

- Single crate per repo (all repos are single-crate, none are workspaces). `--summary-only --all-features`, default jobs, 2 repos in parallel, per-repo timeout 15–30 min; total wall time ≈ 55 min.
- Numbers are **line coverage** from the `TOTAL` row of the llvm-cov summary table. Branch coverage is reported by llvm-cov but `-` for these crates (no branch instrumentation data with default settings).
- `--all-features` intentionally unions features; three repos fail to compile under that union (app-error, poolkit) or have a never-compiling test target (clock). A per-feature matrix would give different (likely better) numbers for those.
- Raw per-repo logs retained at `/tmp/opencode/cov/logs/` (transient). Re-run the audit any time with `cargo llvm-cov --summary-only --all-features` per repo.
- Proptest seeds discovered during this audit were persisted into the repos' `proptest-regressions/` files (salting, ratelimit) — re-runs will reproduce those failures deterministically.
