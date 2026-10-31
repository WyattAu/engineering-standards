# ADR-0011: Omni templates carry the spec/doc standard (OMNI-CORE 11p)

**Status:** Accepted
**Date:** 2026-10-31

## Context

New repos inherit OMNI-CORE through the Omni templates, but the
specification/documentation standard (`spec-standards`, SPEC-CORE) was
adopted per-repo after creation: 2026-10-31 swept the existing estate
(record: spec-standards `docs/sweep-2026-10-31.md`). Repos created from
templates would repeat the sweep cycle forever.

## Decision

Every active Omni template ships, and therefore every derived repo is
born with: the shared docs workflow (`docs.yml`, tier k) + monthly bitrot,
canonical `.markdownlint.json`, the SPEC/TRUTH-TABLE/RESEARCH_LOG/ADR
skeletons under `docs/templates/`, and an `llms.txt` projection. New
invariant OMNI-CORE **11p** (projection freshness): packaged projections
of estate canons (skills, MCP servers, doc sites) declare their source
rev, are rebuilt by CI, and a stale projection fails the canon gate.
First consumers of 11p: the standards skill pack + MCP server in
`standards-dist`.

## Consequences

- Positive: born-conformant repos; adoption debt stops accruing; the
  2027-01/2027-04 blocking flips only have to cover the legacy estate.
- Negative: template CI now runs the docs gate; derived repos gain two
  workflows and four skeleton files.
- Risks: skeleton drift vs spec-standards templates; tracked by the
  projection gate when standards-dist lands.

## Alternatives considered

| Alternative | Pros | Cons | Reason rejected |
|---|---|---|---|
| Post-creation adoption only (status quo) | no template churn | every new repo re-accrues sweep debt | rejected: construction beats correction |
| Fold into copier update hooks only | no template file changes | hooks rot; not visible in template review | visible scaffolding wins |
