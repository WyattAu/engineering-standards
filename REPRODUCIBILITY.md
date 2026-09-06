# Build Reproducibility

Same-machine determinism verification for released crates, via
`scripts/verify-reproducible.sh <crate-dir>`.

## Method

Two **from-scratch** `cargo build --release --locked` runs compared by SHA-256
of every artifact (top-level `release/` outputs plus `deps/*.rlib`,
`deps/*.rmeta`, `deps/*.so`). Each build gets:

- the **same absolute target dir and CARGO_HOME**, wiped in between — rustc
  embeds absolute paths of the target dir and dependency sources in
  rlib/rmeta, so distinct paths would legitimately hash differently;
- a **sanitized environment** (`env -i`: no `RUSTFLAGS`, no ccache/sccache
  wrappers, no incremental state, `SOURCE_DATE_EPOCH` pinned to the HEAD
  commit time, `TZ=UTC`, `LC_ALL=C`);
- a **fresh dependency download** — the registry cache is wiped, so every
  crate is re-fetched and its checksum re-verified (catches registry drift).

A run passes only if all artifact hashes are identical across builds.

## Caveat

Rust builds are reproducible **only** with the same toolchain, flags, and
dependency set. This verifies **same-machine determinism**: it catches
nondeterministic codegen and environment leaks, not cross-machine variance
(OS, CPU, rustc binary, absolute paths). A mismatch is a smell to
investigate, not by itself a supply-chain event.

## Results

Toolchain: `rustc 1.94.1 (e408947bf 2026-03-25)`, x86_64-linux.
Hashes are of the crate's primary artifact (`target/release/lib<crate>.rlib`).

| Crate | Version | Build 1 SHA-256 | Build 2 SHA-256 | Match |
|---|---|---|---|---|
| salting | 1.0.0 | `b3d734dc480c7c6ed9d8fe88bfe5f09e7a9fd8a950368fe5662d552d26bb7c77` | `b3d734dc480c7c6ed9d8fe88bfe5f09e7a9fd8a950368fe5662d552d26bb7c77` | ✅ (53/53 artifacts) |
| breaker | 1.0.0 | `ac8e9594ce4821a54570ced09c52814cbcd697d4b41a91f6ab64fd49a191d7bb` | `ac8e9594ce4821a54570ced09c52814cbcd697d4b41a91f6ab64fd49a191d7bb` | ✅ (all artifacts) |
| geo-kit | 1.0.0 | `56a38f9d24eb9072de39f788121318bccf49a5052ef42bb8213d59780ba0625d` | `56a38f9d24eb9072de39f788121318bccf49a5052ef42bb8213d59780ba0625d` | ✅ (all artifacts) |

Remaining 1.0.0 crates to verify (target: all 11): error-codes,
webhookkit, chronoshift, decimal-money, validkit, otelkit, throttle-kit.

## Release integration

Release provenance (`.github/workflows/attest.yml`) records the primary
artifact hash in `provenance/<crate>-<version>.json`; a provenance entry is
only meaningful if the crate also passes `verify-reproducible.sh` locally.
