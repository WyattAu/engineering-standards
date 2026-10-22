# Research program: 10 iterations (Oct 2026)

Method per iteration: **pull → analyze → compare → implement → re-prove.**

1. Pull the state of the art (papers, standards, tool docs: primary sources).
2. Analyze it against what this estate actually does today; find the delta in
   both directions (what we lack, and what we already do that others cannot).
3. Compare against the strongest reference repos (nixpkgs, deno, zig, rustc,
   Home Assistant, Google OSS Rebuild, step-security): did they solve it
   better, or is it an unsolved problem for them too?
4. Land the conclusion in the spec (`OMNI-CORE.md` / ADR / gate code).
5. Where the Lean template models an invariant, adjust the proof.

| # | Topic | Primary sources | Reference repos | Output |
|---|---|---|---|---|
| 34 | Reproducible builds & hermeticity | Lamb & Zacchiroli 2021; SLSA; reproducible-builds.org | nixpkgs, deno, zig, OSS Rebuild | repro gate v2 |
| 35 | Provenance & attestations | Sigstore/in-toto; SLSA provenance; GH artifact attestations | OSS Rebuild, sloths | SBOM + attest mandate |
| 36 | Dependency update policy | Renovate/Dependabot docs; cooldown research | Home Assistant, Grafana | update policy spec |
| 37 | Flaky tests & test selection | Meta Predator; Google flaky-test papers | rustc (highfive), chromium | flaky policy |
| 38 | Mutation testing vs coverage | cargo-mutants; mutmut; Stryker | tokio, polars | mutation gate (advisory) |
| 39 | Formal verification in CI | Lean 4/mathlib CI; Kani; hacspec | mathlib4, aws-lc | lean proof adjustment |
| 40 | Merge queues & trunk discipline | GitHub merge queue; bors | rust-lang, servo | merge-queue spec |
| 41 | SBOM + VEX + dependency review | CycloneDX vs SPDX; VEX; GH dependency-review | kubernetes, grafana | SBOM + review gate |
| 42 | Agent-facing repo interfaces | llms.txt; AGENTS.md conventions; MCP | openai/codex, anthropics | agent-interface standard |
| 43 | Runner hardening & cache poisoning | step-security/harden-runner; cache-poisoning research | step-security examples | harden-runner + cache rules |

Ground rules: no finding enters the spec without a source; no gate changes
without a local or CI measurement; anything we do better than the references
is written down as a claim others can check.
