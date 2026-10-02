# clock-kit — precision time substrate (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file. `REQ-CLK-NNN` tags below are the traceability anchors
> the future implementation must cite: doc comments on public items carry the
> tags, every REQ maps to ≥ 1 named test (provisional matrix in §Requirements).

**Layer:** L1 — substrate · **REQs:** 6 (CLK-001…006) · **Deps:** `libc` (feature-gated) only — no rand, no serde · **no_std:** leaning · **Date:** 2026-10-02

| Field | Value |
|---|---|
| Layer | **L1 — substrate** — already listed in [docs/layers.md](../docs/layers.md) as a future L1 crate ("future: `uring-kit`, `clock-kit`, `hw-kit`") |
| Manifest declaration | `[package.metadata.layers] tier = "L1"` at repo creation |
| Estate deps | none at v1; a `chronoshift` (L0) edge is proposed but undecided — see §Decisions. Either way the ceiling rule holds (L1 ≥ L0). |
| External deps | `libc` behind the `libc` feature. No `rand`, no `serde`, no `chrono`. |
| Sibling | `chronoshift` (L0) owns general time **abstraction**; clock-kit owns time **precision and cost**. |

## §Semantics

clock-kit is the estate's time source for latency-critical paths (ECN/HFT feed
handlers, matching threads, latency measurement). It answers three questions
that `std` leaves unresolved: **how expensive is reading the clock**, **how
much do we trust it**, and **how do we test against it deterministically**.

### Guarantee grades

- **G1 — hard guarantee (monotonic suffix).** `Timestamp::mono` never goes
  backward within a process (REQ-CLK-001). Every clock implementation must
  enforce this by construction: a process-wide floor (`AtomicU64` on
  64-bit targets, critical-section fallback on targets without 64-bit
  atomics — the chronoshift MockClock pattern) so that even a misbehaving
  or poorly-synchronized source is clamped to the highest value ever
  returned. A regression is a bug, not a documented possibility.
- **G2 — advisory quality.** `SyncQuality` (REQ-CLK-004) is a *hint* read at
  clock construction/discovery time. It is never a guarantee: a PTP-labelled
  source may be in holdover. Consumers use it to decide whether derived
  timestamps may be correlated across machines, never for correctness.
- **G3 — deterministic fiction.** `MockClock` (REQ-CLK-005) never consults
  the OS. Time advances only when the test advances it, so property tests
  and replay are reproducible bit-for-bit.

### Wall vs monotonic

Wall time and monotonic time are separate fields with separate rules
(REQ-CLK-002). Wall time is comparable across processes and machines and may
step (NTP slew, PTP step, operator action). Monotonic time is comparable only
within a process and never steps. No API may derive one from the other
except through an explicitly labelled, lossy conversion helper.

### Cheap reads behind calibration

On x86_64/aarch64 the hot path reads a hardware counter (TSC / CNTVCT) and
converts through a calibrated ns-per-tick factor (REQ-CLK-003). Calibration
is an explicit, fallible step; the conversion is a multiply-shift, not a
division. If calibration fails or the counter is judged unusable (no
invariant-TSC bit, constant-freq check fails), the clock transparently falls
back to `Instant`-based reads under `std` (or `clock_gettime(CLOCK_MONOTONIC)`
under `libc`). Read cost and source used are observable (`Clock::source()`).

### PTP detection, not PTP participation

REQ-CLK-004 detects the *presence and classification* of a synchronized
source: `/sys/class/ptp/ptpN` device presence plus a `CLOCK_TAI` vs
`CLOCK_REALTIME` offset probe via `clock_gettime` (feature `ptp`, via
`libc`). It runs no daemon, opens no PHC device for control, and performs no
`adjtimex` writes. Detection is best-effort and never blocks or fails the
clock: any read error classifies as `SyncQuality::Fallback`.

### Latency statistics without allocation

`LatencyRing` (REQ-CLK-006) is a fixed-capacity (const-generic) ring of `u64`
nanos. Recording is O(1); when capacity is exceeded the oldest sample is
evicted — the ring is a sliding window, not an accumulator. `stats()` is
exact over the current window: it sorts a stack-resident copy of the live
samples (CAP bounded; default 4096 → 32 KiB scratch) and reports
min/max/mean (integer floor)/p50/p99/p99.9. No heap allocation anywhere;
the crate is core-only in this module. (Pattern donor: `percentile-kit` —
which is L2 and therefore **cannot** be a dependency; see Cross-references.)

## §API sketch

```rust
#![cfg_attr(not(feature = "std"), no_std)]
// features: std (default-on) · libc · tsc · ptp

pub enum SyncQuality { Ptp, Ntp, Fallback }                    // REQ-CLK-004

/// REQ-CLK-002: wall and monotonic are independent fields with independent rules.
pub struct Timestamp {
    pub wall: WallTime,   // SystemTime-backed under `std`; u64-epoch-nanos under core+libc
    pub mono: u64,        // nanos; REQ-CLK-001: never regresses within a process
}

pub struct WallTime { /* … */ }
impl WallTime {
    pub fn unix_nanos(&self) -> u64;                  // identical accessor on both builds
    #[cfg(feature = "std")] pub fn system(&self) -> std::time::SystemTime;
}

pub trait Clock {
    /// REQ-CLK-001: `t.mono` never decreases across calls within a process.
    fn now(&self) -> Timestamp;
    fn quality(&self) -> SyncQuality;                 // REQ-CLK-004 (const-ish per impl)
    fn source(&self) -> ClockSource;                  // Tsc | Cntvct | Instant | LibcMono | Mock
}

pub struct SystemClock;      // CLOCK_REALTIME + CLOCK_MONOTONIC (std or libc path)
pub struct CalibratedClock;  // REQ-CLK-003: TSC/CNTVCT behind calibrated conversion,
                             // Instant/CLOCK_MONOTONIC fallback; construction is fallible
pub struct MockClock;        // REQ-CLK-005

impl MockClock {
    pub fn start_at(mono_ns: u64, wall_ns: u64) -> Self;
    pub fn advance(&self, dt: core::time::Duration);  // manual, deterministic
    pub fn advance_nanos(&self, ns: u64);
    pub fn step_wall(&self, offset_ns: i64);          // simulate NTP/PTP step for tests
}

// REQ-CLK-003 — calibration (feature `tsc`; per-arch cfg inside):
#[cfg(all(feature = "tsc", target_arch = "x86_64"))]  pub fn counter_read() -> u64; // core::arch x86_64::_rdtsc (rdtscp-serialized)
#[cfg(all(feature = "tsc", target_arch = "aarch64"))] pub fn counter_read() -> u64; // cntvct_el0 via inline asm
pub struct Calibration { pub ns_per_tick: u64, pub frac: u32, pub method: CalMethod }
pub fn calibrate(reps: u32) -> Result<Calibration, CalError>; // multiply-shift factor out
                                                              // (no division on the read path)

// REQ-CLK-004 — detection (feature `ptp`, std):
pub fn detect_sync_quality() -> SyncQuality;   // /sys/class/ptp/ptpN + CLOCK_TAI offset probe
pub fn tai_offset_ns() -> Option<i64>;

// REQ-CLK-006 — fixed-capacity interval stats, allocation-free:
pub struct LatencyRing<const CAP: usize = 4096> { /* ring of u64 nanos */ }
pub struct IntervalStats { pub min: u64, pub max: u64, pub mean: u64,
                           pub p50: u64, pub p99: u64, pub p999: u64 }
impl<const CAP: usize> LatencyRing<CAP> {
    pub fn record(&mut self, interval_ns: u64);   // O(1); evicts oldest when full
    pub fn stats(&self) -> IntervalStats;         // exact over current window; no alloc
    pub fn len(&self) -> usize;
    pub fn reset(&mut self);
}
```

## §Requirements

### Functional

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CLK-001 | `Clock::now()` returns `Timestamp` whose `mono` field never goes backward across calls within a process, enforced by a process-wide floor even when the underlying source regresses | MUST |
| REQ-CLK-002 | `Timestamp` separates wall time (SystemTime-based under `std`, u64 Unix-epoch-nanos under core+`libc`, same `unix_nanos()` accessor on both) from monotonic u64 nanos; no API derives one from the other except an explicitly lossy labelled helper | MUST |
| REQ-CLK-003 | With feature `tsc`: x86_64 reads `rdtsc` via `core::arch::x86_64`, aarch64 reads `cntvct_el0`, each behind a calibrated ns-per-tick multiply-shift conversion, gated per target arch, falling back to `Instant` (std) / `CLOCK_MONOTONIC` (libc) when calibration or the invariant-counter check fails | MUST |
| REQ-CLK-004 | With feature `ptp`: `detect_sync_quality()` classifies the process's time quality as `Ptp` (PTP device in `/sys/class/ptp/` + coherent `CLOCK_TAI` offset), `Ntp`, or `Fallback`; detection is read-only, best-effort, and performs no daemon/sync actions | MUST |
| REQ-CLK-005 | `MockClock` advances only by explicit manual calls, is fully deterministic under single-threaded use, and supports simulated wall steps for skew tests | MUST |
| REQ-CLK-006 | `LatencyRing` reports min/max/mean/p50/p99/p99.9 at nanosecond resolution over a fixed-capacity window with **zero heap allocation** on `record` and `stats` (stack/const-capacity scratch only) | MUST |

### Traceability matrix (provisional — names fixed at implementation)

| Requirement | Planned test | Property class |
|-------------|--------------|----------------|
| REQ-CLK-001 | `mono_never_regresses_under_all_sources` (`tests/monotonic.rs`) | unit + loom (shared floor) |
| REQ-CLK-002 | `wall_and_mono_independent_no_implicit_conversion` (`tests/timestamp.rs`) | unit |
| REQ-CLK-003 | `tsc_read_matches_instant_within_tolerance` (arch-gated integration; skipped where unsupported) | integration, per-target |
| REQ-CLK-004 | `ptp_detection_classifies_synthetic_sysfs` (`tests/ptp_detect.rs`, fixture sysfs tree) | unit (std) |
| REQ-CLK-005 | `mock_advance_is_deterministic_and_step_wall_works` | unit + miri |
| REQ-CLK-006 | `interval_stats_exact_over_window_no_alloc` (proptest vs reference sort; alloc-counter harness; miri on the ring) | property + miri |

## §Out of scope

- **PTP participation** — running/orchestrating `ptp4l`/`ts2phc`, PHC control, `adjtimex` writes. REQ-CLK-004 is an indicator, not a daemon.
- NTP client functionality.
- Timestamp *distribution* between processes — that is `shm-rings` territory; clock-kit only produces `Timestamp` values.
- Calendar, timezone, or duration-arithmetic surface beyond raw nanos — `chronoshift` (L0) domain.
- `serde` support for `Timestamp` (hot-path type; conversion at the edge by consumers).

## §Gate plan

Tier A — the estate's full matrix per [README](../README.md) (build `--locked`
all-features + no-default-features, test, clippy `-D warnings` + pedantic +
`unwrap_used`/`indexing_used`/`panic` denied, fmt, cargo-deny, cargo-audit,
llvm-cov ≥ 90, semver-checks, criterion, loom, miri, cargo-vet, weekly
mutation), with these adjustments:

| Adjustment | Rationale |
|---|---|
| llvm-cov denominator **excludes arch-gated `tsc` code on non-native hosts**; dedicated per-target jobs (`x86_64`, `aarch64`) measure their own branches; residuals recorded in `COVERAGE-NOTES.md` | validkit per-config lesson: `--all-features` unions features but a single host target cannot execute foreign-arch branches — union coverage would understate |
| miri runs `LatencyRing` + `MockClock` suites (pure logic, no FFI on those paths) | mandated miri-for-the-ring; FFI/clock syscalls are out of miri scope |
| loom job covers the process-wide monotonic floor (atomic max) if implemented with lock-free atomics | Tier A concurrency-primitive gate |
| criterion baselines: `now()` cost per source (TSC vs Instant vs libc), `record()` and `stats()` cost vs CAP | latency-relevant crate → criterion is required, not optional |
| embedded gate (`thumbv7em-none-eabihf`, `--no-default-features`) run — no_std is claimed for the core modules | targets without 64-bit atomics need the critical-section floor fallback; gate catches regressions |
| no wasm32 claim in v1 → no wasm gate | TSC/CNTVCT and PTP paths are meaningless on wasm; core modules would build but the claim buys nothing |

## §Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Non-invariant or cross-socket-desynced TSC produces skewed `mono` | Silent timestamp skew between cores | CPUID invariant-TSC check before enabling TSC path; document per-socket caveat; `Clock::source()` observable; fallback on failure |
| Calibration drift over long runs (frequency drift, thermal) | Slowly-biased nanos conversion | Calibration is repeatable (`calibrate()` re-callable); drift bound documented; consumers needing hard accuracy re-calibrate periodically |
| `CLOCK_TAI` offset absent/stale → PTP misclassification | Wrong SyncQuality downstream | Classification requires *both* device presence and coherent TAI offset; anything ambiguous → `Fallback` (fail-closed to distrust) |
| `/sys/class/ptp` layout differs across kernels | Detection fragility | Parse minimally (existence + dev name), never numbers-of; malformed layout → `Fallback` |
| 32-bit targets lack `AtomicU64` for the monotonic floor | Build break on embedded | Critical-section fallback (chronoshift MockClock pattern); covered by thumbv7em gate |
| `stats()` stack scratch (CAP × 8 B) overflows small stacks | Stack smash on constrained targets | CAP is const-generic and documented; default chosen for ≥ 64 KiB stacks; no-recursion guarantee |
| Duplication with `chronoshift`'s Clock/MockClock splits estate idiom in two | Two ways to abstract time | Decision item below — resolve before implementation |

## §Cross-references

- **book-kit** (consumer): consumes raw `u64` nanos, *not* `Timestamp`, to stay estate-dep-free — see `specs/book-kit.md` §Decisions.
- **chronoshift** (L0): overlap flagged. Proposal: clock-kit re-exports/wraps chronoshift's `Clock` trait rather than minting a rival abstraction — L1→L0 edge, ceiling-legal.
- **percentile-kit** (L2): pattern donor for the fixed-capacity ring only. A dependency is **forbidden** (upward edge, layers.md rule 1); if the ring is ever shared, the shared primitive must be lifted *down* to L0, never book-kit/clock-kit pulled up.
- **shm-rings** (L1): downstream publisher of timestamps; same-layer composition legal when needed.
- **uring-kit** (future L1): sibling platform substrate.

## §Decisions flagged for owner review

1. **chronoshift relationship (blocking).** Wrap chronoshift's L0 `Clock` trait (recommended: one estate time idiom, clock-kit adds precision/quality/mock determinism) vs a parallel self-contained trait (no runtime edge, two idioms). Spec above is written self-contained so either choice is a small delta.
2. **Wall representation under core+libc (REQ-CLK-002 reading).** The mandate says "SystemTime-based"; `SystemTime` does not exist in core. Proposed: `WallTime` is SystemTime-backed under `std` and u64-epoch-nanos under core+`libc`, with `unix_nanos()` as the portable accessor. Owner to confirm this reading.
3. **Percentile semantics.** Exact-over-window (sort a bounded stack copy; proposed default) vs streaming P² approximation (O(1) memory, inexact). HFT latency gates usually want exact-over-window.
4. **Feature shape for arch gates.** Single `tsc` feature with per-arch `#[cfg(target_arch)]` internals (proposed) vs two features `tsc-x86_64`/`tsc-aarch64`. Single feature keeps `--all-features` coherent on every host.
5. **`libc` vs `std` as the no-`Instant` monotonic path** — proposed: `libc` feature exists for no_std hosts; CI measures both configurations (already in the matrix as no-default-features build).
