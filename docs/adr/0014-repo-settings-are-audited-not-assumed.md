# ADR-0014: repository settings are audited, not assumed

- **Status**: Proposed (2026-11-09). Ratification pending; advisory until then.
- **Date**: 2026-11-09
- **Complements**: ADR-0013 (standards model and index)
- **Supersedes**: nothing

## Context

`estate.yml` is the registry of record, but its keys are `area, crates,
docs, gated, notes, status, _seen`. None of them is a *setting*. As a
result, `OMNI-CORE 10` ("security defaults") and `11g` ("trunk discipline")
described controls that nothing could observe:

| Setting | State on 2026-11-09 |
|---|---|
| Branch protection on default branch | 0 of 8 sampled repositories |
| Workflows reacting to `merge_group` | 0 of 125 checkouts |
| Secret scanning | enabled in 3 of 5 sampled, off in starlight-sites and aether-core |
| Push protection | off in the same two |
| Dependabot security updates | off in 5 of 5 sampled |
| `gated: true` in the registry | 13 of 289 |

A rule with no observer is the failure mode ADR-0013 exists to prevent, and
the index listed these as `none` because no artifact said otherwise.

## Decision

1. **Requirements live in `settings-policy.yml`**, not in `estate.yml`: the
   registry keeps recording intent (area, status, docs), and policy records
   what must be true. This avoids a schema change to a document that other
   gates already parse.
2. **`scripts/audit-repo-settings.py` observes the four settings REST
   exposes** and reports adoption as a fraction (`n/checked`), per repo and
   per setting.
3. **Merge queue is reported `unknown`, never `pass`.** GitHub exposes no
   REST endpoint for it. Claiming coverage would be exactly the lie
   AGENTS.md rule 7 forbids, and `11g` stays `declared` in the index until a
   GraphQL check exists.
4. **Waivers are per repo, owned, reasoned, and dated**, and an expired
   waiver fails the audit (STANDARDS-MODEL SM-6).
5. **Advisory first.** The first run reports the estate as it is. Blocking a
   pull request because an unrelated repository lacks a setting it never had
   is how a gate gets deleted; LOOP.md graduation applies.

## Consequences

- **The gap becomes a number.** The index row for branch protection moves
  from `none` to `OMNI-CORE 10`, with adoption measured rather than
  guessed. `13/289 gated` stops being the only quantitative statement about
  estate posture.
- **Two failure modes become visible in CI**: a repository created without
  secret scanning, and a protection rule silently removed.
- **What this does not do**: it does not enable anything. Turning on
  protection or scanning is an owner setting change with notification
  effects on 289 repositories, so it stays a decision made on the numbers.
- **Cost**: 3 API calls per repo; the default sample is 25 (`--limit`), so a
  full sweep is a deliberate, rate-limit-aware run, not something every CI
  invocation does.
- **Honest limit**: a token that cannot see a private repository makes that
  repository look misconfigured. The audit fails loudly on API errors
  instead of counting them as "off", which is the entitlement discipline
  from loop 25.
