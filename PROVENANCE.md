# PROVENANCE: build provenance for distributable artifacts

> **Status: PROPOSED (v0.1.0, 2026-11-10).** Ratification: ADR-0021.
> Implements [OMNI-CORE.md](./OMNI-CORE.md) invariant 11c.

Every distributable artifact a repository ships must carry build provenance
bound to the publishing workflow's OIDC identity, so consumers can verify
what was built, from which source, by which workflow. Provenance is
per-artifact and non-falsifiable by construction when issued via a trusted
registry or GitHub artifact attestations.

Machine check: `scripts/check-provenance.py`. Rule IDs: `PV-*`.

## PV-1. Attestation workflow or explicit non-distributable scope

A repository MUST satisfy one of:

1. **Attestation workflow present:** `.github/workflows/attest.yml` (or a
   workflow whose name/path clearly indicates provenance attestation)
   exists and contains (a) a step using `actions/attest-build-provenance`
   and (b) workflow/job permissions declaring `id-token: write` and
   `attestations: write` (required for GitHub artifact attestations).
2. **No distributable artifacts:** the repository explicitly declares that
   it produces no distributable artifacts covered by 11c, via a
   `.provenance-scope` file at the repository root containing
   `distributable: none` (or `distributables: none`). A repo with nothing
   to attest must say so rather than claiming coverage.

Fresh templates and repos without publishers stay unarmed by default (they
should carry the explicit `distributable: none` declaration until they
ship artifacts).

## PV-2. Provenance is bound to the publishing identity

Where artifacts are shipped, provenance MUST be bound to the workflow's
OIDC identity: GitHub artifact attestations (`actions/attest-build-provenance`)
for files the repo ships directly, and/or registry-generated provenance
where the registry provides it (e.g. npm `--provenance`, PyPI PEP 740
Trusted Publishing attestations). `check-provenance.py` validates the
presence and minimal shape of the attestation workflow; it does not verify
that every release run actually emitted a valid attestation.

## PV-3. Committed provenance records (when used)

If the repository keeps a committed provenance record (e.g. a `provenance/`
directory of per-release notes/hashes), the directory and its records are
the source of record for that mechanism. This is complementary to, not a
substitute for, signed/registry-bound attestations where those apply.

## Scope and limits

`check-provenance.py` checks presence and minimal workflow shape in one
repository path. It does not prove that a given artifact was attested in
CI, that OIDC/registry trust is correctly configured, or that
reproducibility (11b) holds. It does not enumerate all "distributable
artifacts"; the `distributable: none` declaration is the repo's explicit
scope statement and is trusted as a declaration (auditable in review).
Estate-wide adoption is measured separately.
