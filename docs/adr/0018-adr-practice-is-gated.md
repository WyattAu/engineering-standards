# ADR-0018: ADR practice is a gated format contract

- **Status**: Accepted (2026-11-09). Advisory for one loop completed
  (CI 42725718935, 577a49d); graduated to `gated` in `STANDARDS-INDEX.md`.
- **Date**: 2026-11-09
- **Amends**: nothing (OMNI-CORE 9 names an ADR directory; this standard
  defines the record contract)
- **Supersedes**: nothing
- **Related**: ADR-0013 (standards model), ADR-0015 (commits gated),
  ADR-0016 (adoption registry), ADR-0017 (design scales gated)

## Context

OMNI-CORE 9 requires an ADR directory, and this repository has 16 ADRs.
Nothing checked their structure. The format drifted across three styles:
metadata lines (`- **Status**: ...`), bold metadata (`**Status:** ...`), and
section-headed status (`## Status` with a paragraph). Dates appeared as
`2026-10-31`, as `2026-10-08 (loop 21 amendment 2026-10-09)`, and as a
standalone `Date:` line.

The drift is not cosmetic. A status that a tool cannot find is a status a
reader cannot trust at a glance, and a decision without a date or a
consequence section is harder to audit than the diff that prompted it. The
standards work in this repository has also become self-referential: ADR-0013
through ADR-0017 each ratify a gate, so the record format is now load-bearing
for the canon, not just documentation hygiene.

The constraint is historical: 16 records already exist, several of them
settled. A gate that rejects them would force a rewrite of accepted history
for a formatting gain, which is the failure DC-5 exists to prevent.

## Decision

`DECISIONS.md` defines DC-1 through DC-8, and `scripts/check-adr.py` gates
the mechanical subset:

| Check | Finding code | What it accepts |
|---|---|---|
| filename `NNNN-lowercase-slug.md` | `adr-filename` | the form already used by all 16 records |
| unique number | `adr-duplicate` | gaps reported as notes, not failures |
| `Status` present, lead word known | `adr-status`, `adr-status-word` | metadata line or `## Status` section |
| `Date` present with `YYYY-MM-DD` | `adr-date`, `adr-date-format` | amendment dates after the first are allowed |
| `## Context` and `## Decision` | `adr-section` | case-insensitive heading match |
| consequence/rationale/outcome section | `adr-section` | `Consequences`, `Rationale`, `Outcome`, `Amendment`, `Alternatives`, `Impact`, `Risks` |

The gate deliberately accepts all three historical forms and treats sequence
gaps as notes, because the real invariant is a unique, citable number. It
does not judge materiality, completeness, or whether a change deserved an
ADR; those remain `REVIEW` under DC-1 and DC-5 through DC-7.

Measured on 2026-11-09 against `docs/adr/`: 16 records, 0 findings, 1 note
(`0007` absent). `test-check-adr.py` covers 9 fixture mutations, one per
rule family.

## Consequences

- "ADR practice" moves from `declared` to `advisory` in
  `STANDARDS-INDEX.md`, adding one machine-checked concern (41 of 57) while
  keeping enforcement advisory for one loop.
- Future records have a concrete contract to target, and the contract is
  tolerant enough that following it does not require learning which of three
  legacy styles a particular file happened to use.
- The gate cannot prevent a silent rewrite of an accepted record or a wise
  decision from being badly argued. Making those mechanical would produce
  either false failures or a gate everyone ignores, so the boundary is
  stated in DC-8 and left there.
- The `0007` gap remains a reported note. Closing it would mean inventing or
  renumbering history; neither is worth more than the note costs.
