# ADR-0013: a standards model, a design canon, and a countable index

- **Status**: Proposed (2026-11-09). Owner ratification pending; the artifacts
  land as PROPOSED and are advisory until ratified.
- **Date**: 2026-11-09
- **Complements**: [ADR-0004](0004-gui-toolchain-semantics-layer-not-toolkit.md)
  (the token contract this canon governs), ADR-0012 (estate canons conform to
  standards-core)
- **Supersedes**: nothing

## Context

An estate-wide audit on 2026-11-09 measured the gap between "we have a
standard" and "the standard is enforced". The findings that motivate this
ADR, all reproducible from the checkouts and the GitHub API:

1. **Rules exist without controls.** `OMNI-CORE 11g` requires a merge queue;
   **0 of 125 checkouts** have a workflow that reacts to `merge_group`.
   `11j` requires harden-runner; **0 of 125** use it. A stated invariant with
   zero adoption and no gate is a preference.
2. **Controls exist without observability.** `estate.yml` has no settings
   field (`area, crons, docs, gated, notes, status`), so no audit can see
   branch protection, secret scanning, or Dependabot security updates. 0 of 8
   sampled repos are protected; Dependabot security updates are off in 5 of 5
   sampled.
3. **Adoption is asserted, never counted.** The estate had no single place
   stating how many repositories satisfy which rule. 13 of 289 registered
   repos are `gated: true`.
4. **Design was the largest unstandardized surface.** Three design systems
   and four UI stacks predate `theme-kit` (ADR-0004), and the rules that make
   a palette defensible (contrast ratios, CVD separation, derivation) live in
   crate specs and PR comments rather than in one address a surface can be
   judged against.
5. **Gate scripts can silently check nothing.** `doc-lint.sh` used
   `EXTRA_FIND` before defining it, so under `set -u` the find subshell died
   and the oracle/REQ checks passed over zero files (fixed 2026-11-09).

The pattern: the estate standardized *code shape* well and *evidence* badly.

## Decision

1. **`STANDARDS-MODEL.md` is the meta-standard** (SM-1..SM-11). Every
   normative statement names an evidence class (`GATE`, `TEST`, `MEASURE`,
   `REVIEW`); every threshold is a number with a unit and a source; every
   exception is declared, owned, dated, and fail-closed; every standard is
   versioned and modular; coverage is countable.
2. **`DESIGN.md` is the visual and interaction canon** (DS-1..DS-19). It
   converts design decisions into numbers with cited sources: 4.5:1 and 3:1
   (WCAG 2.1 SC 1.4.3 / 1.4.11), 7:1 (SC 1.4.6), 2 px focus appearance
   (WCAG 2.2 SC 2.4.13), Lc 60/75 rank separation, delta-E-Ok 0.02 identity,
   45 to 75 characters measure, +30% localisation growth, 100 to 200 ms
   micro-motion, 4/8 px spacing base. Each rule carries a `Why`.
3. **`STANDARDS-INDEX.md` is the registry of record for coverage**: 56
   concerns, each with its standard, requirement ids, gate, enforcement
   status, and a measured adoption figure with sample and date.
4. **Two gates make the claims mechanical.**
   `scripts/check-design-tokens.py` implements DS-1/3/4/9/19 over a DTCG
   document (contrast, alias resolution, undeclared and expired exceptions),
   with `scripts/test-check-design-tokens.py` as its self-test.
   `scripts/check-standards-index.py` fails when the index cites a document
   or gate that does not exist and when its totals disagree with its rows.
5. **`scripts/buildinfo.sh` makes OMNI-CORE 11b checkable**: a deterministic
   JSON record of commit, toolchain, lockfile digests, locale, timezone,
   `SOURCE_DATE_EPOCH`, flags, host, and command, with `--compare` so two
   builds can be shown identical or different as bytes.
6. **`OMNI-CORE.md` gains a pointer, not a thirteenth invariant.** The twelve
   stay twelve; the design and meta canons are referenced from it, and
   changes to either require an ADR under the existing rule.

## Consequences

- **What becomes true immediately**: colour choices are reviewable against a
  number instead of taste; a border measured at 1.92:1 fails a build (that
  fixture is in the self-test); the index cannot cite a missing gate;
  a build's inputs are a recorded artifact rather than a assumption.
- **What becomes true only after adoption**: DS rules reach surfaces as
  `theme-kit` adoption reaches them (currently 2 token crates, 1 adapter).
  The index reports `0` adoption honestly rather than implying coverage.
- **What stays a `REVIEW` item**: typography, spacing, motion, icons,
  localisation, and data-visualisation taste are numeric `SHOULD`s with no
  harness yet. They are labelled as such, which is the point: the residue of
  judgement is visible instead of hidden inside prose.
- **Refusal**: this ADR does not add branch protection, secret scanning, or a
  merge queue to any repository. Those are settings changes with owner
  impact; the index records them as gaps with measured adoption so the
  decision can be made on numbers.
- **Cost**: two new gates and one script, all stdlib-only, all runnable
  locally (SC-9 / AGENTS.md rule 5); one more document per standard, which is
  the price of an address per concern.

## Evidence

| Claim | Command | Result (2026-11-09) |
|---|---|---|
| Design gate passes a conforming document | `scripts/test-check-design-tokens.py` | 7 fixtures, PASS |
| Design gate rejects a 1.92:1 border | same, `low-contrast` fixture | exit 1, `FAIL contrast` |
| Design gate rejects an undeclared exception | same, `undeclared` fixture | exit 1, `FAIL undeclared-exception` |
| Design gate measures alpha composited | same, `alpha-composite` fixture | exit 1, `FAIL contrast` |
| Index has no dangling references | `scripts/check-standards-index.py` | 56 concerns, 0 findings |
| Build record is deterministic | `scripts/buildinfo.sh --out a.json` twice then `--compare` | MATCH |
