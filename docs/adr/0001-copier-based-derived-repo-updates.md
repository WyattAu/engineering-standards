# ADR-0001: Copier adoption for derived-repo updates

- **Status**: Accepted (loop 9 — implementation lands in loop 10)
- **Date**: 2026-10-08

## Context

GitHub *template repos* copy once. Everything the Omni estate has built since —
265 pinned actions, perf/repro gates, licensing manifests — reaches a derived
repo only if that repo re-clone-and-diffs by hand. The one structural feature
the market leaders have that we lack is **in-place updates of derived repos**.
`copier update` is that feature: it replays template changes onto a derived
repo while preserving the answers and local edits.

## Decision

**Adopt Copier in two phases, without breaking what exists.**

1. **Phase 1 (loop 10): answers contract.** Every template gains a
   `.copier-answers.yml` schema (project slug, language tier, feature flags)
   and a `copier.yml` question set whose defaults reproduce today's template
   exactly. `copier copy` output must be **byte-identical to the current
   template** — verified in CI by copying into a scratch dir and diffing
   against the repo. Zero behavior change is the acceptance test.
2. **Phase 2 (loop 11): drift service.** A scheduled workflow copies each
   template with pinned answers and opens a PR when the diff is non-empty —
   the estate's own update channel, dogfooding the same gates.

Non-goals: converting consumers' local edits into template variables;
supporting Copier < 9.

## Consequences

- **Good**: derived repos get `copier update` with three-way merge; the estate
  gains a machine-checkable "template == scaffold" invariant it does not
  currently have.
- **Cost**: two sources of truth for one file set (repo file vs Jinja
  template) during migration — the byte-identical diff test is the control.
- **Cost**: `{{ }}` delimiters collide with workflow expression syntax
  (`${{ }}`); the migration must set Copier's `skip_if_exists`/renderer
  options per file type.
- **Not chosen**: `degit`-style re-scaffold (loses local history and edits).
