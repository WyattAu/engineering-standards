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
| 11g | **Trunk discipline** (GitHub merge queue; bors lineage): main is validated as a *grouped future state* via the merge queue, FIFO on green -- not as N independently-green PRs that go stale on landing. CI triggers on `merge_group`; protection rules target `main` exactly (no wildcards); the admin bypass used by automation is a recorded deviation, not a hidden one. | main is never stale relative to its checks |
| 11f | **Formal verification** (Lean kernel; mathlib CI practice): machine-checked properties live where the language supports them, and CI audits them -- `#print axioms` printed per theorem, any `sorry` fails the build, documented behavior is proven not just described. Non-formal gates are strong but empirical; the distinction is stated, not blurred. | specs that cannot rot |
| 11e | **Flaky-test policy** (Google Testing Blog; Mill; nextest): failed tests retry once, and the retry is reported as flake data -- blanket retries are masking. Test isolation is preferred over retrying (nextest per-test processes in the Rust kit; pytest-randomly order randomization in the Python kit). Quarantine = non-blocking + owner + ticket + 14-day expiry + written exit criteria; it never deletes or silently skips. | trustworthy CI signal |
| 11d | **Update policy** (RB report 2026-03; 2026 TeamPCP/axios campaigns): package releases age before automated adoption -- 30d majors, 7d minors, 7d github-actions, 3d patches; Dependabot security PRs bypass the cooldown by design. Lockfiles stay committed so build-time resolution is always cold. | takedown-window-resistant dependency adoption |
| 11c | **Provenance** (SLSA; Sigstore/in-toto): every *distributable* artifact gets build provenance bound to the publishing workflow's OIDC identity -- GH artifact attestations for files we ship, registry-generated provenance where the registry does it (npm --provenance, PyPI PEP 740). Repos with no distributable artifacts say so instead of claiming coverage. Publishers stay unarmed by default (fresh templates skip, not fail). | non-falsifiable provenance per artifact |
| 11b | **Reproducibility** (Lamb & Zacchiroli, IEEE Software 2022): a build is reproducible when *all legitimate inputs* — toolchain versions, epoch, locale, lockfiles, runner environment — are recorded per run (`.buildinfo`) and replicated, not merely the command. Gate = double-build artifact-hash compare + input-record comparison. Python-family artifacts additionally forbid bytecode caches (`*.pyc`, `__pycache__`): a deterministic poisoned `.pyc` passes hash comparison (RB report 2026-03). Toolchains that embed timestamps by design run in report mode with the mismatch explained (ADR-0006). | reproducible, diagnosable, poisoning-resistant artifacts |
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
