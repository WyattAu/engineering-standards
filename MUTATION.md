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

## Baselines (2026-09-06/07)

| Crate | Mutants | Killed | Survived (unresolved) | Unviable | Viable-kill score | Tests added | Headline finding |
|---|---|---|---|---|---|---|---|
| barbican | 10 | 7 | 0 | 3 | 100% | 0 | Extractor fn-bodies unviable-by-construction; suite already total. |
| chronoshift (clock) | 49 | 45 | 0 | 4 | 100% | 0 | Clean — mock/real clock seams fully observed. |
| healthkit | 19 | 15 | 0 | 4 | 100% | 0 | Clean — axum route + registry tests kill everything viable. |
| salting | 60 | 51 | 0 (9 untested) | 0 | 100% of tested (51/51) | 2 | `low_memory()` preset was roundtrip-tested only — Default-replacement invisible; zxcvbn score-bucket guards had no boundary pins. 9 `strength.rs` mutants untested under the 25-min cap (run interrupted); `error.rs` generates no mutants (pure thiserror enum). |
| breaker | 89 | 58 | 1 equiv | 14 | 98.3% (58/59) | 2 | `failure_count()` getter observable only through the metrics histogram — killing test captures it with a recording recorder; `lock.rs` cfg-shim excluded (loom/kani harnesses). |
| validkit | 291 | 178 | 8 equiv (+41 cfg-unviable) | 64 | 95.7% (178/186) | ~78 | Validator-internal branches were barely observed: accessor roundtrips, `is_valid_*` helpers, length boundaries, and per-character-class inputs were missing; CR/LF guards masked by downstream validation are pinned by *message-asserting* tests. |
| money | 124 | 107 | 3 equiv | 14 | 97.3% (107/110) | 1 | Zero-amount sign flip (`<`→`<=`) rendered `$0.00` as `-$0.00` unobserved — now pinned; 2 of 3 equivalents are masked-by-later-guard (`use_iso_code` branch never reads `show_symbol`) and a boundary no-op (`==places` pads width-0 ≡ truncates to full length). |
| tokenkit | 32 | 25 | 1 cfg-phantom | 6 | 96.2% (25/26) | 4 + 1 fixed | Cross-algorithm (REQ-TK-105) test was masked by its own missing `iss` claim — required-claims rejection fired before the pinned-algorithm check; `validate()`/`encode_standard`'s exp arithmetic and Debug's algorithm name were unobserved; Redis store fail-closed pinned with a guaranteed-refused endpoint (kills all 3 store mutants). |
| otelkit | 16 | 12 | 1 equiv | 3 | 92.3% (12/13) | 1 | Sentry `traces_sample_rate`/`release` plumbing was unobserved — now asserted in-process via the hub client's `options()` (no network); `TelemetryGuard::drop` flush is equivalent-in-host-suite (observable only through an external collector/transport). |

Notes:
- **validkit "cfg-unviable" (41):** all `#[cfg(not(feature = "regex"))]` /
  `not(std)` / `not(url)` fallback branches — covered by
  `tests/fallback_paths.rs` under `--no-default-features`, not by the
  mutation suite. Reclassify as kills by running a second
  `--no-default-features` mutation pass (queued).
- **Killing masked mutants:** a guard whose rejection a later validator
  repeats is *not* equivalent when the two paths emit different error
  messages — assert the message fragment, not just `is_err()`.
- **Masked killer lesson (tokenkit REQ-TK-105):** a rejection test can pass
  for the *wrong reason*. The cross-algorithm test's claims omitted `iss`,
  so required-spec-claim validation rejected every token before the
  pinned-algorithm check could fire — the algorithm-confusion defense was
  green while its entire mapping function was mutable. Fixtures for
  rejection tests must be valid in every other respect; otherwise the test
  masks the very defense it names.
- **Fail-closed pins without infra (tokenkit Redis store):** store methods
  whose happy path needs a live backend are still killable — point them at
  a guaranteed-refused endpoint (`redis://127.0.0.1:1/`) and assert `Err`.
  This pins the fail-closed property AND kills every silent-success mutant;
  never use a "probably not running" default port.
- **Read-back beats equivalence (otelkit):** before classifying a config
  plumbing mutant as equivalent, check whether the value is readable back
  in process — `sentry::Hub::current().client().options()` exposed both
  deleted fields without any transport. Private-field ≠ unobservable.
- **Flaky kill lesson (validkit `bucket.rs:89`):** a length-boundary mutant
  flipped between runs because only a proptest ever generated a max-length
  input. Every boundary mutant now gets a pinned test.

## Queued (baseline pending — workflow landed, no baseline yet)

cryptkit, webauthn-kit, hdwallet, ratelimit, ws-kit, blobkit. Same
`mutation.yml` (header: *baseline pending*). Order of attack when compute
allows: one crate per night, smallest `src/` first; budget 25 min/crate,
narrow by `--file` on timeout.

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
