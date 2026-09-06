# Mutation Testing — cargo-mutants

Policy, baselines, and roadmap for mutation testing across WyattAu Rust kits.

Tool: [cargo-mutants](https://mutants.rs/) 27.1.0, invoked as
`cargo mutants --all-features` (Tier A profile). Baselines below measured
locally 2026-09-06.

## Policy

1. **Cadence.** Every kit carries `.github/workflows/mutation.yml` — weekly
   schedule (Sat 03:00 UTC, cron `0 3 * * 6`) + `workflow_dispatch`. The job
   runs `cargo mutants --all-features -o mutants-out`, is
   `continue-on-error: true`, and uploads `mutants-out/` as an artifact.
2. **Promote when stable.** A workflow graduates to a blocking gate once
   (a) survivors are zero or equivalent-only, and (b) the score is stable
   across 4 consecutive weekly runs. Graduation = set
   `continue-on-error: false` and add
   `cargo mutants --all-features --fail-under <score>`.
3. **Triage discipline.** Every survived mutant is classified as exactly one
   of:
   - **MISSING TEST** → write a killing test, confirm with a scoped re-run,
     land under `test: kill <n> surviving mutants (cargo-mutants)`.
     (27.1.0 has no `--line` filter: confirm with `--file <f>` and/or
     `-F <regex>` matched against names from `--list`.)
   - **EQUIVALENT** → record in `<crate>/mutants-equivalent.txt` with a
     behavioral rationale (masked-by-later-guard with identical observable
     result, unreachable branch, by-construction-unreachable).
   - **UNVIABLE** → compile-error mutants (fn-body → `Default::default()`
     where no `Default` exists). Counted out of the score denominator.
4. **Cfg-unviable code.** `#[cfg]`-gated branches that `--all-features` never
   compiles (hand-rolled fallbacks, loom/kani shims) cannot be killed by the
   host suite. Exclude them via `mutants.toml` (`exclude_globs`) **only** when
   a dedicated harness covers them (`--no-default-features` fallback tests,
   loom/kani runs), and say so in the file comment.
5. **Timeouts.** A mutant classified TIMEOUT counts as caught (the mutation
   broke test termination), but is flagged in triage: proptest-based suites
   can turn operator swaps into hangs, which is signal, not silence.
6. **Determinism.** Kills must not depend on proptest luck. Any survivor
   whose only killer is a randomly-generated max/min-length input gets a
   pinned boundary test.
7. **25-minute local cap.** A full-crate local run is capped at 25 min; on
   timeout, narrow with `--file <largest src file>` and report partial
   coverage honestly (see salting).

## Baselines (2026-09-06)

| Crate | Mutants | Killed | Survived (unresolved) | Unviable | Viable-kill score | Tests added | Headline finding |
|---|---|---|---|---|---|---|---|
| barbican | 10 | 7 | 0 | 3 | 100% | 0 | Extractor fn-bodies unviable-by-construction; suite already total. |
| chronoshift (clock) | 49 | 45 | 0 | 4 | 100% | 0 | Clean — mock/real clock seams fully observed. |
| healthkit | 19 | 15 | 0 | 4 | 100% | 0 | Clean — axum route + registry tests kill everything viable. |
| salting | 60 | 51 | 0 (9 untested) | 0 | 100% of tested (51/51) | 2 | `low_memory()` preset was roundtrip-tested only — Default-replacement invisible; zxcvbn score-bucket guards had no boundary pins. 9 `strength.rs` mutants untested under the 25-min cap (run interrupted); `error.rs` generates no mutants (pure thiserror enum). |
| breaker | 89 | 58 | 1 equiv | 14 | 98.3% (58/59) | 2 | `failure_count()` getter observable only through the metrics histogram — killing test captures it with a recording recorder; `lock.rs` cfg-shim excluded (loom/kani harnesses). |
| validkit | 291 | 178 | 8 equiv (+41 cfg-unviable) | 64 | 95.7% (178/186) | ~78 | Validator-internal branches were barely observed: accessor roundtrips, `is_valid_*` helpers, length boundaries, and per-character-class inputs were missing; CR/LF guards masked by downstream validation are pinned by *message-asserting* tests. |

Notes:
- **validkit "cfg-unviable" (41):** all `#[cfg(not(feature = "regex"))]` /
  `not(std)` / `not(url)` fallback branches — covered by
  `tests/fallback_paths.rs` under `--no-default-features`, not by the
  mutation suite. Reclassify as kills by running a second
  `--no-default-features` mutation pass (queued).
- **Killing masked mutants:** a guard whose rejection a later validator
  repeats is *not* equivalent when the two paths emit different error
  messages — assert the message fragment, not just `is_err()`.
- **Flaky kill lesson (validkit `bucket.rs:89`):** a length-boundary mutant
  flipped between runs because only a proptest ever generated a max-length
  input. Every boundary mutant now gets a pinned test.

## Queued (baseline pending — workflow landed, no baseline yet)

tokenkit, cryptkit, webauthn-kit, hdwallet, ratelimit, ws-kit, blobkit,
money, otelkit. Same `mutation.yml` (header: *baseline pending*). Order of
attack when compute allows: one crate per night, smallest `src/` first;
budget 25 min/crate, narrow by `--file` on timeout.

Also queued: salting `strength.rs` completion pass (9 mutants untested under
the cap), and a `--no-default-features` second pass over validkit fallback
branches to convert the 41 cfg-unviable into tested kills.

## Running locally

```sh
cargo install cargo-mutants --locked   # or: taiki-e/install-action@cargo-mutants
timeout 1500 cargo mutants --all-features -o /tmp/mutants/<crate>
# triage survivors, then confirm kills scoped:
cargo mutants --all-features --file src/<file>.rs
```

Results land in `mutants.out/` (written only on completion — interrupted runs
leave partial `caught.txt`/`missed.txt` but no summary).
