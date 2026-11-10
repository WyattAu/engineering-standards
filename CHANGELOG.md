# Changelog

One version for the document set, not for a package: this repository ships
standards, gates and token documents, so the unit of release is the canon.
Material change means version bump + ADR + entry here
(`STANDARDS-MODEL.md` SM-7, SPEC-CORE §5, AGENTS.md rule 6). A version bump
lands in the header of every document that changed.

## 0.5.0 - 2026-11-09

- ADR-0018 graduated: ADR practice (`DECISIONS.md` / `check-adr.py`,
  DC-1..DC-8) moved `advisory` -> `gated` in `STANDARDS-INDEX.md` after
  one clean loop (CI 42725718935, 577a49d). Adoption measured at 18
  records, 0 findings. Totals 44 machine-checked, 27 gated, 13 advisory.

## 0.4.0 - 2026-11-09

- `REPO-HYGIENE.md` (RH-1..RH-4, PROPOSED): vulnerability reporting path
  (SECURITY.md), CODEOWNERS ownership rules, issue templates, and pull
  request templates; implements OMNI-CORE 8.
- `scripts/check-hygiene.py` (+ `scripts/test-check-hygiene.py`, 10
  fixtures, PASS): per-repo presence/shape gate, stdlib-only, `--path`.
- ADR-0019 `docs/adr/0019-repo-hygiene-is-gated.md` (Proposed);
  `estate-audit.yml` runs the self-test and check as advisory for one loop
  (AGENTS.md rule 3).
- Reference templates added (`templates/CODEOWNERS`,
  `templates/PULL_REQUEST_TEMPLATE.md`, `templates/ISSUE_TEMPLATE/*`) and
  this repo adopts root `SECURITY.md`, `.github/CODEOWNERS`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*`.
- `STANDARDS-INDEX.md`: CODEOWNERS, SECURITY.md, and issue/PR templates
  moved `declared` -> `advisory` (REPO-HYGIENE.md / `check-hygiene.py`).
  Totals 44 machine-checked, 14 advisory, 10 declared.

## 0.3.0 (2026-11-09)

### Added

- `DECISIONS.md` (DC-1..DC-8), the ADR practice standard: numbered, stable
  filenames; machine-readable status and ISO date; required context,
  decision and consequence sections; amendment over silent rewrite (ADR-0018).
- `scripts/check-adr.py`, which gates the mechanical subset and accepts the
  three metadata forms already present in the corpus, plus
  `scripts/test-check-adr.py` (9 fixtures). Measured against this repository:
  16 records, 0 findings, 1 reported sequence gap (`0007` absent).
- CI runs the ADR gate as an advisory `standards-index` step (one loop).

## 0.2.0 (2026-11-09)

### Changed

- `DESIGN.md` DS-10, DS-11 and DS-12 move from `SHOULD` + `REVIEW` to `MUST`
  with a gate (ADR-0017). The type scale, spacing scale and motion set are
  now token groups with closed constraints rather than review checklists:
  integer px on one ratio, 4 px multiples starting at the base, durations
  inside named bands, and a mandatory 0 ms reduced-motion path.

### Added

- `type`, `space` and `motion` groups in both reference documents, measured
  by the gate: 5 type steps at ratio 1.25, 8 spacing steps from 4 to 64, and
  durations plus three cubic-bezier easings.
- `check-design-tokens.py` gains `type-*`, `space-*` and `motion-*` rules and
  the `--require-scales` flag that makes the three groups mandatory; CI
  passes it for both documents.
- 11 new fixtures in `test-check-design-tokens.py` (18 total), one per rule
  family, so a rule that stops firing fails the gate's own self-test.
- `CHANGELOG.md`, which SM-7 required but which did not exist.

## 0.1.0 (2026-11-09)

### Added

- `STANDARDS-MODEL.md` (SM-1..SM-11): how a standard is written, evidenced,
  versioned and indexed.
- `DESIGN.md` (DS-1..DS-19) and the reference palette, with the twelve-role
  closed vocabulary and ten gated contrast pairs per variant.
- `COMMITS.md` (CS-1..CS-9) and the measured commit-history baseline.
- `ADOPTION.md` (AD-1..AD-9) and `candidates.yml`, the third-party decision
  registry with API-measured metadata.
- `STANDARDS-INDEX.md`: 57 concerns, each with its standard, requirement ids,
  gate, enforcement level and measured adoption.
- Gates and self-tests: `check-design-tokens.py`, `check-commits.py`,
  `check-standards-index.py`, `check-adoption.py`, `audit-repo-settings.py`,
  `buildinfo.sh`.
- `tokens/estate-dark.dtcg.json` and `tokens/estate-light.dtcg.json`.
