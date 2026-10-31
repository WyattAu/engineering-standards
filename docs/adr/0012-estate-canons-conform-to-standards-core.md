# ADR-0012: The estate canons conform to STANDARDS-CORE

**Status:** Accepted
**Date:** 2026-10-31

## Context

`standards` (L0) defines what a standard is: identity, layering with
tighten-only inheritance, invariant anatomy (id/statement/why/
enforcement), dependency mechanics, lifecycle, gates, projections. This
repo (L1 universal canon) and spec-standards predate it.

## Decision

engineering-standards declares conformance to STANDARDS-CORE v0.1 as an
L1 canon: OMNI-CORE is its invariant table (the four-field anatomy was
already in production), the gate matrix is its enforcement surface, and
domain standards in `standards/` may tighten but never loosen OMNI-CORE.
The standards-side freshness machinery (SC-11/11p) covers any future
projections of this canon.

## Consequences

- Positive: one meta-standard; domain standards resolve their inheritance
  against both canons through the standards registry.
- Negative: canon changes now also owe attention to the L0 anatomy rules
  (they already satisfied them in practice).
