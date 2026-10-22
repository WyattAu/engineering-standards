# AGENTS.md: instructions for AI coding agents

Project: **engineering-standards**: the shared contract, gates, and shared
workflows every repo in the WyattAu estate derives from. Changes here move
faster and further than anywhere else in the estate: this repo *is* the
standard.

## Non-negotiable contract

1. **Measure, never assume.** Every claim about a tool, gate, or performance
   characteristic is backed by a measurement recorded in the same commit.
   "Evaluated and rejected" is a first-class outcome (see ADR-0007's original
   verdict, kept verbatim next to its superseding amendment).
2. **Never weaken a gate to make it pass.** A gate that fails for a reason you
   do not understand stays red until the cause is understood and fixed at the
   source. Lowering a threshold requires an ADR with the measurement that
   justified it.
3. **New jobs land advisory for exactly one loop, then graduate.** Advisory
   (`continue-on-error`) is a staging state, not a resting state. Loop 25's
   `llms-links` and loop 26's `pin-consistency` shipped advisory-in-spirit and
   were gating within the loop.
4. **One source of truth per concern.** Pins, policy, licensing, and scope each
   live in exactly one file (`REUSE.toml`, `estate.yml`, the gate scripts).
   Never add a parallel config that can disagree with the first.
5. **Scripts are canonical; workflows call them.** CI runs `scripts/*`, never
   an inline copy of a script. A gate that exists only in YAML is a gate a
   developer cannot run locally.
6. **Decisions get ADRs** (`docs/adr/NNNN-*.md`): Status, Context, Decision,
   Consequences. Superseding an ADR keeps the original text visible: the
   record of being wrong is more valuable than the record of being right.
7. **Gates must be able to lie.** Any check whose result depends on the
   credential it runs with must prove it is entitled to the claim it makes
   (loop 25: an audit asserted repo absence from a token that could not see
   private repos, red for six nights).

## Loop protocol

`LOOP.md` is the runbook: survey → diff against the market matrix
(`COMPETITIVE-ANALYSIS.md`) → rank by leverage × frequency ÷ risk →
estate-wide sweep → test → publish. Each iteration appends a row and states
the next iteration's contract. `PITFALLS.md` records what cost time; it is
written for the next agent, not for the record.

## Layout

| Path | Purpose |
|---|---|
| `OMNI-CORE.md` | the family-wide contract every template implements |
| `LOOP.md` | iteration log + doctrine (survey, graduation, publish) |
| `PITFALLS.md` | lessons that must not be relearned |
| `COMPETITIVE-ANALYSIS.md` | market matrix vs leading templates |
| `estate.yml` | registry of record for every repo (area, status, scope) |
| `docs/adr/` | decisions, including superseded ones |
| `scripts/` | canonical gate implementations + their self-tests |
| `.github/workflows/` | shared kit workflows consumed by all templates |
| `templates/` `specs/` `config-kit/` | material consumed by the estate |

## Gates owned here

- `estate-audit`: manifest vs GitHub vs crates.io vs consumer pins
- `llms.txt links`: no unresolved placeholders in any LLM contract
- `one pin per action`: one SHA per action across loop-owned repos
- `REUSE 3.3`: licensing compliance
- `zizmor`: workflow security lint (advisory)
- `scorecard`: OpenSSF posture (advisory)

## Stack

Python 3.12 (stdlib only; `pyyaml` in CI), bash scripts, GitHub Actions.
Local runs: `python -m pip install pyyaml` then `python scripts/estate-audit.py`.

## Refusals

Refuse to: paper over a red gate, delete a failing test to go green, invent a
measurement you did not take, or mark an ADR superseded without keeping its
original text.
