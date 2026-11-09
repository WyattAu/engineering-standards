# ADR-0015: commits are a gated contract

- **Status**: Proposed (2026-11-09). Ratification pending; advisory until then.
- **Date**: 2026-11-09
- **Complements**: ADR-0013 (standards model), OMNI-CORE 11 (release)
- **Supersedes**: nothing

## Context

The estate writes Conventional Commits by habit across hundreds of
repositories, and release tooling (`release-plz`, `changesets`, `goreleaser`
grouping) already parses them. Nothing checked them. The 2026-11-09 sweep
found commits in the shared canon that mixed a dependency bump with a
behavioural change, and subjects long enough to be truncated in every
`--oneline` view.

Two costs are specific to this estate:

1. **Release automation reads the type.** A lowercase `breaking change:`
   footer is ignored by every parser, so a major change ships as a patch.
2. **History is the only durable artifact.** Forks, mirrors, and the Forgejo
   adapter (OMNI-CORE 12) all lose PR metadata; the commit is what survives.

## Decision

1. **`COMMITS.md` states the contract** as CS-1..CS-9, each with a number,
   an evidence class, and a reason, per STANDARDS-MODEL.
2. **`scripts/check-commits.py` gates the mechanical subset** over a
   revision range: header grammar, closed type set, 50-character subject,
   trailing period, blank line, 72-column body, `BREAKING CHANGE:` casing,
   trailer position.
3. **Signature state is reported, not enforced.** `--require-signature`
   exists, but the default reports `n good / n unsigned / n bad`. Enforcing
   first would block every contributor whose key is not configured, which
   is a process failure disguised as a security gate.
4. **The type set is closed at eleven types** and a new one needs an ADR,
   so `git log --grep` and release-version inference stay meaningful.
5. **Advisory for one loop**, then blocking on the canon repository before
   any adoption push: the standard is dogfooded where it is written.

## Consequences

- **A malformed subject fails a check instead of being re-litigated in
  review**, and `breaking change:` in lowercase becomes a caught defect
  rather than a silently mis-versioned release.
- **The gate is local-first** (SC-9): it reads git, needs no network, no
  token, and no CI-only step, so a contributor can run the same command.
- **What it cannot check**: whether the body is readable, whether the commit
  is one logical change (CS-9). Those stay `REVIEW`, labelled as such.
- **Adoption risk**: history is not retroactively fixable. The gate applies
  to new ranges only; existing commits are measured once, in the index, and
  never rewritten.
