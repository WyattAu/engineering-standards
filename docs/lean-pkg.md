# LEAN-PKG: Lean proof packages (packaging, rigor, reuse)

> **Status: PROPOSED (v0.1.0, 2026-11-23).** Established when the estate
> extracted `clawdius-spec` from `clawdius` and unified the toolchain
> baseline at v4.35.0 (game-spec, clawdius-spec).

| Field | Value |
|---|---|
| Owner | WyattAu/engineering-standards |
| Tiers | all |
| Oracle | `scripts/check-lean-pkg.py` |

## The rule

Every Lean proof in the estate lives in a Lake package that follows this
standard, so proofs are reusable the way crates are: one implementation,
many consumers, pinned claims.

## The failure this addresses

Before LEAN-PKG the estate held 23 proof modules (~5.3k LOC) embedded in
one Rust repo, invisible to its sibling worktrees and unindexable by
Reservoir; one module (`TestFold.lean`) was not built by any lib target
and had gone unverified. Proof logic duplicated the failure mode the
estate already fixed for Rust crates.

## Requirements

Every requirement names its evidence class (SM-4): `GATE` (executable
check decides), `TEST`, `MEASURE`, `REVIEW`.

### LP-1 Package metadata (GATE)

A Lean package MUST declare in its `lakefile.toml`: `name`, `version`,
`description`, `license`. Reservoir reads these fields; missing fields
make the package invisible or mislabelled on the registry.

Evidence: `scripts/check-lean-pkg.py` checks the fields exist.

### LP-2 Toolchain pin (GATE)

A Lean package MUST pin `lean-toolchain` (`leanprover/lean4:vX.Y.Z`).
The fleet baseline is **v4.35.0**. Drift from the baseline is a defect:
proofs are version-fragile, and a mixed-baseline estate cannot share
olean-level guarantees. Toolchain bumps are PRs with a full green build;
never a direct push to main.

Evidence: `scripts/check-lean-pkg.py --baseline` fails on drift; the
fleet hourly check (`sys-check`, warn-only until 2026-11 migration
completes) reports drift across the dev tree.

### LP-3 Zero-sorry gate (GATE)

CI MUST fail on any `declaration uses 'sorry'` warning, not merely on a
non-zero build exit. The canonical gate:

```yaml
lake build 2>&1 | tee build.log
! grep -q "declaration uses" build.log
```

Evidence: the CI workflow in each package contains the grep; the oracle
checks for its presence.

### LP-4 Postulate inventory (REVIEW)

Every `axiom` declaration MUST be listed in the package README with a
one-line justification, and the README MUST state the `native_decide`
count with the reason each use survives. Zero sorries is the floor;
the inventory is the honest statement of what remains trusted.
Provable axioms are proven in follow-up PRs, not excused.

Evidence: `REVIEW` checklist item; the oracle verifies the README
section exists when the source declares axioms.

### LP-5 Import-free modules (REVIEW)

Proof modules MUST NOT import each other and MUST NOT be co-elaborated
(umbrella files that `import` every module are forbidden: duplicate type
names across modules are intentional, and merging environments turns
restatement into collision). Cross-file concepts are restated and tied
by enumeration theorems. Reuse happens at the package level.

Evidence: `REVIEW`; the clawdius-spec extraction demonstrated the
collision (two modules each declaring `ResourceLimits`, legal
separately, a build error merged).

### LP-6 Roots gate (GATE)

Every proof file MUST be reachable from a build target: an explicit
`roots` entry in `lakefile.toml` (or a `[[lean_lib]]` entry in the
clawdius legacy shape). A file no target builds is hand-checked, not
proven: that is how stale proofs survived (`TestFold.lean`, ungated
for its whole life).

Evidence: `scripts/check-lean-pkg.py` lists files under the library
source dir that no root covers and fails on orphans.

### LP-7 Claims are pinned by version tags (GATE)

A proof package MUST publish releases as `v`-prefixed git tags. Consumers
MUST pin an exact tag (`rev = "v0.1.0"` in `[[require]]`), never a
branch. A tag is a claim pin: theorems at that rev are verified and
frozen. Bumping the pin is a PR in the consumer with a green build.

Evidence: `scripts/estate-audit.py` records exact pins for crates; the
same claim discipline applies to `[[require]]` revs (oracle checks the
pin shape in consumers that declare one).

### LP-8 Reservoir shape (MEASURE)

A public proof package SHOULD carry the LP-1 metadata, an Apache-2.0 or
MIT `LICENSE`, and a README stating the rigor contract, so Reservoir
indexes it correctly. Adoption is measured by the package appearing in
`reservoir.lean-lang.org` search (crawl latency: days, not instant).

Evidence: `MEASURE` at the next estate review: record indexed/not per
package with the query date.

## Exceptions

Declared per package in its AGENTS.md, owned by the package owner, dated,
and fail-closed: an expired exception fails the oracle. Current known
exceptions: `morph` (v4.27.0, active Stage-C WIP; bump tracked by its own
loop), clawdius worktree branches (4.28.0 historical states; clear on
merge to main).

## Migration

| Step | Owner | Done |
|---|---|---|
| Extract clawdius proofs → clawdius-spec v0.1.0 | 2026-11-22 | ✓ |
| clawdius consumes via pinned require, sorry-gate CI | 2026-11-22 | ✓ |
| game-spec metadata (LP-1) | 2026-11-22 | ✓ |
| clawdius-spec → v4.35.0 (LP-2) | 2026-11-23 | PR open |
| morph → v4.35.0 | morph loop | pending (WIP freeze) |
| sys-check drift scan live | 2026-11-23 | PR open |
| Reservoir indexing visible | next crawl | pending |
