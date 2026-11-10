# 0020: Dependency update cooldown is a gated contract

- **Status**: Accepted (2026-11-09). Advisory for one loop completed
  (CI 42758017750, cfa334c, standards-index green); graduated to `gated`.
- **Date**: 2026-11-09
- **Deciders**: Wyatt Au
- **Relates to**: ADR-0013 (standards index is authoritative), OMNI-CORE.md invariant 11d, DEPENDENCY-COOLDOWN.md

## Context

OMNI-CORE 11d requires package releases to age before automated adoption
(30d majors, 7d minors, 7d github-actions, 3d patches) to reduce
exposure to short-lived supply-chain compromises. STANDARDS-INDEX
recorded this as `declared` (OMNI-CORE 11d, no machine check) with
53/125 checkouts measured. Without a check, cooldown configuration can be
omitted or weakened per-repo without a signal.

## Decision

Define `DEPENDENCY-COOLDOWN.md` (CD-1..CD-3) and enforce it with
`scripts/check-dependabot-cooldown.py` (stdlib-only, per-repo `--path`,
`--json`). The gate validates that `.github/dependabot.yml` (or `.yaml`)
exists, that every `updates:` entry declares a `cooldown:` mapping, and
that declared values meet the 11d minimums (github-actions: default-days
>= 7; other ecosystems: semver-major >= 30, semver-minor >= 7,
semver-patch >= 3, or default-days >= 30 as a baseline).

Wire the gate into `estate-audit.yml` as advisory for exactly one loop
(AGENTS.md rule 3), then graduate or revert with a recorded reason.

## Consequences

- "Dependency adoption cooldown" moves from `declared` to `advisory`
  with a named standard and machine check. The 53/125 estate adoption
  figure remains the prior measured sample until a fresh estate-wide
  scan recomputes it.
- The checker uses a minimal, indentation-aware parse (stdlib) rather
  than PyYAML to satisfy the checker stdlib-only rule; it covers the
  conventional dependabot.yml shapes this policy needs.
- The gate does not verify that Dependabot runs, that all ecosystems in
  use are listed, or that lockfiles are committed; those remain separate
  11d concerns. Security-update bypass is Dependabot-defined.
