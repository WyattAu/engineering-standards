# Competitive analysis: Omni templates vs. the market
| Lean | lean4/example, mathlib templates | minimal; thin competition |
## Feature matrix: Omni vs. best-in-class
| `just` task runner | ❌ (Makefile, deliberate) | common |; (contract choice) |
hard constraint; TS 7 (native port) ships no programmatic compiler API, so
`astro check` and knip crash on it; recorded as a documented pin plus
1. **AGENTS.md** per template; agent contract: scripts canonical, `make ci`,
2. **llms.txt** per template; machine-readable project summary.
3. **OpenSSF Scorecard** workflow (advisory, results as artifact); all.
4. **zizmor** workflow; GH Actions security lint (advisory until estate
   tunes thresholds); all.
5. **osv-scanner** workflow; TS/Python/Go/Docs (Rust already covered by
   cargo-deny + cargo-audit); advisory until baseline noise is triaged.
6. **macOS + Windows CI legs**; Rust/Go/TS/Python (Embedded/Infra/Dotfiles/
1. git-cliff (Rust/Go) + release-please (TS/Python); changelog automation.
   Contract; owner-gated, per "don't touch OmniCPP" exception.
Ten research iterations (docs/research/) moved the estate past the market matrix on: input-recorded reproducibility (`.buildinfo` + bytecode-cache guard; the 2026 PyPI-scale attack), OIDC-bound provenance on every distributable artifact, age-gated dependency adoption (30/7/3/7 cooldowns; security PRs exempt), flaky-test policy with per-test isolation (cargo-nextest) and order randomization (pytest-randomly), machine-checked properties with axiom audits (Lean; `#print axioms` + no-sorry CI gate), merge-queue readiness, CycloneDX SBOM on releases, a blocking dependency-review PR gate, the agent-interface standard (AGENTS.md single-source; CLAUDE.md pointer; llms.txt gated), and harden-runner audit mode on tag-triggered publishers. Open items are tracked in LOOP.md (iterations 40/43 triage list); not silently dropped.