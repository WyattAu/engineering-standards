# Research note 40: SBOM, VEX & dependency review

**Sources.** GitHub dependency-review action (`fail-on-severity`,
`deny-licenses`/`allow-licenses`); anchore/sbom-action (Syft; CycloneDX for
security/supply-chain workflows, SPDX for licensing/compliance); VEX
(Vulnerability Exploitability Exchange: tells *consumers* which advisories
do not apply to them); CISA federal SBOM push.

## The three controls, and where each lives

| control | what it does | where it lives in the estate |
|---|---|---|
| **dependency review** | PR-time gate: newly added deps with known HIGH vulns fail the PR; deny-listed licenses fail | `security.yml` `dependency-review` job (blocking), all 10 templates |
| **SBOM** | machine-readable component list shipped with releases, so *consumers* can map advisories to themselves | `release.yml` `sbom` job (CycloneDX via Syft, artifact), 6 release-producing templates |
| **VEX** | statement "advisory X does not affect us because Y": cuts consumer alert noise | **not implemented**: requires a triage process to generate honest statements; filed, not faked |

## Decisions recorded

- **CycloneDX over SPDX** for the security artifact (VEX embedding, scoring);
  SPDX remains what Syft emits if a consumer asks.
- **Blocking, not advisory** for dependency review: a HIGH-severity known
  vulnerability in a newly added dependency is a finding by definition (the
  advisory DB is ground truth), so the advisory-one-loop graduation does not
  apply. License denial is scoped to strong copyleft (GPL/AGPL/LGPL-3.x),
  which conflicts with the estate's Apache-2.0 position.
- **Syft over per-ecosystem tooling**: one uniform mechanism covers cargo,
  uv, go.mod, npm and the Haskell cabal graph: one tool, one format, one
  place to upgrade.
