# DEPENDENCY-COOLDOWN: update cooldown policy

> **Status: ACCEPTED (v0.1.0, 2026-11-09).** Ratification: ADR-0020.
> Implements [OMNI-CORE.md](./OMNI-CORE.md) invariant 11d.

Package releases must age before automated adoption so that a compromised
release is likely to be detected or withdrawn before it enters the estate.
Dependabot security updates bypass version cooldowns by design and are not
delayed by this policy.

Machine check: `scripts/check-dependabot-cooldown.py`. Rule IDs: `CD-*`.

## CD-1. Dependabot configuration exists

A repository that uses Dependabot for dependency updates MUST contain
`.github/dependabot.yml` (or `.github/dependabot.yaml`). Repositories that
have no package ecosystem or action dependencies managed by Dependabot are
out of scope for this file but should record that fact in review; the
machine check applies when the file is present and to repos that declare
themselves in scope via the gate.

## CD-2. Every update entry declares a cooldown

Each entry in `updates:` MUST include a `cooldown:` mapping. An entry
without `cooldown:` does not satisfy 11d.

## CD-3. Cooldown minimums (OMNI-CORE 11d)

Cooldown values MUST meet or exceed:

| Ecosystem kind | Minimum |
|---|---|
| `github-actions` | `default-days: 7` (semver fields are not valid for this ecosystem) |
| All other ecosystems | `semver-major-days >= 30`, `semver-minor-days >= 7`, `semver-patch-days >= 3` |

For non-`github-actions` ecosystems, `default-days` MAY be used as a
baseline only when it is >= 30 (covering all semver classes); otherwise the
semver-specific fields MUST be present at or above the minimums. A
`default-days` value below the required minimum for a class that is not
explicitly overridden is a finding.

## Scope and limits

`check-dependabot-cooldown.py` validates the presence and declared values of
cooldown settings in one repository. It does not verify that Dependabot runs
successfully, that all ecosystems in use are listed, or that lockfiles are
committed (11d also requires committed lockfiles; that is a separate concern).
Security-update bypass behavior is Dependabot-defined and not gated here.
