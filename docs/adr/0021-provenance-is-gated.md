# 0021: Build provenance is a gated contract

- **Status**: Proposed
- **Date**: 2026-11-10
- **Deciders**: Wyatt Au
- **Relates to**: ADR-0013 (standards index is authoritative), OMNI-CORE.md invariant 11c, PROVENANCE.md

## Context

OMNI-CORE 11c requires every distributable artifact to carry build
provenance bound to the publishing workflow's OIDC identity (GitHub
artifact attestations and/or registry-generated provenance), and requires
repos with no distributable artifacts to say so rather than claim
coverage. STANDARDS-INDEX recorded this as `declared` (gate referenced
`.github/workflows/attest.yml`, no named standard/checker) with 6/125
checkouts measured. Without a machine check, attestation presence and
minimal permissions/shape can drift and non-distributing repos lack an
explicit, auditable scope declaration.

## Decision

Define `PROVENANCE.md` (PV-1..PV-3) and enforce it with
`scripts/check-provenance.py` (stdlib-only, per-repo `--path`, `--json`).
The gate passes when a repository either (a) declares `distributable: none`
in `.provenance-scope` (explicit no-distributables scope), or (b) has an
attestation workflow (canonically `.github/workflows/attest.yml`) that
uses `actions/attest-build-provenance` and declares `id-token: write` and
`attestations: write` permissions.

Wire the gate into `estate-audit.yml` as advisory for exactly one loop
(AGENTS.md rule 3), then graduate or revert with a recorded reason.

## Consequences

- "Provenance and attestation" moves from `declared` to `advisory` with a
  named standard and machine check. The 6/125 estate adoption figure
  remains the prior measured sample until a fresh estate-wide scan.
- The check validates presence and minimal workflow shape, not that a
  given release emitted a valid attestation or that OIDC/registry trust is
  correctly configured (stated in PROVENANCE.md limits).
- The `.provenance-scope` declaration gives non-distributing repos (and
  fresh templates, per 11c) an explicit, auditable way to satisfy the
  contract without arming a publisher.
