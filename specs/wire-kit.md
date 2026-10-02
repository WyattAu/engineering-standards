# wire-kit — zero-copy binary wire codecs (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file. `REQ-WIRE-NNN` tags are the traceability anchors the
> future implementation must cite (doc-comment tags on public items; every REQ
> maps to ≥ 1 named test).

**Layer:** L1 — substrate · **REQs:** 7 (WIRE-001…007) · **Estate deps:** none — fully standalone · **External deps:** none mandatory (`simd` is `core::arch` feature-gated) · **Date:** 2026-10-02

| Field | Value |
|---|---|
| Layer | **L1 — substrate** (new registration: `docs/layers.md` table + `scripts/estate-tiers.json` entry due at repo creation; manifest carries `tier = "L1"`) |
| Estate deps | **zero**, by design and by mandate — this is the estate's edge-format leaf for exchange protocols |
| External deps | none. Endianness via `u16/u32/u64::from_le_bytes`/`from_be_bytes` — **no `byteorder`**. SIMD via `core::arch` behind feature `simd`. |
| no_std | core-only lib; nothing in the decode/encode hot path needs alloc or std |
| Codec scope | SBE (FIX SBE, fixed-width blocks + repeating groups + data fields) and FIX 4.4 tag=value |

## §Semantics

wire-kit reads and writes exchange wire formats **in place**: a decoder is a
set of lifetime-bound accessor structs over `&[u8]` (and `&mut [u8]` for the
encoder) — decode touches nothing, allocates nothing, copies nothing
(REQ-WIRE-001, REQ-WIRE-005). One buffer in, typed views out; the views die
with the borrow and can never outlive the buffer.

### Totality (REQ-WIRE-003)

Every decoder is **total**: malformed, truncated, hostile input produces a
typed error (`WireError`) — never a panic, never an out-of-bounds read, never
a `usize` cast that wraps on 32-bit. Bounds are checked at every field
access, which makes the accessors safe Rust over a single `unsafe`-free or
minimal-`unsafe` core. Every decoder gets a fuzz target; fuzzing is part of
the gate, not an afterthought.

### Endianness (REQ-WIRE-004)

Endianness is explicit **per message block**, not a crate-global setting: SBE
schema blocks declare big- or little-endian fields (SBE's `bigEndian` flag),
FIX 4.4 is ASCII tag=value and has none. Conversion uses
`from_le_bytes`/`from_be_bytes` exclusively — byteorder-free by mandate.

### SIMD scanning (REQ-WIRE-006)

Field scanning (FIX `0x01` delimiter search, checksum accumulation windows)
uses SIMD where the target provides it (SSE2/AVX2 on x86_64 via
`core::arch::x86_64`), with a SWAR/scalar reference implementation that is
**always compiled** and used as the differential oracle. The `simd-tokenizer`
pattern: feature-gated intrinsic fast path, identical-results property vs the
scalar reference. Runtime feature detection requires `std`; no_std builds use
the scalar path (or compile-time `target-feature` selection, documented).

### Schema-driven corpus (REQ-WIRE-007)

Golden test corpora for SBE are **generated** from schema descriptions, not
hand-written: a deterministic generator (no `rand`; fixed seeds / LCG only)
emits encoded frames + expected accessor values from the schema. CI
regenerates and diffs — a generator or codec change that alters output bytes
without a deliberate golden update fails the build. This is test-support
only: wire-kit does not ship an SBE schema codegen (see §Decisions).

## §API sketch

```rust
#![no_std]                     // core-only; `std` feature only for runtime SIMD detection
// features: std (optional, for is_x86_feature_detected) · simd (core::arch fast paths)

pub enum WireError {                                           // REQ-WIRE-003 — typed, exhaustive
    InsufficientBytes { need: usize, have: usize },
    InvalidTag(u16),                                           // FIX unknown/illegal tag position
    BadChecksum { got: u8, want: u8 },                         // FIX tag 10
    InvalidEnum { enum_id: u16, raw: i64 },                    // SBE enum field out of range
    InvalidGroupCount { tag: u16, claimed: usize, remaining: usize },
    UnsupportedSchemaVersion { schema_id: u16, got: u16, max: u16 },
}

// ---- SBE (REQ-WIRE-001) -------------------------------------------------
pub struct SbeHeader;                                          // fixed-width message header:
impl SbeHeader {                                               // block_len, template_id,
    pub fn decode(buf: &[u8]) -> Result<Decoded<'_, HeaderView>, WireError>;  // schema_id, version
}
pub struct HeaderView<'a> { pub block_len: u16, pub template_id: u16,
                            pub schema_id: u16, pub version: u16, pub buf: &'a [u8] }

pub struct MdIncrementalRefresh<'a> { buf: &'a [u8], off: usize }  // example accessor block
impl<'a> MdIncrementalRefresh<'a> {
    pub fn transact_time(&self) -> Result<u64, WireError>;             // fixed field
    pub fn md_entries(&self) -> Result<GroupIter<'a, MdEntry<'a>>, WireError>; // repeating group
    pub fn text_field(&self) -> Result<DataField<'a>, WireError>;      // data field: len + bytes
}
pub struct GroupIter<'a, T> { /* … */ }
impl<'a, T: GroupBlock<'a>> Iterator for GroupIter<'a, T> {
    type Item = Result<T, WireError>;                  // per-entry bounds check, total
}
pub struct Encoder<'a> { buf: &'a mut [u8], pos: usize }
impl<'a> Encoder<'a> {
    pub fn write_header(&mut self, template: Template, endianness: Endianness) -> Result<(), WireError>;
    pub fn write_field_i64(&mut self, v: i64, endianness: Endianness) -> Result<(), WireError>; // REQ-WIRE-004
    pub fn open_group(&mut self, num_count_tag: u16) -> Result<GroupWriter<'_, 'a>, WireError>;
}

// ---- FIX 4.4 (REQ-WIRE-002) ---------------------------------------------
pub struct FixMessage<'a> { buf: &'a [u8] }
impl<'a> FixMessage<'a> {
    pub fn parse(buf: &'a [u8]) -> Result<Self, WireError>;      // header/tag structure + checksum
    pub fn field(&self, tag: u16) -> Option<&'a [u8]>;           // in-place, zero-copy
    pub fn group(&self, leading_tag: u16) -> Result<FixGroup<'a>, WireError>; // declared repeating groups
    pub fn verify_checksum(&self) -> Result<(), WireError>;      // tag 10, sum mod 256
    pub fn iter(&self) -> FixFieldIter<'a>;                      // flat tag=value scan (SOH-delimited)
}
pub fn fix_checksum(body: &[u8]) -> u8;                          // pub for cross-verification

// ---- scanning (REQ-WIRE-006) ---------------------------------------------
pub fn find_soh(buf: &[u8]) -> Option<usize>;     // scalar/SWAR reference — always compiled
#[cfg(feature = "simd")] pub fn find_soh_simd(buf: &[u8]) -> Option<usize>; // core::arch gated
```

## §Requirements

### Functional

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-WIRE-001 | SBE block encoding/decoding covers fixed-width message headers, repeating groups, and data fields, as hand-rolled reader/writer over `&[u8]` — decode produces lifetime-bound accessor structs over the buffer with zero allocation and zero copying | MUST |
| REQ-WIRE-002 | FIX 4.4 tag=value codec encodes and decodes messages, verifies/computes the tag-10 checksum, exposes declared repeating groups, and provides in-place (zero-copy) field access | MUST |
| REQ-WIRE-004 | Endianness is explicit per message block: SBE fields honor the block's declared byte order (big/little), FIX is ASCII; all integer conversion uses `from_le_bytes`/`from_be_bytes` (no byteorder dependency) | MUST |
| REQ-WIRE-005 | Zero-copy read accessors are lifetime-bound to the input buffer (`Decoder<'a>`/`*View<'a>`), making dangling or outliving views unrepresentable in safe code | MUST |
| REQ-WIRE-006 | With feature `simd`: field scanning uses `core::arch` intrinsics where available (per-arch `#[cfg]`), with a scalar/SWAR fallback that is always compiled and produces identical results | MUST |
| REQ-WIRE-007 | SBE test corpora are generated deterministically (seeded, no `rand`) from schema descriptions, with byte-identical regeneration enforced in CI | MUST |

### Robustness (security-relevant)

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-WIRE-003 | All decoding is bounds-checked and total: every malformed input yields a typed `WireError` (`InsufficientBytes`, `InvalidTag`, `BadChecksum`, `InvalidEnum`, …); no decoder panics, wraps, or reads out of bounds, and every decoder has a cargo-fuzz target | MUST |

### Traceability matrix (provisional — names fixed at implementation)

| Requirement | Planned test | Property class |
|-------------|--------------|----------------|
| REQ-WIRE-001 | `sbe_roundtrip_header_group_datafield` (`tests/sbe.rs`) | property (proptest roundtrip) |
| REQ-WIRE-002 | `fix_checksum_groups_and_inplace_fields` (`tests/fix.rs`) | unit + golden vectors |
| REQ-WIRE-003 | `fuzz_<decoder>` × every decoder (`fuzz/`), CI smoke run over seeded corpus | fuzz + miri (alignment/UB) |
| REQ-WIRE-004 | `endianness_explicit_per_block` (golden big- and little-endian frames both decoded) | unit |
| REQ-WIRE-005 | `views_borrow_not_own` (compile-fail trybuild: view outlives buffer) | compile + unit |
| REQ-WIRE-006 | `simd_scan_matches_scalar_oracle` (differential property, both feature states; also under `--no-default-features`) | property |
| REQ-WIRE-007 | `corpus_regeneration_is_byte_identical` (CI regen-diff) | determinism gate |

## §Out of scope

- **SBE schema codegen** — wire-kit hand-rolls codecs over raw buffers per the mandate; reading `.xml` SBE schemas and emitting Rust structs (Firmament/realign-style plugins) is future work or an out-of-crate tool. REQ-WIRE-007 uses schemas only for *test corpus* generation.
- FIX session layer — logon/heartbeat/sequence-number state machines, resend logic. This is the FIX 4.4 *presentation* codec only.
- Encryption/authorization (FIX 4.4 no-encryption framing only).
- Any transport (TCP/UDS/multicast) — consumers wire decoders into their own I/O.
- `serde` bridges; JSON conversion of wire messages is an edge-tool concern.
- New protocol definitions (the estate's own binary formats live in `suture-protocol`/`vane-proto` land, not here).

## §Gate plan

Tier A — full estate matrix, with these adjustments:

| Adjustment | Rationale |
|---|---|
| **Fuzz targets are a blocking gate artifact**: one cargo-fuzz target per decoder, run in CI as a bounded smoke fuzz (fixed time budget) over the committed seeded corpus; full-budget fuzzing scheduled off-peak | REQ-WIRE-003 is the crate's security contract; smoke fuzz catches regressions, nightly budget hunts |
| `simd`-gated code measured **per-config** (`--features simd` on a host with AVX2; `--no-default-features` scalar suite), SIMD branches excluded from the union-coverage denominator and documented in `COVERAGE-NOTES.md` | validkit per-config methodology: `--all-features` unions cannot execute non-native intrinsic paths |
| Tier A lint stack applies with force: `indexing_used`/`unwrap_used`/`panic` denied push decoders toward `get()`+typed errors — this is exactly REQ-WIRE-003 expressed as lints | decoders are the estate's canonical "never panics on input" surface |
| miri over encode/decode suites (catches misaligned/UB in any `unsafe` fast path); loom **n/a** (no shared-memory concurrency primitives — rationale recorded) | miri/loom applicability split |
| criterion: FIX `find_soh` scalar vs simd GB/s, SBE decode of representative market-data frame ns/op | latency-relevant Tier A |
| no wasm claim in v1 (SIMD paths are arch-gated; scalar would build, but the claim buys nothing) → no wasm gate; `#![no_std]` is claimed → thumbv7em `--no-default-features` gate runs | README embedded-gate rule: gate runs when no_std is claimed |
| corpus regen-diff test is part of the standard `test` gate | REQ-WIRE-007 determinism enforcement |

## §Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Panic path survives in a decoder (indexing, unwrap, cast overflow) | Remote crash on hostile feed | Tier A lint denial (`panic`/`indexing_used`/`unwrap_used`) + fuzz targets + miri; decoders are total by construction |
| Misaligned reads via `unsafe` fast path | UB, only visible on some targets | `read_unaligned` only, or `from_*_bytes` on slices; miri catches; fuzz corpus includes odd-offset frames |
| SIMD and scalar paths diverge on edge inputs | Two decoders, two truths | Scalar oracle is the reference; differential property test (REQ-WIRE-006) runs in both configs; SIMD path is behind a feature that default builds omit |
| FIX repeating-group parsing ambiguity (nested groups, order-dependent delimiters) | Silent misparse of real feeds | v1 supports single-level declared groups; nested groups are typed errors (`InvalidGroupCount`) until spec'd — flagged decision; fuzz targets include group-fuzzing grammars |
| Tag-10 checksum is sum-mod-256 — trivially weak | False sense of integrity | Documented as transport-integrity check only, never tamper protection; spec says so explicitly |
| SBE schema/version drift vs real exchanges (schema_id/version mismatch) | Decoder accepts wrong-version frames | Header carries schema_id+version; `UnsupportedSchemaVersion` typed error; per-block endianness honored (REQ-WIRE-004) |
| Corpus generator drift hides encoder changes | Golden rot | CI regen-diff (REQ-WIRE-007): any byte change without a reviewed golden update fails |
| Scope creep into full FIX engine or SBE codegen | Layer confusion, review blowup | Out-of-scope list; codegen explicitly deferred as a decision item |

## §Cross-references

- **Standalone by mandate**: no estate-internal deps; consumers (feed handlers, book builders) bring the buffers.
- **simd-tokenizer** (L0): pattern donor for feature-gated SIMD + scalar oracle (SWAR reference idiom); no dependency edge.
- **book-kit** (L1, sibling substrate): natural consumer pair — wire-kit decodes frames, book-kit applies commands; deliberately *no* shared types (book-kit takes raw `(seq, Command)`), keeping both crates independently usable.
- **shm-rings** (L1): zero-copy decoders over ring buffers are the intended composition shape (decode in place over the shared-memory region).

## §Decisions flagged for owner review

1. **SBE coverage strategy.** v1 ships generic block/group/data-field primitives plus hand-written accessor blocks for the message set the estate needs (mandated "hand-rolled"); full schema→Rust codegen is explicitly future/adjacent work. Owner to confirm the v1 message-set scope (e.g. CME MDP3 subset as the reference corpus).
2. **Nested FIX groups.** Single-level groups in v1 with typed errors on nesting (proposed) vs full nested-group support up front. FIX 4.4 has real nested groups (e.g. NestedParties); deferring is honest but must be a documented limitation.
3. **SIMD selection: runtime vs compile-time.** Proposed: `std` feature enables `is_x86_feature_detected` runtime dispatch; no_std builds get scalar (or `target-feature`-driven compile-time selection). Alternative: compile-time only (one true path per build).
4. **wasm claim deferred** — scalar core would build on wasm32, but v1 makes no claim; activating the wasm gate costs CI and buys nothing today.
5. **Error taxonomy naming** — `WireError` proposed as the single crate-level error; alternative is per-codec error enums (`SbeError`/`FixError`) if owner prefers finer granularity at the cost of cross-codec match arms.
