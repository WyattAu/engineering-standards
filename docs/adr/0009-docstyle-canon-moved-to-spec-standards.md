# ADR-0009: DOC-STYLE canon moved to spec-standards

**Status:** Accepted
**Date:** 2026-10-31

## Context

DOC-STYLE.md lived in this repository but governs prose in every estate
repository, including those that consume no engineering gate. A new
repository, `spec-standards`, now owns specification and documentation
standards estate-wide (invariants SPEC-CORE SC-1..SC-10, prose rules,
tiered S/K/A/D gates, the docs registry schema, spec/doc templates).
Decision record for the split: spec-standards `docs/adr/0001-concern-split.md`.

## Decision

The DOC-STYLE canon moves to
[spec-standards/DOC-STYLE.md](https://github.com/WyattAu/spec-standards/blob/main/DOC-STYLE.md).
This repository keeps a pointer stub at the old path; the stub is a
pointer, never a fork (OMNI-CORE 11i pattern). The canon gained two
sections in the move: the spec-citation extension (SPEC-CORE SC-3) and
status-stamp/freeze rules (SPEC-CORE §5). The mechanical gate implementing
DOC-STYLE §1 is `doc-lint.sh` in spec-standards.

## Consequences

- Positive: one owner for prose rules; rules and their gate live in the
  same repo; engineering repo loses a concern it never gated.
- Negative: paths in kit linters that referenced this file must update in
  the docs-workflow sweep; the stub keeps old links resolving.
- Risks: a fork re-appearing; detected by the monthly bitrot link check
  and repo audits.

## Alternatives considered

| Alternative | Pros | Cons | Reason rejected |
|---|---|---|---|
| Keep DOC-STYLE.md here, referenced from spec-standards | zero migration | wrong owner; boundary between the two standards would be fictional | forks the concern spec-standards exists to own |
