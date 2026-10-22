# Research note 37: flaky tests & test selection

**Sources.** Google Testing Blog, *Flaky Tests at Google and How We Mitigate
Them* (smart retry; "if it reproduces, fail it"); Mill/Li Haoyi, *How To
Manage Flaky Tests in your CI Workflows* (retry failed tests only, after the
suite, on a clean machine); minware + TestDino + Datadog flaky-management
practice (quarantine with owner, ticket, 14-day expiry, exit criteria,
weekly review); cargo-nextest (per-test process isolation, `--retries` with
flake reporting); Google's finding that **new flake rate ≈ fix rate**: you
manage flakes as debt, you never reach zero.

## Policy (adopted loop 37)

1. **Retries are data, not a pass.** A failed test may retry **once**; the
   retry is reported as flake data. Blanket retries (re-running everything,
   or rerunning until green) are masking and are forbidden.
2. **Isolation beats retrying.** The strongest anti-flake mechanism is not a
   retry policy but per-test process isolation: shared state cannot cause
   order flakiness if tests cannot share state.
3. **Quarantine, never delete or silently skip.** A quarantined test keeps
   running in a non-blocking job, with an owner, a ticket, a 14-day expiry,
   and exit criteria (e.g. 50 consecutive greens to return to blocking).
4. **Randomize execution order where the runner supports it**, printing the
   seed: order coupling is a top flake cause and randomization surfaces it.

## Implementation

- **rust-kit**: `cargo-nextest` (via taiki-e install-action): per-test
  isolation + `--retries 1`. Doctests run explicitly in their own step
  (nextest does not cover them; dropping them silently would shrink the
  gate). Loom keeps the standard harness (`--test-threads=1`). Verified in
  CI on OmniRust: `Nextest run ID ...` present, all gates green.
- **OmniPython**: `pytest-randomly` added: randomized order, seed printed
  for reproduction. Hypothesis manages its own counterexample
  reproducibility. Suite green (11 passed).
- **Go**: `go test` has no retry primitive; `gotestsum --rerun-fails` is the
  standard upgrade: filed, not forced (Go's test binaries are
  long-lived-process, so isolation differs; revisit when a flake appears).

## What we do that the references do not

The estate's property-based tests (Hypothesis in Python) generate their own
reproducers on failure, and the loom model-checking job in rust-kit tests
concurrency deterministically: flake *prevention* at the mechanism level,
which the quarantine-and-dashboards practice in the literature implicitly
treats as out of scope.
