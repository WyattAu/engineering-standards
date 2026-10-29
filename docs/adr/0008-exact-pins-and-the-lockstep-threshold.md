# 0008. Exact pins, and the lockstep threshold at which families stop paying the cascade

Date: 2026-10-29

## Status

Accepted (2026-10-29). The tripwire below is measured from the 2026-10-24
to 2026-10-27 publishing rounds and the tooling built in the same window
(`scripts/chain-walk.py`, `scripts/drift-sweep.py`); re-measure it if the
publishing rhythm changes.

## Context

The estate pins its own crates exactly (`= x.y.z`) in every consumer
manifest. ADR-0005's rationale stands: exact pins force every consumer to
re-test against every producer release, which is how duplication, drift,
and silent breakage get caught while the break is one commit deep.

The cost of that discipline is now measured, not imagined:

- The vat-rules 0.1.1 release required five republishes before the
  composition graph could follow (ap-kit, fx-kit, invoice-kit,
  vat-return, statement-camt), plus the consumer pins.
- The 2026-10-24 to 27 publishing wave produced drift queues of 15, 27,
  4, 9, and 64 entries across two days; draining mid-wave was measured to
  be motion without progress (study 46, finding 6).
- The recon-kit 0.1.1 chain was walked twice by two agents working in one
  tree, because the walk had no owner and no tool.
- A release cut against a stale lock (webhookkit 2.2.2 and 2.2.3) shipped
  broken twice for the same missing call-site fix.

The tooling built in the same window: `scripts/chain-walk.py` walks a
republish chain end to end (query reverse dependencies, republish each
estate dependent in dependency order, run the tests, publish);
`scripts/drift-sweep.py` drains the consumer-pin queue; `scripts/crates.py`
publishes in topological order; the vet bots reconcile the store. The
mechanic is automated. The architecture question -- who should have to
republish, and how often -- is not, and this ADR answers it.

The in-estate precedent already exists: chisel-platform and signalkit
version as units, with a single `[workspace.dependencies]` root and
members inheriting the family version. Study 45 measured the same
structure at scale in zed (268 crates), rerun (162), and slint (110).

## Decision

1. **Exact pins remain the estate default** between crates that release
   independently.
2. **The lockstep tripwire: when walking one producer bump for a family
   requires republishing more than four estate crates, the family
   migrates to a lockstep workspace** -- one `[workspace.dependencies]`
   root, members inheriting the family version, exact pins retained only
   between families. The threshold is four because five has been paid
   (vat-rules) and one to three has been absorbed without pain (ap-kit's
   single-dependent chain; recon-kit's two-dependent chain).
3. **Within a lockstep family, the composition graph pins the family's
   single version.** The family's own CI gates its internal
   compatibility; `--locked` stays in CI; the family releases as one
   version per producer bump instead of N republishes.
4. **`scripts/chain-walk.py` is the tripwire's instrument**: its report
   of kept-versus-conflicting pairs per walk is the measurement that
   declares a family past the threshold. Declare at round close, from
   the report, not in the middle of a wave.
5. **Signalkit is the reference implementation** and is already past the
   threshold in practice (its three members cascade as one; the 0.3.0
   release moved them together). trendkit (three members, two published
   majors in one weekend) is the next candidate if its cascade repeats.

## Consequences

**Positive.** Intra-family cascades collapse to one commit and one
publish per producer bump. The family's members stop pretending to
release independently when they in fact move together. The composition
graph pins one number per family, which is the number a reader wants
anyway.

**Negative.** Family members lose independent release rhythm: a one-line
fix to one member ships at the family version, and an unfixed member
rides along. The lockstep migration is a one-time restructuring per
family (signalkit's rode its 0.3.0 major), and the family's internal
`cargo test` becomes the compatibility gate its members used to get for
free from the consumers' exact pins.

**Neutral.** The drift gate's meaning shifts at family boundaries: it
flags family-version lag, not per-crate lag. The audit's per-crate
freshness check stays, because freshness is still the signal that starts
the walk.

## The note this ADR files alongside

`templates/Cargo.toml.workspace` already carries the stanza a
family-ification needs, and `scripts/chain-walk.py --dry-run` is the
measurement that declares the threshold crossed. What this ADR adds is
the number, so the migration happens because a line was crossed -- not
because a wave was annoying.
