# Feature compatibility — the additive-feature rule

Cargo unifies features **graph-wide**. If any crate in a consumer's dependency
graph enables `dep/feat`, then *every* crate in that graph is compiled with
`feat` enabled. There is no per-crate opt-out: features are a property of the
resolved graph, not of the crate that declares them.

That makes one ordinary-looking Rust idiom unsound in a shared graph:

```rust
pub enum CircuitBreakerError {
    Failure(String),
    #[cfg(feature = "timeout")]   // <-- unsound
    Timeout,
}
```

Nothing is wrong with this crate on its own. It builds green under
`--all-features` and green under `--no-default-features`. The defect is that
the crate's *correctness depends on which features the host happens to enable*,
and the crate cannot know that. A downstream crate that wrote an exhaustive
`match` compiles today and breaks the day an unrelated crate in the same graph
turns `timeout` on.

## The rule

> **An additive cargo feature must not gate a public API element.**

Concretely, a feature may **not** control whether any of these exist:

- a variant of a `pub enum` (R1)
- a `pub` field of a `pub struct` that is not `#[non_exhaustive]` (R2)
- a match arm over an enum the crate does not own (R3)
- a required method of a `pub trait` — one with no default body (R4)

A feature **may** add capability, as long as it adds whole new things rather
than reshaping existing ones. All of these are fine:

```rust
#[cfg(feature = "tls")]
pub mod tls { .. }                        // a whole module

#[cfg(feature = "mtls")]
pub struct MtlsIdentity { .. }            // a whole type

#[cfg(feature = "tracing")]
pub fn traced_request() { .. }            // a whole function

pub trait Clock {
    fn now_nanos(&self) -> u64;
    #[cfg(feature = "tsc")]
    fn now_tsc(&self) -> u64 { self.now_nanos() }   // default body (R4 ok)
}

#[non_exhaustive]
pub struct RetryConfig {
    #[cfg(feature = "jitter")]
    pub max_jitter: Duration,              // #[non_exhaustive] (R2 ok)
    ..
}
```

The distinction is **additive vs reshaping**. Gating a whole type adds a
capability: a host that never enables the feature never names the type, so
nothing it wrote can break. Gating a *field* or a *variant* reshapes a type
that already exists, and hosts already wrote code against the old shape.

Gating a private item is always sound. A `pub struct` with any non-`pub` field
already cannot be built with a struct literal downstream, and a `pub(crate)`
enum cannot be named by a host, so neither is observable outside the crate.
The rules deliberately do not fire on those.

## Why this is a rule and not a lint suggestion

The estate already paid for this class once. `outbox-kit` 0.1.0 matched
`CircuitBreakerError` without a `Timeout` arm; `breaker` exposes `Timeout`
behind an additive `timeout` feature; `worker-kit` then re-armed the same bomb
by pinning `timeout` in its own manifest. Every host that pulled both crates
failed with `E0004: non-exhaustive patterns`, and the only reason it was ever
found is that a human happened to write an integration suite combining them.

The fix for each instance was local and reasonable — enable the feature
yourself, or add a catch-all arm. But nothing prevented the next crate from
repeating it, and the failure mode is a *consumer* build breaking on an
unrelated dependency's feature change. That is the shape of defect a gate
belongs on.

Note what the accepted fixes have in common: they make the crate's match
**total under any unification**. A catch-all arm does that. Enabling the
feature in your own manifest also does that, because your `--all-features`
build then compiles against the widest enum you can see. Both are legitimate;
the rule's job is only to make sure somebody noticed.

## R3 in detail

R3 is the subtle one. A gated match arm is only dangerous when the enum being
matched has variants this crate does not control:

```rust
match breaker_result {
    CircuitBreakerError::CircuitOpen => ..,
    CircuitBreakerError::Failure(e) => ..,
    #[cfg(feature = "timeout")]
    CircuitBreakerError::Timeout => ..,   // <-- R3: foreign enum
}
```

If instead the enum is declared in this crate, gating both the variant and the
arm is self-consistent — the crate owns both sides of the invariant and no host
can observe the difference. (If the enum is `pub` *and* its variant is gated,
that is R1, reported once at the variant.) So the checker resolves enum
ownership crate-wide, including `Self` through the nearest enclosing `impl`.

R3 also requires the gated line to actually be an arm — a pattern followed by
`=>`. Gating a *statement* inside a match body is common and sound, and the
estate does it constantly:

```rust
match outcome {
    Ok(v) => v,
    #[cfg(feature = "tracing")]
    { tracing::warn!("retrying"); schedule_next() }   // a block, not an arm
}
```

## Enforcement

The shared CI workflow runs a `feature-compat` job on every kit repo. It checks
out this repo and runs [`scripts/check-features.py`](../scripts/check-features.py),
which fails the build on R1–R4 and on undocumented suppressions. It is pure
stdlib — no third-party Python deps, nothing to install in kit repos.

```sh
python3 scripts/check-features.py --cwd .          # human-readable
python3 scripts/check-features.py --cwd . --json   # machine-readable
python3 scripts/test-check-features.py             # the checker's own tests
```

The checker's tests are fixture crates under `scripts/testdata/`, one per rule
plus a `clean` crate that must produce no findings at all. `clean` is the
important one: it is the false-positive guard, and every case in it was a real
bug this checker had during adoption.

### Suppressing a finding

Sometimes a gate genuinely cannot apply — a vendored enum you do not control,
a type whose shape is frozen by an external ABI. Document it inline:

```rust
#[cfg(feature = "exemplars")]
// feature-compat: allow — `Exemplar` is appended by the wire-format spec we
// mirror; a host enabling it must handle the variant, and the spec is frozen.
Exemplar,
```

The reason is mandatory. A bare `// feature-compat: allow` with no text is
itself a finding (R5): the estate does not accept undocumented escape hatches,
and an unexplained `allow` is indistinguishable from a blanket suppression.

## Current estate state

Swept 2026-10-04: 29 kit crates and 4 multi-crate workspaces (1,100+ `.rs`
files across library targets). **16 findings, in 4 crates.** Both product
workspaces and both kit workspaces carry real debt.

| Crate | Rule | Feature | Sites | Assessment |
|---|---|---|---|---|
| `metrics-kit` | R1 | `openmetrics` | 1 | Real. `Format::OpenMetrics` — hosts rendering exposition output must handle both formats. |
| `worker-kit` | R1 | `cron` | 2 | Real, and the worst of the set: `Trigger::Cron` and `RegisterError::InvalidCron`, both `pub` enums that hosts match on. `RegisterError` is a `thiserror` enum whose gated variant carries a `#[source]`. |
| `crawlkit-engine` | R1 | `full`, `postgres`, `wasi-preview2` | 5 | Real. `CrawlError`, `StorageError`, `PluginInstance`. Note `full` is a **default** feature, so these are the common case rather than an edge. |
| `clawdius-gateway` | R2 | `auth` | 2 | Real. `AdminState` has public feature-gated fields and is constructible by struct literal. |
| `clawdius-core` | R1 | `local-llm` | 1 | Real. `EmbedderType`. |

The `crawlkit` and `clawdius` results are worth stating precisely, because both
look alarming and neither is as bad as the raw count suggests:

- **Binary members are excluded**, correctly. `crawlkit/crates/crawlkit` (the
  CLI) gates ~14 clap subcommands on `full`/`queue-ops`/`warehouse`. That is
  the idiomatic pattern for a binary with no `lib.rs`, and the checker skips
  the whole member.
- **Vendored code is excluded**, correctly. An earlier revision reported
  `clawdius/.cargo-vendor/half/src/slice.rs`. These rules are the estate's;
  holding a dependency to them is a false accusation.
- What remains in `clawdius` is 6 findings across three real libraries,
  including `clawdius/src/cli/mod.rs` — which *does* have an 8-line `lib.rs`
  re-exporting `pub mod cli`, so its `Commands` enum is technically public
  even though the crate is an application.

### Fix order

`worker-kit` first: two `pub` enums, both host-matched, and `cron` is
off-by-default so the break lands on whoever enables it. `crawlkit-engine` next
— five sites and `full` is default-on, so it has the widest blast radius.
`metrics-kit` and `clawdius` after.

The standard remedy for all of them is `#[non_exhaustive]` on the enum, which
converts "silently breaks every exhaustive match" into "one compile error at the
point of use, with a migration note". For `R2` on `AdminState`,
`#[non_exhaustive]` is the fix as well.

`outbox-kit` and `breaker` — the crates that started this — are clean, and
`outbox-kit` is now defended twice over: it enables `breaker/timeout` in its own
manifest *and* ends its dispatch match with a catch-all arm, each with the
reasoning recorded at the site. That is the shape to copy.

## Adoption order for the sweep

When enabling this gate across the estate, expect red on the four crates above.
The mechanical order that keeps every commit independently green:

1. Land the checker and this document (no behaviour change).
2. Add the `feature-compat` job to `rust-kit.yml` with `continue-on-error` or as
   a non-required status check, so adoption does not block unrelated work.
3. Fix the 16 findings. Each is small: an `#[non_exhaustive]` attribute, or
   splitting a public struct's feature-gated fields behind a new type.
4. Flip the job to required.

Steps 3 and 4 are where the estate's own gate rules apply: any change to a
public enum is a semver-affecting edit and needs the `CHANGELOG.md` entry and
the release-gate treatment, not a drive-by fix.

## See also

- [`layers.md`](layers.md) — the L0–L3 model, enforced by `check-layers.py`
- [`naming-convention.md`](naming-convention.md) — the 6 naming rules
- `README.md` §7 (Dependencies) and §10 (Feature compatibility)
