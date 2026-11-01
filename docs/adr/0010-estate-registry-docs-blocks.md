# ADR-0010: docs posture blocks in the estate registry

**Status:** Accepted
**Date:** 2026-10-31

## Context

`estate.yml` is the registry of record for repo and crate health
(area, status, crates, pins). Specification and documentation posture had
no registry expression, so nothing failed when a repo's docs claims and
reality diverged. `spec-standards` (SC-7) defines the `docs:` block schema
and owns `spec-audit.py`; this auditor is the registry's authority and
must at least validate the block shape.

## Decision

Repo entries gain an optional `docs` block: `tier` (s/k/a/d), `specs`
(list of normative spec paths), `truth_table`, `llms_txt` (bool),
`status` (current/draft/frozen/stale/superseded), `last_audit` (ISO date).
`docs` joins `REPO_KEYS`; the auditor validates enums and types. Schema
ownership stays with spec-standards (SPEC-CORE §7); path existence and
staleness checks run via `spec-audit.py --registry --remote`, not here,
to keep this audit's network surface unchanged. `spec-standards` itself
is registered (area infra, status support: support deliberately not core,
since no consumer suite pins the shared docs workflow yet).

Seeded 2026-10-31 from per-repo probes (root listings): 177 blocks
(168 k, 1 s, 8 a), 75 active-status advisories for repos without blocks;
dormant/template/fork/personal/orphan repos carry no block. All blocks
carry `status: draft` (adoption in progress) except `spec-standards`
(`current`).

## Consequences

- Positive: docs posture is auditable exactly like crate health; drift
  between claimed and actual llms.txt/spec files is caught by
  `spec-audit.py --remote`.
- Negative: repos adopt `draft`, so the honest state until the sweep
  lands is visible in the registry; advisories stay until blocks are
  earned.
- Risks: block rot (last_audit aging); spec-audit flags repos audited
  more than 90 days ago.

## Alternatives considered

| Alternative | Pros | Cons | Reason rejected |
|---|---|---|---|
| Separate docs.yml registry in spec-standards | no change here | two registries of record; the estate already has exactly one | violates single-registry principle |
| Enforce path existence in this auditor | one-stop audit | adds GitHub content calls per repo to an audit that already walks crates.io | existence/staleness stay in spec-audit --remote |
