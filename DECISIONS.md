# DECISIONS: how a material choice becomes a record

> **Status: PROPOSED (v0.1.0, 2026-11-09).** Ratification: ADR-0018.
> Gate: `scripts/check-adr.py`.

**Applies to:** every Architecture Decision Record under `docs/adr/` in a
repository that has opted into this gate.
**Oracle:** the record files themselves. A decision not written down is not
a decision the next maintainer can honour or reverse on purpose.

## Why this standard exists

Chat explains a choice once. A commit message explains what changed. Neither
explains what was rejected, what would make the choice wrong, or who owns
reversing it. The estate already writes ADRs (16 in this repository alone),
and OMNI-CORE 9 names an ADR directory as required documentation. The format
still varied enough that a gate could not read it: some records put status
in a metadata line, some in a `## Status` section, and none of that was
checked.

The rule this standard enforces is simple: **a material choice leaves a
dated, numbered, machine-readable record that states the context, the
decision, and what follows from it.**

## DC-1 One record per material decision

**MUST.** A change that alters a public contract, a canonical invariant, a
gate, a security boundary, a dependency strategy, or the meaning of an
existing standard is recorded in `docs/adr/` before or with the change.
Typos, link fixes, and refactors that preserve behaviour do not require a
record.

- Evidence: `REVIEW` (materiality is judgement; the gate checks the record,
  not the decision to write one)
- Why: the cost of a missing record is paid by the next person who touches
  the code and has to reconstruct the reasoning from a diff.

## DC-2 Filenames are numbered, lowercase, and stable

**MUST.** A record is named `NNNN-lowercase-slug.md` where `NNNN` is a
zero-padded decimal number unique within the directory. The number is never
reused. A withdrawn draft may leave a gap in the sequence; uniqueness is the
invariant, not contiguity.

- Evidence: `GATE` (`adr-filename`, `adr-duplicate`); sequence gaps are
  reported as notes, not findings
- Why: a stable filename is a stable citation target. Renumbering a record
  breaks every ADR, issue and commit that cites it, and gaps are cheaper
  than broken links.

## DC-3 Status and date are present and machine-readable

**MUST.** Every record states a `Status` and a `Date` containing an ISO
`YYYY-MM-DD` value. Either metadata form is accepted because the existing
corpus uses both:

```text
- **Status**: Accepted (2026-10-31)
- **Date**: 2026-10-31
```

```text
## Status

Accepted (2026-10-29).
```

The status lead word is one of: `proposed`, `accepted`, `rejected`,
`superseded`, `deprecated`, `withdrawn`, `draft`. Text after the lead word
(ratification notes, loop ids, amendment dates) is allowed.

- Evidence: `GATE` (`adr-status`, `adr-status-word`, `adr-date`,
  `adr-date-format`)
- Why: status is how a reader knows whether to follow the record or route
  around it. A date without an ISO value is not sortable and not auditable.

## DC-4 A record states context, decision, and consequence

**MUST.** Every record contains a `Context` section, a `Decision` section,
and a section that states what follows: `Consequences`, `Rationale`,
`Outcome`, `Amendment`, `Alternatives considered`, or an equivalent heading.
The gate matches by heading name, case-insensitively.

- Evidence: `GATE` (`adr-section`)
- Why: a decision without context is an order; a decision without
  consequences is a wish. The third section is where the cost, the risk and
  the reversal path live.

## DC-5 Accepted records are amended, not silently rewritten

**MUST.** A material change to an accepted decision is recorded as an
amendment in the original record (dated) or as a new record that states
`Supersedes`/`Amends`. The original text remains readable so the history of
the decision survives.

- Evidence: `REVIEW` (the gate cannot tell whether a rewrite was silent)
- Why: rewriting an accepted record makes the old citations lie. A
  superseding record is cheap; reconstructing why a system behaves the way
  it does after the evidence was edited is not.

## DC-6 Status transitions are explicit

**SHOULD.** A record moves through states deliberately: `proposed` before it
is in force, `accepted` when ratified, `superseded` or `deprecated` when
replaced, `rejected` or `withdrawn` when not taken. A superseding record
names the record it replaces.

- Evidence: `REVIEW`
- Why: an accepted record that was quietly abandoned is more dangerous than
  a rejected one, because readers still treat it as current.

## DC-7 A record cites the canon it touches

**SHOULD.** When a decision changes a standard, a gate, or a token document,
the record names the requirement ids or file paths it affects (`DESIGN.md`
DS-10, `check-design-tokens.py`, `tokens/estate-dark.dtcg.json`). The
reverse link (the standard naming its ratifying ADR) belongs in the
standard's status line.

- Evidence: `REVIEW`
- Why: a decision that cannot be traced to the artefact it changed is hard
  to audit and easy to miss during a later revision.

## DC-8 The gate is the format, not the judgement

**MUST.** `check-adr.py` validates structure: filename, uniqueness,
metadata, required headings, status vocabulary. It does not judge whether
the decision was wise, whether the context is complete, or whether a change
required an ADR. Those remain review obligations (DC-1, DC-5, DC-6, DC-7).

- Evidence: `GATE` (scope is declared by the tool's own output)
- Why: a gate that pretends to judge reasoning will either block honest
  records or be routed around. The mechanical contract is what keeps the
  corpus readable; the judgement stays with humans and the review record.

## Using it

```sh
python3 scripts/check-adr.py                 # validate docs/adr/
python3 scripts/check-adr.py --dir path/adr  # another repository
python3 scripts/check-adr.py --json          # machine-readable
python3 scripts/test-check-adr.py            # self-test the gate
```
