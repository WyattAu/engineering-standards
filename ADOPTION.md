# ADOPTION: when third-party code enters the estate

> **Status: PROPOSED (v0.1.0, 2026-11-09).** Ratification: ADR-0016.
> Registry: `candidates.yml`. Gate: `scripts/check-adoption.py`.

**Applies to:** every third-party project the estate considers taking code
from, whether as a dependency, a fork, or a rebuild.
**Oracle:** the candidate registry plus the API metadata recorded in it.

## Why this standard exists

"Should we fork this?" is usually answered by enthusiasm, and enthusiasm
does not pay maintenance. Three failure modes are already visible in the
estate: a dependency adopted before its licence was read, a fork that
diverged until it could no longer take upstream fixes, and a rebuild that
duplicated a crate already maintained here.

The rule this standard enforces is simple: **a decision names its licence,
its maintenance cost, and its overlap before it names its enthusiasm.**

## AD-1 Exactly one decision per candidate

**MUST.** Every candidate carries one of:

| Decision | Meaning | Commits the estate to |
|---|---|---|
| `adopt` | use as a dependency, pinned | tracking upstream releases |
| `fork` | maintain a downstream copy | rebasing, CI, security response |
| `rebuild` | own implementation | writing and maintaining it |
| `follow` | watch it, take no code | reading its changelog |
| `hold` | insufficient information | a review date |
| `reject` | not for this estate | nothing, and the reason is recorded |

- Evidence: `GATE` (`check-adoption.py`, closed vocabulary)
- Why: "we should look into it" is how a backlog becomes a graveyard. A
  `follow` with a review date is honest; a `fork` nobody rebases is debt.

## AD-2 A verified permissive licence is required to take code

**MUST.** `adopt`, `fork`, and `rebuild` require `license_verified: true`
and an SPDX id from the allowlist: `Apache-2.0`, `MIT`, `BSD-2-Clause`,
`BSD-3-Clause`, `ISC`, `MPL-2.0`, `Zlib`, `Unlicense`, `CC0-1.0`.
`MPL-2.0` is allowed only unmodified (file-level copyleft).

- Evidence: `GATE` (`license`, `license-unverified`)
- Why: AGPL, SSPL, BUSL, and GPL impose obligations the estate cannot meet
  for published crates and hosted sites. Reading the licence after the
  merge is how a licence problem becomes a legal problem. MPL is safe only
  while the files are untouched, so a fork of it is a trap.

## AD-3 Copyleft code is followed or rejected, never absorbed

**MUST.** A candidate under `AGPL-3.0`, `GPL-2.0`, `GPL-3.0`, `SSPL-1.0`,
`BUSL-1.1`, or `EUPL-1.2` may only be `follow` or `reject`.

- Evidence: `GATE` (`copyleft`)
- Why: these licences are compatible with *using* the software and
  incompatible with quietly vendoring it into a published crate or a hosted
  product. Studying the design and reimplementing the idea is lawful and is
  what `rebuild` means; copying the code is not.

## AD-4 A fork must be cheaper than a rebuild, and the numbers say so

**MUST.** A `fork` decision records: upstream `stars`, `pushed` date,
`open_issues`, and the estimated divergence in lines. It is rejected when
any of these hold:

| Condition | Threshold | Why |
|---|---|---|
| Upstream is stale | `pushed` older than 180 days | you inherit the maintenance |
| Upstream is a one-person project | contributors below 2, where known | bus factor of one |
| Divergence would exceed | 200 lines | past that it is a rewrite wearing a fork's clothes |
| Upstream has no releases | 0 tags | no rebase base to track |

- Evidence: `MEASURE` (recorded fields), `REVIEW` (divergence estimate)
- Why: a fork is a promise to merge someone else's future work. If upstream
  is not producing any, the fork is a rebuild with extra steps.

## AD-5 Overlap is measured before a rebuild is approved

**MUST.** A `rebuild` names the existing estate crate that covers the same
concern, or states `none`, and justifies the new implementation on a
measured axis (performance, correctness, licence, platform) with a number.

- Evidence: `REVIEW` plus the `overlap` field
- Why: the estate already carries 175 crates across four layers. A rebuild
  that duplicates `color-kit`, `docs-core`, or `crawlkit-engine` costs more
  than the feature it adds, and the layer model cannot absorb two homes for
  one concern (SPEC-CORE SC-1).

## AD-6 Stack and layer fit

**MUST.** `adopt` names the layer the dependency lands in (`L0` to `L3`,
per `docs/layers.md`) and must not point upward. Rust is preferred for
runtime code; TypeScript and Python are acceptable for tooling and docs
pipelines, not for substrate.

- Evidence: `GATE` (`layer` required for `adopt`), `REVIEW` (stack)
- Why: a JavaScript runtime in `L0` breaks `no_std` and the layer ceiling
  rule in one move. The stack question is not taste: it decides whether the
  crate can ever be used by the layers above it.

## AD-7 Adopted code is pinned, and its licence is re-checked on upgrade

**MUST.** `adopt` pins an exact version or revision (matching the estate's
pin discipline), and a major upgrade re-runs this standard rather than
assuming the licence and maintenance signals are unchanged.

- Evidence: `GATE` (pin consistency covers the resulting manifest)
- Why: licences change (Apache to BUSL has happened repeatedly), and a
  maintainer disappearing is not announced. The decision has a review date
  for the same reason.

## AD-8 Every field is sourced and dated, and unknowns are `null`

**MUST.** `candidates.yml` carries `measured` (ISO date) and a `source` per
candidate. Unknown values are `null`, never a guess. A `hold` names the
information that would resolve it.

- Evidence: `GATE` (`source`, `measured`, `rationale` length)
- Why: a registry of remembered star counts is worse than no registry,
  because it looks authoritative. The first run of this standard already
  forced one correction: a project described as "unmaintained" in memory
  had a release nine days ago.

## AD-9 Decisions expire

**MUST.** Every candidate carries `review_by` (ISO date, at most 180 days
after `measured`). A `hold` that is not resolved by then becomes `reject`
with that reason.

- Evidence: `GATE` (date arithmetic), `REVIEW` (quarterly sweep)
- Why: a hold is a question, and questions rot. The review date makes the
  cost of indecision visible instead of free.

## Using it

```sh
python3 scripts/check-adoption.py            # validate the registry
python3 scripts/check-adoption.py --json     # counts by decision
```

Adding a candidate: append a row to `candidates.yml` with the API values,
pick a decision, and write the reason in one sentence that a stranger could
disagree with.
