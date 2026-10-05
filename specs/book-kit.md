# book-kit — lock-free order book substrate (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file. `REQ-BOOK-NNN` tags are the traceability anchors the
> future implementation must cite (doc-comment tags on public items; every REQ
> maps to ≥ 1 named test).

**Layer:** L1 — substrate · **REQs:** 10 (BOOK-001…010) · **Estate deps:** none at v1 (clock-kit edge considered and *rejected* — see §Decisions) · **Scope:** the BOOK, not the engine · **Date:** 2026-10-02

| Field | Value |
|---|---|
| Layer | **L1 — substrate** (new registration: `docs/layers.md` table + `scripts/estate-tiers.json` entry due at repo creation; manifest carries `tier = "L1"`) |
| Estate deps | **zero** at v1. Arenas re-implement the `slab-pool` (L1) pattern locally; the seqlock follows the `shm-rings` (L1) ordering standard; the ring re-implements the `percentile-kit` (L2) pattern — none of these are edges. |
| External deps | none mandatory. `alloc`-optional. No rand, no serde. |
| Concurrency model | single writer (the matching/feed thread), many lock-free readers |
| Layer note | zero estate deps + core-only internals would satisfy L0's letter; L1 declared per the `slab-pool` precedent ("lift only, never lower") — flagged in §Decisions |

## §Semantics

book-kit maintains a price-time-priority limit order book with two
synchronized views: **L2** — quantity aggregated per price level — and **L3**
— the FIFO of individual orders within each level (REQ-BOOK-001). It is the
state substrate *under* a matching engine or feed handler, not one: it applies
typed lifecycle commands (add/cancel/replace/execute) and publishes
consistent reads (REQ-BOOK-003). Matching logic, order routing, and
persistence are out of scope.

### Concurrency model (REQ-BOOK-002)

One writer thread mutates the book. Readers never take locks: each read
obtains a **version-consistent snapshot** through a seqlock protocol (the
writer bumps an odd/even sequence counter around each mutation; a reader that
observes an odd counter or a changed post-read counter retries). Livelocked
readers are a documented possibility under a hot writer, so `try_read`
(single attempt) and `read` (bounded retry + spin hint) are both exposed and
the retry bound is caller-visible. The protocol, including the acquire/release
ordering matrix, follows the `shm-rings` estate standard (REQ-BOOK-007) so
review and loom evidence transfer between the two crates. An epoch-based
variant remains the designated alternative if retry costs measure poorly
(§Decisions).

### Numeric discipline (REQ-BOOK-004)

Prices are `i64` ticks; quantities are `u64` fixed-point units. **No `f64`
exists on the hot path** — not in keys, comparisons, quantities, or checksums.
Float conversion is an edge concern for presentation layers only, and the
crate ships no such conversion.

### Side typing (REQ-BOOK-005)

Bid/Ask are distinct types, never `bool`. Unit structs `Bid`/`Ask` implement a
sealed `Side` trait; side-specific views (`SideView<Bid>`) are lifetime-bound
and API-distinct, so `book.bids()` and `book.asks()` cannot be swapped at
compile time.

### Memory discipline (REQ-BOOK-008)

All orders live in a pre-allocated slab arena addressed by **generational
indices** (slot + generation counter), the `slab-pool` pattern: a freed and
reused slot invalidates stale indices because the generation no longer
matches, killing ABA hazards. `add`/`cancel`/`replace`/`execute` perform zero
heap allocation. Price-level storage is an implementation choice bounded by
the complexity contract of REQ-BOOK-006 (best bid/ask in O(1); depth
iteration best→worst without allocation).

### Determinism (REQ-BOOK-009, REQ-BOOK-010)

Replay rebuilds a book from an ordered command feed (trade/journal events)
and is deterministic: identical feed → checksum-identical state. The checksum
is an integer-only, non-cryptographic integrity hash over the full book state
(levels, quantities, order FIFOs, version) used for snapshot verification and
replay equivalence checks.

## §API sketch

```rust
#![cfg_attr(not(feature = "alloc"), no_std)] // core-only hot path; `alloc` feature = convenience constructors
// features: alloc (optional)

pub type Price = i64;      // REQ-BOOK-004: ticks. No f64 anywhere on the hot path.
pub type Qty = u64;        // fixed-point quantity units

#[derive(Clone, Copy, PartialEq, Eq, Hash)] pub struct OrderId(u64);
pub struct GenIndex { slot: u32, gen: u32 }                    // REQ-BOOK-008 arena handle

pub struct Bid;  pub struct Ask;                               // REQ-BOOK-005
pub sealed trait Side { fn opposite() -> Self; /* … */ }
impl Side for Bid {}
impl Side for Ask {}

pub enum Command {                                             // REQ-BOOK-003 — side carried by
                                                               // distinct variants, never bool
    AddBid { id: OrderId, price: Price, qty: Qty, ts_mono: u64 },
    AddAsk { id: OrderId, price: Price, qty: Qty, ts_mono: u64 },
    Cancel { id: OrderId },
    Replace{ id: OrderId, new_price: Price, new_qty: Qty },
    Execute{ id: OrderId, qty: Qty },                          // apply a fill; NOT matching
}
pub enum Reject { UnknownOrder, DuplicateId, ZeroQty, NonPositivePrice,
                  ArenaFull, StaleGeneration }                 // typed, exhaustive

pub struct Book { /* seqlock header + arenas */ }
impl Book {
    pub fn with_arena(orders: OrderArena, levels: LevelArena) -> Self;   // caller-provided memory
    #[cfg(feature = "alloc")] pub fn with_capacity(max_orders: usize, max_levels: usize) -> Self;

    // ---- writer path (single thread; zero-alloc) ---- REQ-BOOK-008
    pub fn apply(&mut self, cmd: Command) -> Result<Applied, Reject>;
    pub fn version(&self) -> u64;

    // ---- reader path (lock-free, consistent) ---- REQ-BOOK-002
    pub fn try_read(&self, out: &mut BookBuf) -> Result<u64, Torn>;      // one attempt → version
    pub fn read(&self, out: &mut BookBuf, max_spins: u32) -> Result<u64, Torn>;
    pub fn bids(&self, buf: &BookBuf) -> SideView<'_, Bid>;
    pub fn asks(&self, buf: &BookBuf) -> SideView<'_, Ask>;
}

pub struct BookBuf { /* reader-owned scratch: depth array + top-of-book order ids */ }

pub struct SideView<'a, S: Side> { /* … */ }                   // REQ-BOOK-005 lifetime-bound
impl<'a, S: Side> SideView<'a, S> {
    pub fn best(&self) -> Option<LevelView<'a, S>>;            // REQ-BOOK-006 O(1)
    pub fn depth(&self) -> DepthIter<'a, S>;                   // best→worst price levels
    pub fn total_qty(&self) -> Qty;
}
impl<'a, S: Side> LevelView<'a, S> {
    pub fn price(&self) -> Price;  pub fn qty(&self) -> Qty;   // L2 aggregate
    pub fn orders(&self) -> impl Iterator<Item = OrderRef<'a>>;// L3 FIFO (REQ-BOOK-001)
}

// REQ-BOOK-009 — replay/journal
pub fn replay<I>(book: &mut Book, feed: I, policy: GapPolicy) -> Result<ReplayReport, ReplayError>
where I: IntoIterator<Item = (u64 /*seq*/, Command)>;
pub enum GapPolicy { Fail, Skip }                              // sequence-gap handling, explicit

// REQ-BOOK-010 — snapshot verification
impl Book { pub fn checksum(&self) -> u64; }                   // integer-only FNV-1a-64 over full state
```

## §Requirements

### Functional

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-BOOK-001 | The book maintains price-time priority with an aggregated-per-price-level (L2) view and an order-by-order (L3) view, and the two views are mutually consistent at any version | MUST |
| REQ-BOOK-003 | Commands add/cancel/replace/execute mutate the book and every failure mode returns a typed `Reject` variant — no panics, no silent drops | MUST |
| REQ-BOOK-004 | Prices are `i64` ticks and quantities `u64`; the public hot-path API contains no `f64` (float conversion exists only at consumer edges, outside this crate) | MUST |
| REQ-BOOK-005 | Bid/Ask are distinct types behind a sealed `Side` trait; no public API accepts `bool` for side | MUST |
| REQ-BOOK-006 | Best bid and best ask are O(1); depth iteration yields price levels best→worst without heap allocation | MUST |
| REQ-BOOK-009 | `replay` rebuilds book state from an ordered command feed deterministically: identical feed → checksum-identical state; sequence gaps handled by explicit `GapPolicy` | MUST |
| REQ-BOOK-010 | `checksum()` is a deterministic, integer-only hash over full book state (levels, quantities, order FIFOs, version) that changes whenever observable state changes | MUST |

### Concurrency & memory

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-BOOK-002 | Reads take no locks: every reader obtains a version-consistent snapshot via the seqlock (or epoch) protocol; torn reads are detected and reported (`Torn`), never observed | MUST |
| REQ-BOOK-007 | The reader protocol (sequence counter ordering matrix) is verified under loom and follows the `shm-rings` estate ordering standard, so the two crates' memory-ordering evidence is interchangeable | MUST |
| REQ-BOOK-008 | `add`/`cancel`/`replace`/`execute` perform zero heap allocation; orders live in pre-allocated arenas addressed by generational indices (slab-pool pattern) that defeat ABA reuse hazards | MUST |

### Traceability matrix (provisional — names fixed at implementation)

| Requirement | Planned test | Property class |
|-------------|--------------|----------------|
| REQ-BOOK-001 | `l2_aggregation_equals_l3_summation` (`tests/views.rs`) | property |
| REQ-BOOK-002 | `reader_never_sees_torn_state_under_hot_writer` (`tests/seqlock_soak.rs`) + loom model | soak + loom |
| REQ-BOOK-003 | `every_lifecycle_rejection_is_typed` (table-driven) | unit |
| REQ-BOOK-004 | `price_is_i64_no_f64_in_hot_api` (type-level + API surface lint/test) | unit |
| REQ-BOOK-005 | `sides_are_distinct_types_not_bool` (compile-time + unit) | unit |
| REQ-BOOK-006 | `best_is_o1_depth_iter_is_ordered_no_alloc` | property + alloc-counter |
| REQ-BOOK-007 | `loom_seqlock_matches_shm_rings_matrix` (`tests/loom/…`, `--cfg loom`) | loom |
| REQ-BOOK-008 | `apply_paths_zero_alloc` (global alloc-counting harness) + `stale_generation_index_rejected` (ABA) | unit + miri |
| REQ-BOOK-009 | `replay_is_deterministic_and_gap_policy_honored` | property |
| REQ-BOOK-010 | `checksum_detects_any_state_delta` (mutation-style probes; replay equivalence) | property |

## §Out of scope

- **Matching** — no crossing logic, no order admission policy, no self-trade prevention. `Execute` applies a fill to resting quantity; deciding *which* orders fill is the engine's job.
- Networking, feed parsers, and wire decoders — `wire-kit` / transport crates.
- Persistence (journal *format* on disk) — book-kit consumes an in-memory command iterator; file formats live elsewhere.
- Historical/interval book analytics — consumers build on `SideView`/snapshots.
- Serialization of `Book` (serde or otherwise).

## §Gate plan

Tier A — full estate matrix, with these adjustments:

| Adjustment | Rationale |
|---|---|
| **loom is the headline gate**: dedicated `--cfg loom` job over the seqlock protocol, arena reuse, and generation counters; loom-cfg'd shims excluded from mutation-testing globs (`mutants.toml`, breaker precedent) with the loom harness named as the covering evidence | Tier A concurrency-primitive gate; this crate's core risk *is* the lock-free protocol |
| miri runs arena, generation/ABA, replay, and checksum suites (non-atomic pure logic). Miri does **not** arbitrate the concurrent seqlock itself — that is loom's job (data-race detection at the protocol level) | miri + loom division of labor per MUTATION.md policy 4 |
| Coverage floor: loom/`cfg(loom)` branches excluded from the host-coverage denominator via `COVERAGE-NOTES.md` documentation (covered by the loom job, not the host suite) | MUTATION.md cfg-unviable doctrine applied to coverage |
| alloc-counter harness (`#[global_allocator]` counting wrapper) is a required test utility, not optional polish | REQ-BOOK-008 is unenforceable by compiler alone |
| criterion baselines: `apply(Add|Cancel|Execute)` ns/op, `read()` snapshot ns/op vs writer contention level | latency-relevant Tier A |
| no wasm/thumbv7em claim in v1 → embedded/wasm gates not run | `no_std` posture is core-only *internals*; the crate targets Linux HFT hosts and the claim is deferred (u64 atomics assumed). Revisit before any no_std announcement |
| fuzz: one target over `replay` input streams (malformed sequence gaps, duplicate ids) | feed-facing ingress deserves fuzz discipline; full fuzz matrix remains wire-kit's burden |

## §Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Seqlock reader livelock/starvation under a hot writer | Reader makes no progress | Bounded-retry `read()` + `try_read()`; documented backoff policy; criterion contention benches make degradation visible |
| Memory-ordering bug (missing acquire/release) ships | Torn state observed in production | loom verification is a blocking gate (REQ-BOOK-007); ordering matrix textually shared with shm-rings for cross-review |
| Snapshot buffer undersized for deep books | Truncated depth read | `BookBuf` capacity is explicit; truncation returns typed error/flag, never silent partial state |
| Generation-counter wrap (u32) after ~2³² reuses | ABA resurrected | Document wrap bound; optional u64 generation feature for ultra-long-running processes; replay test drives reuse cycles |
| Caller mutates from two threads | Data race (UB) — protocol violated | `&mut self` writer API makes misuse a compile error; reader API takes `&self` only; document the contract loudly |
| Checksum collisions hide state divergence | False "verified" snapshots | Non-cryptographic checksum is documented as integrity *detection*, not adversarial protection; FNV-1a-64 choice flagged for owner review (cryptkit L0 edge is legal if owner wants stronger hashing) |
| Replay depends on out-of-crate event ordering conventions | "Deterministic" only per undocumented assumption | Feed is a total-ordered `(seq, Command)` iterator; gap semantics explicit via `GapPolicy`; determinism property test is the contract |
| Scope creep toward a matching engine | Review burden, wrong layer | Out-of-scope list above is part of the spec; PRs touching crossing logic rejected at review |

## §Cross-references

- **clock-kit** (L1): *considered and rejected* for v1 — commands carry raw `u64` nanos (`ts_mono`) so book-kit keeps zero estate deps and stays freely reusable; a clock-kit edge stays legal (same-layer) if the owner overturns. Decided per the task mandate to "prefer raw u64 nanos … decide and document".
- **slab-pool** (L1): pattern donor (generational indices). Same-layer dep would be legal; v1 re-implements locally to stay dep-free — flagged.
- **shm-rings** (L1): ordering-standard donor (REQ-BOOK-007); natural downstream publisher of book deltas.
- **percentile-kit** (L2): ring-pattern donor only; dependency forbidden (upward edge).
- **cryptkit** (L0): optional stronger-hash donor for REQ-BOOK-010 if FNV-1a is judged too weak.

## §Decisions flagged for owner review

1. **clock-kit edge: rejected for v1 (raw `u64` nanos).** Book stays estate-dep-free; timestamp *semantics* live with the producer. Overturnable at review.
2. **Seqlock vs epoch.** Seqlock chosen (simpler header, matches shm-rings discipline); epoch scheme is the named fallback if contention benches show reader starvation. REQ-BOOK-002 wording admits both so the swap is not a spec break.
3. **Layer declaration L1 despite L0-eligible dependency graph** — `slab-pool` precedent (substrate infra, "lift only, never lower"); keeps future same-layer composition (clock-kit, shm-rings) open.
4. **L3 storage shape** — per-level intrusive FIFO inside one slab arena (proposed) vs flat order array with per-level lists. Complexity contract (REQ-BOOK-006) is fixed; internal layout is free until benches decide.
5. **Checksum primitive** — dependency-free FNV-1a-64 (proposed) vs cryptkit (L0) edge. Non-cryptographic status must be documented either way.
6. **`no_std` claim deferred** — internals are core-only but the v1 target is Linux hosts; announcing `no_std` support would activate embedded gates prematurely.
