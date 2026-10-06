# Competitive analysis — Omni templates vs. the market

Date: 2026-10-05 · Loop 1 · Sources: GitHub search + project docs (see
[LOOP.md](LOOP.md) for methodology). Star counts are direction, not merit.

## Market leaders per language

| Language | Leading templates | Their signature features |
|---|---|---|
| Rust | d-oit/rust-2026-template, carlosferreyra/rust-template, RAprogramm/rust-crate-template, hiranp/rust-cli-template, rust-cli/recommended structure | AGENTS.md + `.agents/skills/`, `llms.txt`, cargo-dist releases, git-cliff changelogs, xtask, mutation testing, mdbook docs, REUSE.toml licensing, just recipes, miette/completions (CLI) |
| Python | audreyfeldroy/cookiecutter-pypackage v0.5, osprey-oss/cookiecutter-uv (1.3k★), cookiecutter-uv-package, bosd/uv-forge | SHA-pinned actions, Sigstore attestation, PyPI trusted publishing, `ty` type checker, `just`, Zensical docs, release-please, tox-uv multi-version, deptry |
| Go | golang-standards/project-layout (de-facto), goreleaser examples | layout convention, goreleaser multiplatform + brew, govulncheck |
| Flutter | VeryGoodOpenSource/very_good_core (moved to very_good_templates), news_toolkit (1.4k★) | **100% coverage enforced**, Very Good Analysis strict lints, build flavors (dev/staging/prod), i18n, bloc architecture, mason bricks |
| Docs | Starlight official showcase, Docusaurus, VitePress | versioned docs, i18n, search, MDX |
| Terraform/IaC | antonbabenko/terraform-best-practices, pre-commit-terraform suite | pre-commit composition, module docs, policy gates |
| Lean | lean4/example, mathlib templates | minimal — thin competition |

## Feature matrix — Omni vs. best-in-class

Legend: ✅ ships today · 🔶 partial/advisory · ❌ absent · 🎯 exceeds market

| Capability | Omni | Best market | Verdict |
|---|---|---|---|
| Monorepo-first scaffold | ✅ all templates | rare (per-repo only) | 🎯 |
| Shared reusable CI gates | ✅ rust-kit/node-ci/python-kit/go-kit/haskell-kit | none share gates across languages | 🎯 |
| Kernel/formal gates | ✅ Lean proofs + Rust loom/miri | none | 🎯 |
| Property-based testing | ✅ Rust proptest, Python hypothesis, Haskell hedgehog | rare | 🎯 |
| Mutation testing (gate policy) | ✅ Rust weekly→gate | d-oit (periodic) | ✅ |
| Fuzzing | ✅ Rust cargo-fuzz, Go native | rare | 🎯 |
| Reproducible-build check | ✅ Rust double-build SHA-256 | none | 🎯 |
| Supply chain | ✅ cargo-vet + cargo-deny (Rust) | cargo-deny only | 🎯 |
| Coverage gates | ✅ tiered per language | VGV 100% (Flutter only) | ✅ |
| Artifact attestation | ✅ all release paths | cookiecutter-pypackage (Sigstore) | ✅ |
| AGENTS.md | 🔶 this loop | d-oit | → ✅ |
| llms.txt | 🔶 this loop | d-oit | → ✅ |
| OpenSSF Scorecard | 🔶 this loop | rare in templates | → 🎯 |
| zizmor (workflow lint) | 🔶 this loop | rare | → 🎯 |
| Performance budget gate | ✅ loop 2 | CodSpeed / benchmark-action | 🎯 |
| osv-scanner | 🔶 this loop (non-Rust) | rare | → ✅ |
| Linux CI | ✅ all | ✅ | ✅ |
| macOS CI | 🔶 this loop (Rust/Go/TS/Python) | common | → ✅ |
| Windows CI | 🔶 this loop (Rust/Go/TS/Python) | common | → ✅ |
| nix devShell | ✅ all | rare (some Lean/nix langs) | 🎯 |
| Dual devcontainers (image+nix) | ✅ all | none | 🎯 |
| Bitrot cron (monthly drift check) | ✅ all | none | 🎯 |
| Forgejo/self-hosted parity | ✅ all | none | 🎯 |
| 100% coverage mandate | ❌ (tiered 90/80/70) | VGV (Flutter) | ✅ tiered, deliberate |
| git-cliff / release-please changelogs | ❌ roadmap | common | backlog |
| cargo-dist style polyglot releases | ❌ roadmap (goreleaser ships for Go) | common | backlog |
| `just` task runner | ❌ (Makefile, deliberate) | common | — (contract choice) |
| REUSE.toml licensing | ❌ roadmap | RAprogramm | backlog |
| Multi-version test matrix | ✅ Python 3.12–3.14, GHC 9.6–9.10, Go old/stable/next | common | ✅ |
| Docs deploy zero-touch | ✅ OmniDocs | common | ✅ |

## Loop 1 outcome

Everything below shipped and is green on `main`. Two rows moved beyond the
plan: the nix devcontainer flavor was found to be **broken** (the GHCR feature
401s for anonymous pulls) rather than merely advisory, so it was repaired and
promoted from advisory to a blocking gate; and the TypeScript floor became a
hard constraint — TS 7 (native port) ships no programmatic compiler API, so
`astro check` and knip crash on it — recorded as a documented pin plus
dependabot guard, detailed in [PITFALLS.md](PITFALLS.md).

| Capability | Omni | Best market | Verdict |
|---|---|---|---|
| AGENTS.md | ✅ | d-oit | ✅ par |
| llms.txt | ✅ | d-oit | ✅ par |
| OpenSSF Scorecard (advisory) | ✅ | rare in templates | 🎯 |
| zizmor + osv-scanner (advisory) | ✅ | rare | 🎯 |
| macOS CI | ✅ Rust/Go/TS/Python | common | ✅ par |
| Windows CI | ✅ Rust/Go/TS/Python | common | ✅ par |
| Nix devcontainer that actually builds | ✅ | rare to ship nix at all | 🎯 |

## Gap-closing work in loop 1

1. **AGENTS.md** per template — agent contract: scripts canonical, `make ci`,
   guardrails (never weaken gates, never commit secrets).
2. **llms.txt** per template — machine-readable project summary.
3. **OpenSSF Scorecard** workflow (advisory, results as artifact) — all.
4. **zizmor** workflow — GH Actions security lint (advisory until estate
   tunes thresholds) — all.
5. **osv-scanner** workflow — TS/Python/Go/Docs (Rust already covered by
   cargo-deny + cargo-audit) — advisory until baseline noise is triaged.
6. **macOS + Windows CI legs** — Rust/Go/TS/Python (Embedded/Infra/Dotfiles/
   Haskell are platform-scoped by nature; Lean/Haskell docs targets stay
   Linux).

## Backlog for loop 2+ (ordered by leverage)

1. git-cliff (Rust/Go) + release-please (TS/Python) — changelog automation.
2. REUSE.toml licensing compliance job.
3. cargo-dist (Rust) + per-language performance-budget jobs
   (benchstat for Go, Codspeed for Python, tinybench for TS).
4. Windows-first fixes found by the new legs.
5. Copier-based in-place updates for derived repos (`copier update`), the
   one feature uv-forge has that GitHub template repos lack.
6. Migrate legacy Omni templates (LaTeX/CPP/Flutter/R) to the Omni Core
   Contract — owner-gated, per "don't touch OmniCPP" exception.
