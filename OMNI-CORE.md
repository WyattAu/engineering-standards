# OMNI-CORE — the Omni template contract

Every repo in the [Omni template family](https://github.com/WyattAu?tab=repositories&q=omni-template)
(R, LaTeX, C++, Flutter, Python, Rust, TS, Go, Haskell, Embedded, Infra,
Dotfiles) ships these invariants. Derived projects inherit them; template
changes that violate one require an ADR in the template repo.

## The 12 invariants

| # | Invariant | Why |
|---|---|---|
| 1 | **Scripts are canonical; CI is a mirror.** `scripts/*` do the work; CI runs exactly those scripts. No CI-only steps. | "pipeline is the contract" — local green ⇒ CI green |
| 2 | **Thin `Makefile` wrapper** over scripts with the same verbs everywhere (`build test lint fmt fmt-check coverage contract ci`). | muscle memory across languages |
| 3 | **Monorepo-first**: `packages/*` / `crates/*` / cabal project / go.work — always with a demo **internal-dependency pair**. | repo = unit of consistency, package = unit of reuse |
| 4 | **Nix flake devShell** = system-dependency source of truth; the language-native lockfile owns language deps. direnv `.envrc`. | one toolchain pin shared by host/CI/containers |
| 5 | **Two devcontainer flavors**: image-based default + `.devcontainer/nix/` (nix+direnv → flake shell). Both built in CI. | user choice; neither rots |
| 6 | **pre-commit mirrors CI gates** — same formatters/linters, same failures. | hook failures are rehearsal, not surprise |
| 7 | **CI shape**: push(main)+PR + **monthly bitrot cron** + one **experimental allowed-fail leg** (next toolchain version) + concurrency cancel. | catches ecosystem drift; never blocks on tomorrow |
| 8 | **GitHub housekeeping**: dependabot (lang + actions, Mon, grouped), CODEOWNERS, issue templates, PR template, SECURITY.md, `.editorconfig`, `.gitattributes`. | hygiene is not per-repo taste |
| 9 | **Docs**: ARCHITECTURE.md (why) + README (how) + CONTRIBUTING + ADR dir + REQUIREMENTS.md + THREAT-MODEL.md for untrusted-input parsers. | decisions are dated, not re-litigated |
| 10 | **Security defaults**: explicit least-privilege `permissions:` per workflow, gitleaks + typos hooks, artifact attestation on releases, secret-redaction conventions. | templates ship safe by default |
| 11 | **Release**: CHANGELOG + tag; per-language publisher with provenance/attestation (release-plz / uv+trusted publishing / changesets / goreleaser / attested binaries). | reproducible, attributable artifacts |
| 12 | **Forgejo adapter**: thin `.forgejo/workflows/*.yml` calling the same scripts. | self-hosted mirroring stays cheap because scripts are canonical |

## Coverage tiers (informational defaults)

| Language | a | b | c |
|---|---|---|---|
| Rust (llvm-cov) | ≥90% | ≥80% | ≥70% |
| Python (pytest-cov) | ≥90% | ≥80% | ≥70% |
| Go (go test -cover) | ≥80% | ≥70% | ≥60% |
| Haskell (hpc) | ≥70% | ≥60% | ≥50% |
| C/C++ embedded | host tests + flash/RAM **size budgets** instead | | |

## Template naming

- `Omni{Lang}-template` — the scaffold (`OmniRust`, `OmniTS`, `OmniGo`, …;
  `OmniR` is taken by R).
- `Omni{Lang}-{variant}` — derivatives (`OmniLaTeX-CV`, `OmniCPP-docker`).
- Topics: `omni-template` + language + `template` (+ `monorepo`, `nix`,
  `devcontainer` where they apply). Every Omni is a **GitHub template repo**.
- License: **Apache-2.0** for all templates (commercial use expressly
  permitted). Estate crates keep their own licensing.

## Template vs estate

`apply-standards.sh` (and per-language variants) remain the idempotent way
to re-apply estate templates to *any* derived repo. Omni repos ship the
files pre-baked; both paths must produce the same result.
