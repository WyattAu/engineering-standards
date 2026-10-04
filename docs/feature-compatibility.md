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

The sweep found 16 findings in 4 crates. All 16 are now fixed, and the gate
re-reports zero across the estate.

| Crate | Rule | Feature | Sites | Fix |
|---|---|---|---|---|
| `metrics-kit` | R1 | `openmetrics` | 1 | `Format` → `#[non_exhaustive]` |
| `worker-kit` | R1 | `cron` | 2 | `Trigger`, `RegisterError` → `#[non_exhaustive]` |
| `crawlkit-engine` | R1, R2, R3 | `full`, `postgres`, `wasi-preview2` | 7 | `CrawlError`, `StorageError`, `PluginInstance`, `AnalysisContext` → `#[non_exhaustive]`; two gated `RequestFailed` arms collapsed into one unconditional arm with a `cfg`-gated body |
| `clawdius-core` | R1 | `local-llm` | 1 | `EmbedderType` → `#[non_exhaustive]` |
| `clawdius` (CLI) | R1 | `keyring`, `vector-db` | 2 | `Commands` → `#[non_exhaustive]` |
| `clawdius-gateway` | R2 | `auth` | 2 | `AdminState` → `#[non_exhaustive]`, plus a new `attach_auth(..)` and two call sites moved off struct literals |

`#[non_exhaustive]` is the right remedy rather than a suppression for every one
of these, and the reason is worth stating: it does not merely silence the gate,
it changes *which* failure a future feature produces. A new gated variant behind
`#[non_exhaustive]` yields one compile error at the point of use, with the
compiler naming the missing arm — instead of a build break in a downstream
crate that never asked for the feature. That is why the checker stands R1 down
when it sees the attribute.

Two of the fixes found further breakage on their own, which is the argument for
doing this before merging the gate rather than after:

- `crawlkit-engine`'s `IsRetryable` matched two `cfg`-gated arms for
  `RequestFailed`. The variant exists in *both* feature states — only its
  payload type changes — so the gating bought nothing while putting the
  match's totality at risk. One arm with a `cfg`-gated body is strictly
  better.
- `AdminState` → `#[non_exhaustive]` immediately failed
  `cargo check -p clawdius-gateway --features auth` with `E0639`: `main.rs`
  built the struct with a literal in two places, a path evidently not built in
  CI without that feature.

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

`outbox-kit` and `breaker` — the crates that started this — were never in the
table: they are already clean. `outbox-kit` is defended twice over, each with
the reasoning recorded at the site: it enables `breaker/timeout` in its own
manifest, *and* ends its dispatch match with a catch-all arm. That is the shape
to copy for a crate that cannot take `#[non_exhaustive]` (a foreign enum it
does not own, for instance).

## Adoption

The gate is in `rust-kit.yml` and every kit picks it up by calling the shared
workflow — no per-repo wiring, and no `continue-on-error` crutch needed,
because the estate is already green.

1. **Done** — checker, 13 fixtures, and this document.
2. **Done** — all 16 findings fixed across 6 crates, each with a
   `CHANGELOG.md` entry naming the gate as the reason.
3. **Next** — merge `rust-kit.yml` to `main` and confirm the first kit runs.

New code should be written against the rule rather than fixed afterwards. The
three always-legal shapes — a whole gated module, a whole gated type, a
defaulted trait method — cover nearly every case anyone actually wants, so the
gate should rarely fire on new work.

## See also

- [`layers.md`](layers.md) — the L0–L3 model, enforced by `check-layers.py`
- [`naming-convention.md`](naming-convention.md) — the 6 naming rules
- `README.md` §7 (Dependencies) and §10 (Feature compatibility)
