# hw-kit — NUMA/topology/pinning substrate (SPEC, pre-implementation)

> **Status: SPEC-ONLY.** No implementation exists or is authorized before owner
> sign-off on this file. `REQ-HW-NNN` tags are the traceability anchors the
> future implementation must cite (doc-comment tags on public items; every REQ
> maps to ≥ 1 named test).

**Layer:** L1 — substrate, **Linux-only by declaration** · **REQs:** 6 (HW-001…006) · **Deps:** `libc` only, feature-gated · **Date:** 2026-10-02

| Field | Value |
|---|---|
| Layer | **L1 — substrate** — already listed in [docs/layers.md](../docs/layers.md) as a future L1 crate ("future: `uring-kit`, `clock-kit`, `hw-kit`"); Linux/platform-scoped L1 with declared `#[cfg(target_os)]` posture is explicitly permitted by the layer definition |
| Platform gate | `#[cfg(not(target_os = "linux"))] compile_error!` — the `uring-kit` posture (REQ-HW-005) |
| Estate deps | zero |
| External deps | `libc` only (feature-gated per REQ-HW-006); topology parsing is pure `std` |
| Safety posture | unsafe surface documented per-block — every `unsafe` block carries a `SAFETY:` comment citing the invariant it relies on (REQ-HW-005) |

## §Semantics

hw-kit is the estate's thin, honest wrapper over the Linux CPU-topology and
placement facilities that HFT/ECN deployment needs: discover the machine,
pin threads, allocate NUMA-local and huge-page-backed memory. It is a
**wrapper, not a platform library**: it adds typed errors, pure-std parsing,
and fail-closed validation over raw syscalls/`sysfs` — no policy engine, no
daemon, no cgroup manipulation.

### Discovery (REQ-HW-001)

CPU topology (cores, packages/sockets, NUMA nodes, sibling/thread sets) is
parsed from `/sys/devices/system/cpu` with pure `std` code — no libnuma, no
hwloc. Parse results are structural (typed `CpuTopology`), and an
unparseable/absent entry is a typed error or an explicitly-`Option` field,
never a guessed default.

### Pinning & isolation validation (REQ-HW-002)

`sched_setaffinity` (via `libc`) pins the current thread (or a target TID) to
a caller-chosen CPU set. Isolation validation is **best-effort verification,
not enforcement**: the crate scans `/proc/*/status` `Cpus_allowed_list`
(and, when present, cgroup cpuset controllers) and reports any foreign task
whose affinity overlaps the pinned set. A clean report at time T does not
guarantee isolation at T+1 — the report is advisory and documented as such;
fail-closed means overlap *is* reported, absence of evidence is not evidence
of isolation.

### NUMA + hugepages (REQ-HW-003, REQ-HW-004)

NUMA locality is exposed as documented hooks over `mmap` + `mbind` (via
`libc`, feature `numa`): map anonymous memory, then bind it to a node set
with a stated policy. The v1 surface is the two blessed policies
(`MPOL_BIND`, `MPOL_PREFERRED`) behind safe wrappers; the raw syscall shape
is documented for everything else. Hugepages use `mmap(MAP_HUGETLB)` with
size class selection; exhaustion or unsupported configuration returns a
typed error — **there is no silent fallback to 4 KiB pages** (a silent
fallback would corrupt latency assumptions downstream).

### Platform gate (REQ-HW-005)

The crate does not exist off-Linux: `#[cfg(not(target_os = "linux"))]
compile_error!("hw-kit is Linux-only …")`. Non-Linux CI jobs run a
build-failure assertion instead of a build. All `unsafe` is surface-documented
per-block; the crate targets Tier A's pedantic stack plus
`clippy::undocumented_unsafe_blocks` and `unsafe_op_in_unsafe_fn` denied.

## §API sketch

```rust
// Linux-only, declared. Cargo.toml:
//   [package.metadata.layers] tier = "L1"
//   [features] hw-discovery = [] (default) · numa = ["libc"] · libc = ["dep:libc"]
#![cfg_attr(not(target_os = "linux"), allow(unused))] // + compile_error below
#[cfg(not(target_os = "linux"))]
compile_error!("hw-kit is Linux-only; this crate intentionally does not build elsewhere"); // REQ-HW-005

pub struct CpuId(pub u32);  pub struct NodeId(pub u32);
pub struct CpuSet { /* bitmask */ }
impl CpuSet {
    pub fn single(cpu: CpuId) -> Self;
    pub fn from_range(a: CpuId, b: CpuId) -> Self;
    pub fn insert(&mut self, cpu: CpuId);  pub fn contains(&self, cpu: CpuId) -> bool;
    pub fn allowed_list(&self) -> String;  // "0-3,8" format for logs/proc interop
}

// REQ-HW-001 — pure-std sysfs parse (feature hw-discovery, default):
pub struct CpuTopology {
    pub cpus: Vec<CpuInfo>,            // std Vec; discovery is not hot-path
    pub packages: Vec<PackageId>,
    pub numa_nodes: Vec<NodeInfo>,
}
pub struct CpuInfo { pub id: CpuId, pub package: PackageId, pub core: CoreId,
                     pub node: Option<NodeId>, pub siblings: SmallCpuList }
pub fn discover() -> std::io::Result<CpuTopology>;   // parses /sys/devices/system/cpu

// REQ-HW-002 — pinning + best-effort isolation validation:
pub fn pin_current(set: &CpuSet) -> Result<(), PinError>;       // sched_setaffinity(0, …)
pub fn pin_thread(tid: i32, set: &CpuSet) -> Result<(), PinError>;
pub fn verify_isolated(set: &CpuSet) -> Result<IsolationReport, PinError>;
pub struct IsolationReport { pub overlapping_tasks: Vec<OverlappingTask>, pub scanned_pids: usize }
// clean report ⇒ no *visible* foreign task on the set at scan time (documented advisory)

// REQ-HW-003 — NUMA hooks (feature numa; libc mmap+mbind documented, not wrapped into a policy engine):
pub struct NumaPolicy { pub nodes: NodeSet, pub mode: MpolMode } // MpolMode::{Bind, Preferred}
pub unsafe fn numa_bind_region(addr: *mut u8, len: usize, policy: &NumaPolicy) -> Result<(), NumaError>;
// safe sugar for the two blessed shapes:
pub fn alloc_on_node(len: usize, node: NodeId) -> Result<NodeRegion, NumaError>;   // mmap + mbind(MPOL_BIND)
pub struct NodeRegion { ptr: *mut u8, len: usize, node: NodeId }                    // drop = munmap

// REQ-HW-004 — hugepages:
pub struct HugeRegion { ptr: *mut u8, len: usize }                              // drop = munmap
pub fn hugepage_reserve(len: usize, size_class: HugeSize) -> Result<HugeRegion, HugetlbError>;
pub enum HugeSize { Default2M, Default1G }
// exhaustion ⇒ typed HugetlbError::Unavailable — never a silent 4 KiB fallback

// error taxonomy is exhaustive & typed across the crate: PinError, NumaError, HugetlbError
```

## §Requirements

### Functional

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-HW-001 | CPU topology discovery (cores, packages, NUMA nodes, sibling sets) is parsed from `/sys/devices/system/cpu` with pure `std` (feature `hw-discovery`), producing a typed `CpuTopology`; absent/unparseable entries are typed errors or explicit `Option`, never guessed defaults | MUST |
| REQ-HW-002 | Core pinning via `sched_setaffinity` (current thread and by-TID) plus best-effort isolation validation that reports any other task whose affinity overlaps the pinned set (scanning `/proc/*/status` `Cpus_allowed_list`, cgroup cpuset when available) | MUST |
| REQ-HW-003 | NUMA-aware allocation hooks document and expose the `mmap`+`mbind` approach via `libc` (feature `numa`), with safe wrappers for `MPOL_BIND` and `MPOL_PREFERRED` and typed errors for policy failure | MUST |
| REQ-HW-004 | Hugepage reservation helpers via `mmap(MAP_HUGETLB)` with size-class selection; exhaustion/unsupported configs return typed errors with **no silent fallback** to base pages | MUST |

### Platform & safety

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-HW-005 | The crate is Linux-only by declaration: `compile_error!` on non-Linux targets (uring-kit posture), and every `unsafe` block carries a per-block `SAFETY:` documentation comment citing the relied-upon invariant | MUST |
| REQ-HW-006 | Runtime dependency surface is `libc` only, feature-gated (`numa` → `libc`; discovery → none); topology parsing uses pure `std`; enforced by cargo-deny bans + dependency-tree assertion in CI | MUST |

### Traceability matrix (provisional — names fixed at implementation)

| Requirement | Planned test | Property class |
|-------------|--------------|----------------|
| REQ-HW-001 | `topology_parses_synthetic_sysfs` (fixture sysfs tree incl. malformed entries) | unit (pure std) |
| REQ-HW-002 | `pinning_sets_affinity_then_reports_overlap` (`tests/pinning.rs`, env-gated `HW_KIT_PIN_TEST=1`) | integration, self-hosted runner |
| REQ-HW-003 | `numa_bind_fails_closed_on_bad_policy` + doc-examples over the documented hook shape | smoke + doc (env-gated) |
| REQ-HW-004 | `hugepage_exhaustion_is_typed_no_silent_fallback` (env-gated; unavailable-hugepages host asserts the typed error) | integration |
| REQ-HW-005 | `non_linux_build_is_compile_error` (trybuild/matrix job) + `every_unsafe_block_has_safety_doc` (clippy `undocumented_unsafe_blocks` denied) | build-gate + lint |
| REQ-HW-006 | `deps_are_libc_only` (cargo-deny bans + `cargo tree` assertion in CI) | CI assertion |

## §Out of scope

- **cgroup/cpuset *manipulation*** — the crate reads affinity state; it never writes controller files or reconfigures partitions.
- IRQ affinity, network queue/RSS steering, kernel bypass (DPDK-style) tuning — deployment tooling, not a library substrate.
- A NUMA allocator *implementation* (`GlobalAlloc` swap) — hooks only; policy stays with the consumer.
- Windows/macOS/BSD support — explicitly none, ever (compile_error posture).
- libnuma/hwloc bindings — the no-external-crate mandate is a feature.
- CPU frequency governor control — clock-kit documents timing; scaling policy is out of scope.

## §Gate plan

Tier A — full estate matrix, with these adjustments (the crate is
syscall-thin and hardware-shaped; the adjustments are honest measurement
posture, not gate evasion):

| Adjustment | Rationale |
|---|---|
| Coverage: syscall/hardware-bound paths (`mbind`, `MAP_HUGETLB` success paths, TID pinning) are **env-gated integration tests** documented in `COVERAGE-NOTES.md` (ratelimit live-Redis pattern); host CI measures the parse/validate/error taxonomy at full floor; hardware tests run on a self-hosted runner job (non-blocking until a runner is provisioned — decision item) | a syscall wrapper cannot execute `mbind` on shared CI; documented env-bound exceptions are the established estate pattern |
| miri **n/a** — recorded rationale: the crate's logic is FFI into real syscalls, which miri cannot execute; pure-std sysfs parsing *is* miri-eligible and runs | miri/FFI boundary; keeps the miri gate where it means something |
| loom **n/a** — no lock-free shared-memory primitives (rationale recorded, like wire-kit) | gate applicability, not omission by neglect |
| **Failure-path coverage is a hard gate**: every typed error arm (`PinError`, `NumaError`, `HugetlbError`) must be exercised by at least one always-runnable test (bad args → typed error, fail-closed) — the "guaranteed-refused endpoint" doctrine applied to syscalls | fail-closed pins without infra |
| Lints: Tier A stack + `clippy::undocumented_unsafe_blocks` + `unsafe_op_in_unsafe_fn` denied crate-wide; `SAFETY:` comments audited in review | REQ-HW-005 is a lint-enforceable contract |
| criterion: **optional** (topology discovery and pinning are one-shot operations, not per-message hot paths) — deviation from the Tier A latency-relevant default recorded | criterion applies to "latency-relevant" crates; this crate's hot path is the consumer's memory, not its API |
| Platform matrix: Linux (gnu + musl) build/test; non-Linux jobs run the build-**failure** assertion | REQ-HW-005 gate shape |
| no_std/wasm/thumbv7em: not applicable — std + Linux-only by declaration | consistent with layers.md platform-scoped L1 |

## §Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| `/sys` layout drift across kernel versions breaks discovery | Parse errors in the field | Minimal structural parsing, per-field `Option`/typed error, fixture-tree unit tests incl. malformed inputs; discovery is pure std so fixes are safe and reviewable |
| Isolation validation raced: task migrates onto the set after the scan | False "isolated" report | Documented as best-effort advisory (semantics section); report includes scan timestamp/pid count; API name and docs say "report", not "guarantee" |
| cgroup v2 (`cpuset.cpus`) restricts affinity below what sysfs suggests | Pinning "succeeds" but placement is wrong | Check effective affinity via `sched_getaffinity` post-pin; surface mismatch as typed warning/error |
| `mbind` policy misuse (node mask vs mode mismatch) | Silent wrong-node allocation or `EIO` | Only the two blessed policies are safe-wrapped; raw hook documented per-block; typed errors surfaced, never swallowed |
| Silent hugepage fallback to 4 KiB | Latency cliffs masquerade as success | Mandated fail-closed (REQ-HW-004): typed `HugetlbError::Unavailable`; tests pin the no-fallback property |
| Pinning a foreign TID races with task exit | `ESRCH` handled inconsistently | Typed error mapping for `ESRCH`/`EINVAL`/`EPERM`; doc-examples pin behavior |
| Unsafe-surface bugs (mmap/munmap lifetimes, pointer provenance) | UB in the estate's lowest layer | `SAFETY:` per-block docs (lint-denied), `NodeRegion`/`HugeRegion` own their mappings (RAII drop = munmap), review checklist item; miri n/a so review + fail-closed tests carry the weight |
| docs.rs builds on non-Linux targets fail | Broken docs | docs.rs builds on Linux (x86_64-unknown-linux-gnu) — verify in CI; `compile_error` gate exercised in the platform matrix, not left to chance |
| Non-blocking hardware-runner job silently never runs | Hardware paths rot uncovered | Decision item: provisioning the self-hosted runner is a pre-publication acceptance criterion, tracked as an issue at implementation |

## §Cross-references

- **Standalone** — zero estate deps; `libc` is its only external edge (REQ-HW-006).
- **uring-kit** (future L1): the `compile_error!` Linux-only posture is borrowed directly (REQ-HW-005); the two crates are natural siblings in kernel-bypass stacks.
- **clock-kit** (L1, sibling): consumers pin cores *then* measure with clock-kit; no shared types — composition happens at the application layer.
- **book-kit / wire-kit** (L1, siblings): hw-kit provides the placement substrate they run on; no dependency edges by design.
- **COVERAGE-NOTES.md doctrine** (estate-wide, see [COVERAGE.md](../COVERAGE.md) ratelimit/validkit entries): the env-gated hardware-path exception posture.

## §Decisions flagged for owner review

1. **Tier A vs Tier B.** Tier A proposed with the documented env-bound coverage exceptions and fail-closed error-path gate; Tier B (≥80) would remove the exception paperwork but reads as under-testing a wrapper this thin. Owner call.
2. **Self-hosted hardware runner.** Required for NUMA/hugepage/pinning *success*-path evidence; proposed as a pre-publication acceptance criterion with the job non-blocking until provisioned. Is that acceptable, or does publication wait for the runner?
3. **NUMA surface shape.** Raw `unsafe` hook + two safe policy wrappers (proposed) vs full safe `MpolMode` enumeration (wrap all policies). More surface = more unsafe audit; the proposal keeps the audit small and the escape hatch documented.
4. **Isolation scan depth.** `/proc`-only in v1 (proposed) vs cgroup cpuset integration in v1. The latter is more truthful under containerized deployment but adds controller-file parsing and edge cases; the semantics section already fails closed either way.
5. **std containers in `CpuTopology`.** `Vec`-based discovery types (proposed — discovery is cold-path) vs fixed-capacity arrays for a `no_alloc` claim. Affects nothing downstream as long as the parse stays pure std.
