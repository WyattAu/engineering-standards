# 0019: Repo hygiene files are gated by contract

- **Status**: Accepted (2026-11-09). Advisory for one loop completed
  (CI 42725718935, 577a49d; 42728537738, 654f303); graduated to `gated`.
- **Date**: 2026-11-09
- **Deciders**: Wyatt Au
- **Relates to**: ADR-0013 (standards index is authoritative), ADR-0018 (ADR practice gated), OMNI-CORE.md invariant 8

## Context

OMNI-CORE 8 declares GitHub housekeeping (CODEOWNERS, issue/PR
templates, SECURITY.md, and others) as hygiene that is not per-repo
taste. STANDARDS-INDEX recorded CODEOWNERS, SECURITY.md, and issue/PR
templates as `declared` (prose only) with measured adoption of 16/125,
65/125, and 17/125,16/125 respectively. A declared rule with no machine
check can drift silently and its adoption number is the only evidence.

## Decision

Define `REPO-HYGIENE.md` (RH-1..RH-4) for SECURITY.md, CODEOWNERS,
issue templates, and pull request templates: standard locations,
non-empty files, a vulnerability reporting path, and at least one real
CODEOWNERS rule. Enforce it with `scripts/check-hygiene.py` (stdlib),
self-tested by `scripts/test-check-hygiene.py`, wired into
`estate-audit.yml` as advisory for exactly one loop (AGENTS.md rule 3),
then graduated to a required gate by a follow-up change recorded in the
index and changelog.

Provide reference templates under `templates/` and adopt the hygiene
files in this repository so the gate validates a real conforming target.

## Consequences

- The three declared OMNI-CORE 8 rows move to `advisory` with a named
  standard and gate; adoption percentages remain the measured estate
  figures until a fresh estate-wide scan recomputes them.
- The check validates presence and minimal shape, not owner freshness,
  contact responsiveness, or template quality (review concerns, stated
  in the standard).
- `check-hygiene.py` accepts common locations to avoid false failures on
  repos that already follow GitHub's supported paths.
