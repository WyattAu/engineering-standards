# 1.0 Releases — API Stability Wave

**Date:** 2026-09-05 · **Gate:** engineering-standards README §1 + gate matrix —
green check/test/clippy `--all-features -D warnings`, cargo-semver-checks clean
vs latest tag, coverage ≥ tier threshold, no open High risks in THREAT-MODEL.md,
`CHANGELOG.md` 1.0.0 entry, tag `v1.0.0` + publish + registry verify.
**Procedure:** `scripts/release.sh <crate-dir> 1.0.0` (bump → gates → semver-checks
→ dry-run → publish → tag → push → registry verify).

## Released

| Crate | Repo | Prior | Now | semver-checks | Published |
|---|---|---|---|---|---|
| salting | WyattAu/salting | 0.2.1 | 1.0.0 | clean ("no semver update required") | ✓ `cargo info` + registry verify |
| breaker | WyattAu/breaker | 0.3.0 | 1.0.0 | clean | ✓ `cargo info` + registry verify |
| geo-kit | WyattAu/geo-kit | 0.1.1 | 1.0.0 | clean | ✓ `cargo info` + registry verify |
| error-codes | WyattAu/errcode | 0.1.0 | 1.0.0 | clean | ✓ `cargo info` + registry verify |

Coverage at release: salting 99.7% (A) · breaker 96.9% (A) · geo-kit 90.0% (B) ·
error-codes 97.7% (C) — all ≥ tier thresholds per COVERAGE.md (2026-09-05 audit).

### Gate fixes made during this wave

| Repo | Fix | Commit |
|---|---|---|
| breaker | `benches/call_overhead.rs`: two must-use `Result`s under `-D warnings` (`--all-targets` reaches benches) | `ef1428c` |
| errcode | `tests/proptest.rs:27`: clippy `manual_range_contains` → `(100..600).contains(&status)` | `3edfb7e` |

Both were caught by the release gate itself (clippy `-D warnings`), fixed, then
re-run through the full gate before publish.

### Notes

- errcode/chronoshift CHANGELOGs carried a stale "not yet published to
  crates.io" note from before the `error-codes`/`chronoshift` names were
  registered; corrected in the 1.0.0 CHANGELOG entries (verified via
  `cargo info`: both crates.io names resolve to WyattAu repositories).
- salting's `PASS*` flake (proptest `fuzz_edited_params_are_classified`) was
  closed by the 0.2.1 PHC-clamp work; regression seed is committed in
  `proptest-regressions/`.

## Deferred (wave 1) — exact blockers

| Crate | Repo | Prior | Tier | Blocker | Remaining work |
|---|---|---|---|---|---|
| chronoshift | clock | 0.2.0 | C | Coverage **64.29% < 70** (−5.7; 25/70 lines missed; measured 2026-09-05 after the import fix — tests now compile/pass, but `wasm.rs` is 0% host-side) | ~2–3 focused tests; wasm module needs a `wasm-bindgen-test` harness or `cfg` exclusion from the denominator. Then 1.0.0. |
| webhookkit | webhookkit | 0.2.0 | A | Coverage **86.69% < 90** (−3.3; 43/323 missed; `ffi.rs` 33 lines at 0%). Also missing `THREAT-MODEL.md`, `CHANGELOG.md`, and any git tag → semver-checks baseline undefined (§1: no publish without changelog + tag) | ~4 tests (FFI harness or denominator exclusion; stripe/replay/timestamp edges); write STRIDE threat model; create CHANGELOG; tag current state as baseline. Then 1.0.0. |
| validkit | validkit | 0.1.x | A | Coverage GAP **76.8%** (−13.2; 203/876 missed) | ~17 tests (COVERAGE.md estimate). Then 1.0.0. |
| decimal-money | money | 0.2.0 | A | Coverage GAP **74.5%** (−15.5; 127/498 missed) | ~11 tests. Then 1.0.0. |
| healthkit | healthkit | 0.1.0 | A | Coverage GAP **76.3%** (−13.7; 64/270 missed) | ~5 tests (small absolute count — cheapest Tier A close). Then 1.0.0. |
| throttle-kit | ratelimit | 0.4.x | A | Coverage **FAIL** — no number: property test `prop_adversarial_chain_matches_oracle` (`tests/client_ip.rs:697`) fails, blocking `cargo test` | Bug-vs-flaky-proptest triage first, then measure coverage. 1.0.0 only after test gate is green. |

## Verification commands

```sh
cargo info <crate>              # version + repository on crates.io
git -C <repo> tag --list v1.0.0 # release tag
scripts/release.sh <dir> 1.0.0 --dry-run   # re-run gate without publishing
```
