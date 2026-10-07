# cargo-vet: coverage, exemptions, and the gate

## The rule

Every estate repo gates on `cargo vet --locked`.

Coverage comes from three places, and which one applies varies by repo:

| Source | Meaning |
|---|---|
| `supply-chain/imports.lock` | crates **vetted** to a criterion |
| `supply-chain/audits.toml` | crates covered by an **audit record** |
| `supply-chain/config.toml` `[[exemptions.NAME]]` | everything **else** |

A package needs an exemption only when neither of the first two apply.
That is a decision for `cargo vet` to make, not for a script to
reimplement — see [Why not derive it from the
lockfile](#why-not-derive-it-from-the-lockfile) below.

## The failure this addresses

Any dependency change can leave a package uncovered, and cargo-vet reports
it as one line per crate:

```
  zerocopy:0.8.59 missing ["safe-to-run"]
  zerocopy-derive:0.8.59 missing ["safe-to-run"]
  …
```

with no hint at the fix. A forgotten exemption update has been the
estate's most frequent CI red, and the hand-rolled repair was itself
order-sensitive: writing exemptions and *then* regenerating the lockfile
leaves them stale again, producing a second red run.

`scripts/resync-vet-exemptions.py` fixes both problems.

## The commands

```sh
# 1. Finalise dependencies (bumps, pins, features).
cargo generate-lockfile

# 2. Fix. Appends exemptions for exactly what cargo vet reports missing,
#    then canonicalises the store itself. This is the whole repair.
python3 scripts/resync-vet-exemptions.py --write

# 3. The gate.
cargo vet --locked
```

`--write` runs `cargo vet fmt` for you, before and after. That is not
tidiness: cargo-vet refuses to *report* coverage while the store is
unformatted, so an out-of-order `[[exemptions.NAME]]` block for a crate
present at two versions makes it emit a store-consistency error instead of
the missing-package list — leaving `--write` with nothing to act on and no
way to tell that from a genuine dead end. Earlier revisions of this script
made the caller do the formatting first, which meant the documented order
was load-bearing; now it is not.

Version blocks for a crate present at two versions are ordered
numerically (`0.9.6` before `0.10.2`), not lexicographically, so the output
is stable and a second run is a no-op.

Verify without writing — this is exactly what CI runs:

```sh
python3 scripts/resync-vet-exemptions.py --check
```

On success it prints cargo-vet's own summary line. On failure it names the
packages, the criterion each needs, and the four-step fix above.

## What CI does

The shared `quality / vet` job in `.github/workflows/rust-kit.yml` runs
**one** cargo-vet invocation, through the script:

```yaml
- run: python3 .standards/scripts/resync-vet-exemptions.py --check
```

The script shells out to `cargo vet --locked` itself, so this is not a
second, slower run — it is the same run with a better failure message.
The script exits with cargo-vet's own status, so it can never turn a green
repo red or a red repo green.

## Why the write is additive

`--write` only ever **appends** `[[exemptions.NAME]]` blocks. It never
deletes or rewrites existing entries and never reorders them. That matters
because:

- a repo with real `imports.lock` audits keeps them untouched;
- a hand-written entry with a good reason survives;
- the diff shows exactly which packages the current lockfile introduced,
  which is what a reviewer wants to see.

It also means genuinely-stale entries (a version no longer in the lock) are
left behind. `cargo vet` does not complain about those, so they are
harmless; `cargo vet fmt` keeps the file tidy. Prune them by hand if the
list grows unwieldable.

`--write` is idempotent: running it twice adds nothing the second time.

## Why not derive it from the lockfile

The first version of this script did exactly that — it derived the
required set from `Cargo.lock` and demanded an exemption for every
registry package. On `formula-lang`, which has a populated
`imports.lock`, that produced **34 spurious exemptions**: cargo-vet was
already satisfied by 32 fully-audited crates plus 2 partial audits, and
the repo passed.

Wiring that version into the shared gate would have turned **19 green
repos red**. The lesson generalises: coverage is a property of three files
plus cargo-vet's own criteria logic, so anything that tries to shortcut it
will be wrong for some repo. The script therefore uses cargo-vet's output
as ground truth and adds no coverage logic of its own.

## Why `cargo vet fmt` is a separate step

`cargo vet fmt` normalises block order and spacing, and `--write` calls it,
so the diff for a dependency bump shows a version change rather than a
reshuffled file.

## Vetting rather than exempting

If a package in the `missing` list should be vetted rather than exempted,
do not add an exemption — add it to `imports.lock`:

```sh
cargo vet --import-keys <crate>   # prints the key lines to paste
```

That is the direction the estate should move over time: blanket
exemption is a pragmatic floor, not a destination.

## Adding a repo

Copy the layout from any green repo:

```
supply-chain/
  config.toml     # [cargo-vet] header + [[exemptions.NAME]] blocks as needed
  imports.lock    # vetted crates — may be empty, or nearly so
  audits.toml     # audit records — may be empty
```

Then run the four steps. If the crate graph has no registry dependencies,
`cargo vet --locked` simply succeeds and there is nothing to write.
