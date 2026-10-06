# LOOP.md — the Omni improvement loop

The estate is never "done". This is the repeating loop that keeps the
templates market-leading. One loop = one focused pass; run it roughly
monthly or after any major ecosystem shift.

## The loop

1. **Survey the market** (~1h): search for new/updated templates per
   language (cookiecutter, cargo-generate topic, very_good_templates,
   golang-standards, Starlight showcase, terraform-best-practices). Note
   any feature that appears in 2+ leaders.
2. **Diff against OMNI-CORE + COMPETITIVE-ANALYSIS.md** (~1h): mark new
   ✅/🔶/❌ in the matrix. Anything two leaders ship that we lack goes on
   the backlog with the loop number.
3. **Pick the top 3–6 backlog items** by (leverage × frequency ÷ risk).
   Maximalist ≠ everything: a feature must not violate the contract
   (scripts canonical, one source of truth, no CI-only steps).
4. **Implement estate-wide** via a sweep (same file lands in every
   template, language-tailored), never per-repo one-offs.
5. **Test the estate**: every template's main CI green; devcontainer both
   flavors green; new jobs advisory until stable, then promoted to gates
   (MUTATION.md promote pattern).
6. **Update the matrix + this file** with the loop's date and outcome, and record any
   new failure mode in [PITFALLS.md](PITFALLS.md).
7. **Publish**: engineering-standards PR (docs + shared gates), then the
   sweep PRs per template.

## Graduation policy (advisory → gate)

A new job (zizmor, osv, scorecard, cross-platform) lands **advisory**
(`continue-on-error: true`) for exactly one loop. It graduates to a
blocking gate when it has been green — or triaged with a written waiver —
for the whole loop. Nothing jumps straight to blocking.

## Loop log

| Loop | Date | Outcome |
|---|---|---|
| 2 | 2026-10-05 | Research step first: pulled OAuth 2.1 `-16`, WebAuthn L3, BIP-32/39/44/84, ISO 4217/20022 and the rounding authorities (ISO 80000-1, ASTM E29, GB/T 8170-2008, ZATCA E-Invoicing vF), then acted on what they said. Five defects found and fixed at source rather than documented: `multi-chain-wallet` refused every BIP-39 phrase under 24 words; `webauthn-kit` accepted an equal signature counter and shipped with six red tests built from the wrong COSE label; `actor-kit` deadlocked a paused actor and then stranded work queued during suspension; `shared-state` never re-exported `TtlCache`; `oauth-toolkit` took the PKCE method as a `&str`. One fix was then **corrected by the research** — L3 §7.2 calls a counter regression a signal, not proof, so the estate's own 0.3.6 hard-fail became a policy choice. New repo `double-entry` (the accounting core) published with a consumer suite in the same loop; `estate-audit.py` caught the resulting pin drift on its own. |
| 1 | 2026-10-05 | COMPETITIVE-ANALYSIS.md + PITFALLS.md; AGENTS.md + llms.txt estate-wide; OpenSSF Scorecard + zizmor + osv-scanner workflows (advisory); macOS+Windows CI legs (Rust/Go/TS/Python) — Rust green on both first try; nix devcontainer flavor repaired (official installer, no GHCR feature) and promoted advisory → gate; TypeScript pinned to 6.x estate-wide (TS 7 breaks `astro check` + knip) with dependabot guards; msrv gate made un-bumpable (`master` + `toolchain` input); OmniPython docs moved to the Pages artifact flow. Graduated to blocking gates: the nix devcontainer flavor (all 10 templates) and the macOS/Windows CI legs (Rust/Go/TS/Python) — both were advisory all loop and came back clean, which is the bar the policy sets. Backlog: git-cliff/release-please, REUSE.toml, perf budgets, Copier updates, legacy-template migration. |
| 2 | 2026-10-06 | Performance budgets estate-wide: one shared comparator (`scripts/compare-bench.py`, identical in all ten templates) that gates on **statistics + exactness** instead of a naive percentage. Microbenchmarks gate via a z-test noise band (criterion std-dev, pytest-benchmark std-dev, spread of five Go runs); byte budgets (site, flash/RAM, `.olean`) gate at 5%; bare wall-clock on shared runners is reported, not gated. `perf` job landed advisory. Also fixed a loop-1 regression: OmniPython was missing AGENTS.md/llms.txt on main. Backlog: Haskell criterion bench component (loop 3), changelog automation, Copier updates, REUSE.toml, legacy templates. |
| 3 | 2026-10-06 | Determinism made real: `scripts/repro-check.sh` in all ten templates - build twice from a clean state with a pinned `SOURCE_DATE_EPOCH`, compare artifact hashes. Gated where the toolchain is deterministic (Rust, Go, Python, TS, Docs, Lean, Dotfiles), reported with the reason where it embeds timestamps/build ids (Haskell, Embedded, Infra). Loop-3 finds: OmniRust's `reproducible-build.sh` existed and was named in ADR-0004 but had **no make verb and no CI job**; `uv build` fails at a `package = false` workspace root (needs `--all-packages`); chezmoi's `run_once_` chatter pollutes a captured manifest and fakes a mismatch. Locally verified reproducible: Python (wheels + sdists), TS/Docs sites, Lean `.olean`, Dotfiles renders, Rust release rlibs. |

## Backlog

See [COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md) § "Backlog".
