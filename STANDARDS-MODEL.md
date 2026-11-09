# STANDARDS-MODEL: how a concern becomes a standard

> **Status: PROPOSED (v0.1.0, 2026-11-09).** Ratification: ADR-0013. Until
> ratified this file is normative for new standards and informative for the
> existing ones (OMNI-CORE, SPEC-CORE, DOC-STYLE), which are being mapped
> onto it rather than rewritten.

This document exists because "we have a standard for X" was unfalsifiable.
Every concern in the estate now has exactly one address, one evidence class,
and one enforcement status, and the number of concerns that satisfy all
three is published (`STANDARDS-INDEX.md`).

## SM-1 One concern, one document, one address

A standard covers exactly one concern and lives in exactly one file. A hub
document may list concerns and link them; it may not restate them. A second
file that states the same rule is a defect, not redundancy: the audit can
only trust a unique address (SPEC-CORE SC-1 applied to standards).

## SM-2 Every standard carries a header block

Required, in this order:

```markdown
# <ID>: <concern>

> **Status: DRAFT | PROPOSED | CURRENT | FROZEN (<date>) | SUPERSEDED by <path>.**
> **Version: v<major>.<minor>.<patch>.** <one line on what changed>

| Field | Value |
|---|---|
| Owner | <repo> |
| Tiers | all | S | K | A | D |
| Oracle | <path> or `No-oracle: <reason>` |
```

A standard without a header block is draft material and may not be cited by
a gate.

## SM-3 Normative language is RFC 2119 / RFC 8174

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, uppercase only when
normative. Prose that describes intent uses lowercase. "Should" in
lowercase is a wish and is not auditable.

## SM-4 Every normative statement names an evidence class

One of exactly four:

| Class | Meaning | Gate behaviour |
|---|---|---|
| `GATE` | an executable check in `scripts/` decides pass/fail | blocking once adopted |
| `TEST` | a named test or property in a named suite decides pass/fail | blocking |
| `MEASURE` | a recorded number with a date and command; a human compares it to a threshold next review | advisory, re-measured on schedule |
| `REVIEW` | a checklist item a human signs in the PR | advisory |

A statement with no class is prose, and prose is not a standard. This is the
mechanism behind "quantifiable and qualifiable": `GATE` and `TEST` are
quantifiable by machine, `MEASURE` is quantified by a dated number, and
`REVIEW` is the explicit, visible residue of judgement.

## SM-5 Thresholds are numbers with units and sources

A threshold MUST be a number with a unit and a citation: `4.5:1 (WCAG 2.1
SC 1.4.3)`, `>= 90% line coverage (cargo-llvm-cov)`, `<= 200 ms (Material 3
motion, micro)`. Banned in normative text: "reasonable", "appropriate",
"sufficient", "fast", "clean", "modern". If a concern genuinely has no
number, it is a `REVIEW` item and says so.

## SM-6 Exceptions are declared, owned, dated, and fail-closed

An exception MUST be declared at the point of use with an owner, an expiry
date, and a reason, in a machine-readable place the gate reads. Undeclared
exceptions fail the gate; declared ones are counted and reported. There is
no global allowlist (matching `docs/layers.md` rule 5: no waiver
mechanism).

## SM-7 Standards are versioned; changes are decided on the record

Material change = version bump + ADR + `CHANGELOG.md` entry (SPEC-CORE §5,
engineering-standards AGENTS.md rule 6). Adding a `MUST`, raising a
threshold, or narrowing scope is material. Typos and link fixes are not.

## SM-8 A standard is modular and composable

Standards reference each other by ID (`OMNI-CORE 11g`, `SPEC-CORE SC-6`,
`DESIGN DS-3`) and never copy text. The dependency direction is one-way:
`STANDARDS-MODEL` -> concern standards -> gates. A concern standard that
needs a rule from another concern cites it, so a change lands in one place.

## SM-9 Coverage is countable and published

`STANDARDS-INDEX.md` lists every concern with its standard, requirement ids,
gate, enforcement status, and measured adoption. Its totals are the honest
answer to "do we have a standard for everything". A concern that appears in
the index with standard `none` is a known gap, not an oversight.

`scripts/check-standards-index.py` fails when the index cites a document or
gate that does not exist, so the index cannot rot into a wish list.

## SM-10 Adoption is measured, not asserted

Every `GATE` row in the index carries an adoption count measured across a
stated sample and date (`0/125 checkouts, 2026-11-09`). A gate that exists
but is adopted nowhere is reported as `declared`, never as `gated`. The
distinction is the difference between a policy and a control.

## SM-11 Standards are consumed by machines

Anything a gate needs is machine-readable: thresholds in the standard's
table, exceptions in the artifact, adoption in the index. A standard that
can only be checked by reading it is a `REVIEW` standard and is labelled as
such.

## Applying this document

1. Name the concern in one sentence. If it needs "and", it is two concerns.
2. Assign the next id in its namespace (see `STANDARDS-INDEX.md`).
3. Write the header block, the requirements as a table with evidence
   classes, and a `Why` column per requirement. The `Why` is not optional:
   a rule without a reason cannot be revised intelligently, only obeyed.
4. Add the index row before writing the gate, so the gap is visible from
   day one.
5. Wire the gate into `scripts/` and the shared workflow, advisory for one
   loop, then blocking (AGENTS.md rule 3).
