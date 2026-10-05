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
| 1 | 2026-10-05 | COMPETITIVE-ANALYSIS.md + PITFALLS.md; AGENTS.md + llms.txt estate-wide; OpenSSF Scorecard + zizmor + osv-scanner workflows (advisory); macOS+Windows CI legs (Rust/Go/TS/Python) — Rust green on both first try; nix devcontainer flavor repaired (official installer, no GHCR feature) and promoted advisory → gate; TypeScript pinned to 6.x estate-wide (TS 7 breaks `astro check` + knip) with dependabot guards; msrv gate made un-bumpable (`master` + `toolchain` input); OmniPython docs moved to the Pages artifact flow. Backlog: git-cliff/release-please, REUSE.toml, perf budgets, Copier updates, legacy-template migration. |

## Backlog

See [COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md) § "Backlog".
