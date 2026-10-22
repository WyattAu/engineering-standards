# Research note 36: dependency update policy

**Sources.** Dependabot cooldown GA (GitHub Changelog, July 2025) and the
July 2026 default change (3 days for all version updates); zizmor's
`dependabot-cooldown` audit; the 2026 TeamPCP campaign (Trivy -> KICS ->
LiteLLM) and the axios token compromise (UNC1069): malicious versions live
**2-3 hours** on the registries before takedown; Feross Aboukhadijeh's
(Socket) 7-day recommendation; Andrew Nesbitt, *Package Managers Need to Cool
Down*; uv ≥ 0.9.17 `exclude-newer` and pip 26 `uploaded-prior-to` as native
install-time mechanisms. Reference: Home Assistant (Renovate,
minimum-release-age), strapi/strapi#26438 (github-actions cooldown supports
`default-days` only).

## The threat model, stated precisely

Registry-resident malware has a **detection window** measured in hours (2026
campaigns: 2-3h) and an **exploitation window** measured in minutes: any CI
that resolves `latest` during those hours executes the payload. A cooldown
does not block the attacker; it makes *your automated adoption* lag the
takedown. Security-patch latency is the cost: which is why the policy must
exempt security updates (Dependabot does by design: cooldowns apply to version
updates only).

## Estate policy (adopted loop 36, all 13 loop-owned repos)

| update class | cooldown | rationale |
|---|---|---|
| semver-major (language deps) | 30 days | breaking-change review period + maximal takedown odds |
| semver-minor | 7 days | Feross/Socket default; covers the observed 2-3h attack window with margin |
| semver-patch | 3 days | GitHub's own new default; patches are small and diffable |
| github-actions | 7 days (`default-days` only: semver fields are invalid for this ecosystem, strapi#26438) | actions run with repo secrets; the compromise class is the most dangerous |
| Dependabot security PRs | **no delay** | exposure to a *known* CVE beats exposure to a hypothetical poison |

## Estate-specific notes

- **Install-time is already cold.** The estate installs from committed
  lockfiles (`uv sync --frozen`, `--locked`, `bun install --frozen-lockfile`),
  so `latest` is never resolved at build time; the cooldown governs when the
  *lock* may move. Defense in depth option filed: uv's `exclude-newer` would
  additionally time-anchor lock regeneration.
- **Renovate equivalence.** Renovate's `minimumReleaseAge` is the same control
  with a different name; the estate's Dependabot choice is unaffected.
- The zizmor `dependabot-cooldown` warnings that motivated this loop are
  resolved by this configuration.
