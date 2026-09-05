# Threat Model — <crate>

Reference: STRIDE. Scope: the crate's public API surface as used by a
downstream service. Trust boundaries: (1) bytes/strings entering public parse
or verify functions, (2) concurrent callers sharing one handle, (3) the
dependency tree.

## Assets

| ID | Asset | Example |
|----|-------|---------|
| A1 | <what an attacker wants: accepted forged input, secret leak, DoS of caller> | |

## STRIDE Analysis

| # | Threat | Category | Surface | Mitigation | Verifying test |
|---|--------|----------|---------|------------|----------------|
| T1 | Panic on malformed input (DoS via abort) | DoS | `<fn>` | Errors are `Result`; fuzz harness `fuzz_x` asserts Err-not-panic | `tests/fuzz.rs` |
| T2 | Forged signature/token accepted | Spoofing | `<verify fn>` | Constant-time compare / ring verification | `<test>` |
| T3 | Replay of previously-valid input | Replay | `<fn>` | `<freshness/counter mechanism>` | `<test>` |
| T4 | Secret material leaked via Debug/Display/logs | Info disclosure | `<types>` | Redacted `Debug`/`Display`, zeroize on drop | `<test>` |
| T5 | Caller-downgrade forcing weak algorithm | Elevation | `<config>` | Allow-listed algorithms only | `<test>` |

## Out of Scope

- Caller-side misuse (e.g., reusing a nonce outside this crate's control)
- Resource exhaustion beyond documented limits

## Residual Risks

- <Known, accepted, documented — with rationale>
