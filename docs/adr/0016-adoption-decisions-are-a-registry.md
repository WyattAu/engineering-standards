# ADR-0016: adoption decisions are a registry, not a conversation

- **Status**: Proposed (2026-11-09). Ratification pending; advisory until then.
- **Date**: 2026-11-09
- **Complements**: ADR-0013 (standards model), `docs/layers.md`, `docs/naming-convention.md`
- **Supersedes**: nothing

## Context

The estate is 289 repositories and 175 published crates. New third-party
projects arrive weekly, and the decision to take code from one was made in
chat, in a PR comment, or not at all. Three specific costs are already
observable:

1. **Licence discovery after the fact.** A candidate with an AGPL licence
   is indistinguishable from an MIT one until someone reads it. The estate
   publishes crates and hosts sites, so the difference is not academic.
2. **Forks that cannot take upstream fixes.** A fork is a promise to merge
   someone else's future work; when upstream is a single maintainer with no
   releases, that promise cannot be kept.
3. **Rebuilds that duplicate owned code.** `color-kit`, `docs-core`, and
   `crawlkit-engine` already own colour maths, the docs pipeline, and
   crawling. A rebuild that re-covers one of them costs a layer violation
   as well as the implementation.

Meanwhile the candidate universe is loud: 400k-star repositories exist for
reverse engineering and agent orchestration, and star velocity is a poor
proxy for whether the code belongs here.

## Decision

1. **`ADOPTION.md` defines six decisions** (`adopt`, `fork`, `rebuild`,
   `follow`, `hold`, `reject`) with the evidence class each requires.
2. **`candidates.yml` is the registry.** Every field is measured from the
   GitHub API on a stated date; unknowns are `null`, never estimated.
3. **`scripts/check-adoption.py` enforces the rubric**: licence verified and
   allowlisted before code is taken, copyleft confined to `follow`/`reject`,
   layer named for `adopt`, rationale long enough to disagree with, and a
   `review_by` no more than 180 days out.
4. **`hold` is a first-class decision with an open question and an expiry.**
   Indecision is allowed; unrecorded indecision is not.
5. **Fork viability is numeric**, not a feeling: stale upstream, bus factor,
   no releases, and a 200-line divergence ceiling.

## Consequences

- **The first registry run produced a correction**: a repository the estate
  "remembered" as dead had a release nine days earlier, and two 100k-star
  projects turned out to be unverifiable on licence, which is now a `hold`
  rather than a silent assumption.
- **Adoption stays cheap and rejection stays cheap.** `follow` costs a
  changelog read and is the correct answer for most of the trending list.
- **What this does not do**: it does not audit the code of an adopted
  dependency, estimate real maintenance hours, or replace a security review.
  Those remain `REVIEW` and supply-chain gates (`cargo-deny`, `cargo-vet`).
- **Honest limit**: stars, issue counts, and last-push dates are proxies.
  The registry says so, records the date, and expires the decision rather
  than pretending the number is stable.
