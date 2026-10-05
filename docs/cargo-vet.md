# cargo-vet: keeping exemptions in sync

## The rule

Every estate repo gates on `cargo vet --locked`.

`supply-chain/imports.lock` and `supply-chain/audits.toml` are
deliberately **empty**: the estate does not vet individual third-party
crates, it exempts them. That means `supply-chain/config.toml` must name
**every** registry- or git-sourced package in `Cargo.lock`, at that
package's **exact** locked version, or `cargo vet --locked` fails with
`missing ["safe-to-deploy"]`.

Packages with no `source` key in the lockfile — workspace members and path
dependencies — are first-party and never need an exemption.

## Why this needs a script

Because of the rule above, `supply-chain/config.toml` is a **pure
function of `Cargo.lock`**. Every dependency change invalidates it.

Regenerating it by hand was, until this script existed, the estate's most
frequent CI red — and the manual fix was itself order-sensitive:

```sh
# WRONG — writes exemptions, then the lockfile moves under them.
#         Resync again and you have a second red run.
python3 scripts/resync-vet-exemptions.py --write
cargo generate-lockfile
```

The correct order is lockfile first, exemptions second. `scripts/resync-vet-exemptions.py`
owns that ordering so nobody has to remember it.

## The commands

```sh
# 1. Finalise dependencies (bumps, pins, features).
cargo generate-lockfile

# 2. Regenerate the exemption set from that lockfile.
python3 scripts/resync-vet-exemptions.py --write

# 3. Canonical ordering/formatting — cargo-vet's own formatter.
cargo vet fmt

# 4. The gate itself.
cargo vet --locked
```

Verify without writing (what CI runs):

```sh
python3 scripts/resync-vet-exemptions.py --check
```

`--check` exits non-zero on drift and prints the missing/stale counts plus
the exact four-step fix, instead of leaving you to read cargo-vet's output.

## What CI does

The shared `quality / vet` job in `.github/workflows/rust-kit.yml` runs:

1. `resync-vet-exemptions.py --check` — fails fast with an actionable
   message if the exemption set drifted.
2. `cargo vet --locked` — unchanged.

Step 1 adds no new failure modes: a repo whose exemptions have drifted
already fails step 2. It only replaces a wall of one-line-per-crate
`missing ["safe-to-deploy"]` output with a single actionable error, and it
catches the case where a stale entry happens to still pass.

## Why `cargo vet fmt` is a separate step

The script writes exemptions sorted by name, then version. That is
deterministic and diff-friendly, but it is not always byte-identical to
cargo-vet's canonical formatting — `cargo vet fmt` normalises block order
and spacing. Running it makes the diff show only real dependency changes,
so a reviewer sees a version bump rather than a reshuffled file.

## Adding a repo

Copy the layout from any green repo:

```
supply-chain/
  config.toml     # [cargo-vet] header + one [[exemptions.NAME]] block per locked package
  imports.lock    # intentionally empty (see header comment)
  audits.toml     # intentionally empty (see header comment)
```

Then run the four steps above. If your crate graph is empty
(no registry dependencies), `resync-vet-exemptions.py` refuses to touch
the file rather than writing an empty exemption set.

## Refreshing versions

To move a pinned dependency to a new version, expect to re-run the
regeneration — that is the intended workflow, not an annoyance. If a
`cargo update` lands without a regeneration, `quality / vet` will say so
in one line.
