# Research note 38 — formal verification in CI (and the Lean proof adjustment)

**Sources.** mathlib4 CI practice (warnings hygiene, `#print axioms` audits,
banned-convention linters, cache-first builds via `lean-action`); the Lean 4
kernel model (proofs re-checked on every build); Kani (Rust bounded model
checking) and hacspec (spec/impl in Rust, proof in Lean/F*/Coq) for the Rust
side.

## The property that makes Lean different in CI

A Lean proof is not a test: the **kernel re-checks every proof on every
build**. A test can rot silently (a flake, an over-mocked assert); a proof
cannot — but it *can* become incomplete (`sorry`) without failing the build,
because `sorry` is only a warning. So the cutting-edge CI practice for a
proof repo is not "run the proofs" (the build does that) but:

1. **fail the build on any `sorry`** (grep gate — mathlib-grade hygiene);
2. **print the axiom basis** of each theorem (`#print axioms`) — an
   incomplete proof surfaces `sorryAx` in the log;
3. **prove the documented behavior, not just the happy path** — a docstring
   that claims behavior the kernel does not check is a spec/test mismatch in
   formal clothing.

## What shipped (OmniLean, loop 38)

- REQ-002 (`clamp`) was defined with *documented* behavior and no proof — a
  spec/test mismatch in formal clothing. Now two theorems:
  `clamp_eq_in_bounds` (via `omega`) and `clamp_eq_lo` (via the hypothesis).
- `#print axioms` for all three theorems printed in CI logs.
- CI fails on any `sorry` in the source tree (grep gate beside
  `lake exe test`).

## The Rust side (filed, not forced)

Kani (bounded model checking of Rust) and hacspec (spec-in-Rust, proof in
Lean/F*) are the cutting edge, but the estate's Rust crates are IO-heavy
libraries where Kani harnesses would be substantial work for partial
coverage. Filed as an advisory rust-kit follow-up: a `kani` job (opt-in
input) behind the same advisory-then-graduate policy.

## vs the reference repos

mathlib4 is the reference: cache-first builds, linters as CI gates, and a
culture where every `sorry` is a tracked issue. The estate's Lean template
now matches the *audit* half (axioms + no-sorry gate) on a template-sized
codebase. The other templates: no formal component — the honest position is
that machine-checked properties live where the language supports them
(Lean), and the estate's other gates are empirically strong but not proofs.
That distinction is now explicit in OMNI-CORE 11f.
