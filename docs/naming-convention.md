# WyattAu Estate Naming Convention

Authoritative naming reference for the WyattAu estate. Every repository name,
crate name, and rename decision is governed by this document. When a name
disagrees with this convention, either the name or this document is wrong —
fix one of them.

## The 6 Rules

### Rule 1 — Repo name = crate name

Every repository publishes exactly one crate, and the two names are identical.

**Rationale.** A repo and its published crate are the same artifact with two
doors. Divergent names force a lookup table to answer "where does this crate
live?" (the estate previously carried exactly such a table in
`docs/layers.md` — 17 mismatches), break `gh repo clone WyattAu/X` ↔
`cargo add X` symmetry, and make `scripts/apply-standards.sh`-style tooling
guess. One name, zero translation.

### Rule 2 — Domain-specific: `{domain}-{concern}`

A crate that only makes sense inside one vertical domain is named
`{domain}-{concern}`: a short lowercase domain prefix, then the specific
concern it addresses (e.g. `decimal-money`, `tamper-audit`).

**Rationale.** Domain stacks self-organize: on crates.io search, docs.rs
reverse-dependency pages, and in `Cargo.toml` files, every member of a stack
sorts and reads together. The name states scope (which domain) and function
(which concern) without opening the README.

### Rule 3 — Cross-cutting: `{concern}-kit`

A crate usable across many domains — retry, shutdown, fetch, outbox — is named
`{concern}-kit`, hyphenated. The hyphenated form is canonical for all new
names; the legacy unhyphenated `*kit` form is closed to new crates.

**Rationale.** `-kit` is the estate's brand for shared infrastructure: it
marks "this is general-purpose, bring it anywhere." The hyphen keeps the
concern readable at a glance (`fetch-kit`, not `fetchkit`) and cleanly
separates new-convention crates from grandfathered legacy names (Rule 6), so
a reader can tell at a glance which era — and which owner — a name came from.

### Rule 4 — Unique primitives: short names

A crate that is a foundational primitive with no meaningful domain/concern
decomposition gets a short, memorable name: `chronoshift`, `breaker`,
`salting`, `typedids`, `vane`.

**Rationale.** Forcing taxonomy onto a primitive produces noise
(`time-source-kit`), while a short name is cheap to type, easy to remember,
and — precisely because the crate has no peers — loses nothing by not
encoding structure. These names function as brands; spend the effort there
instead.

### Rule 5 — Products: product name

A crate or repo that *is* a product keeps the product's name: `homebite`,
`clawdius`, `forgeyard`, `kestrel`. Do not force product repos into the kit
taxonomy.

**Rationale.** Products own their identity; a product named
`meal-planning-kit` obscures it and invites the question of which other
crates share the `meal-planning` stack when none do. Taxonomy naming is for
libraries composed into things; products are the things.

### Rule 6 — Grandfathering: established names stay until next major

Established names that predate this convention keep their names. They are
renamed only at their next major (semver-breaking) release, where the rename
ships together with the breaking change and a `CHANGELOG.md` entry.

**Rationale.** A rename is paid for by every downstream user: dependency
edits, docs links, muscle memory, and search equity. Bundling the rename with
an already-breaking release amortizes that cost into a single migration
instead of two.

## Repo/Crate Mismatches

Rule 1 violations in the estate, and the fix for each. The crate name is
already convention-correct in every case — the **repo is renamed to match the
crate**, never the reverse:

| Repo (current) | Published crate | Fix | Convention violated |
|---|---|---|---|
| `graceful` | `shutdown-kit` | rename repo → `shutdown-kit` | Rule 3 — an adjective with no concern; this is a cross-cutting graceful-shutdown kit |
| `money` | `decimal-money` | rename repo → `decimal-money` | Rule 2 — `money` is too generic; the decimal representation (the actual scope) is invisible |
| `auditlog` | `tamper-audit` | rename repo → `tamper-audit` | Rules 2/3 — the defining property (tamper-evidence) is missing from the name |
| `retry-backoff` | `loop-retry` | rename repo → `loop-retry` | Rule 3 — names the mechanism (backoff) instead of the concern (retrying loops) |
| `fetchkit` | `fetch-kit` | ✅ done (repo + crates.io) | Rule 3 — legacy unhyphenated form; `fetchkit` on crates.io was also owned by an unrelated project |

See [Renaming existing repos](#renaming-existing-repos) for the exact
commands. The remaining four require owner execution.

## Grandfathered Names

Per Rule 6, these established names are **kept as-is** and rename only at
their next major release:

- `webhookkit`
- `blobkit`
- `cryptkit`
- `validkit`
- `tokenkit`

These are Tier A security-critical crates with large downstream surfaces —
exactly the case where rename churn must ride a breaking release. Do not
"fix" them opportunistically. New crates may not use the unhyphenated `*kit`
form (Rule 3).

## Domain-Stack Naming Template

For a vertical stack (a family of crates serving one industry or file/domain),
apply Rule 2: one shared `{domain}` prefix, one crate per `{concern}`:

```
{domain}-{concern}
   │        │
   │        └── the specific capability (one or two words, lowercase)
   └── the stack: short, one word, lowercase, identical across the stack
```

| Stack | Crates under the template |
|---|---|
| automotive | `auto-can`, `auto-obd`, `auto-uds`, `auto-vin` |
| font | `font-shaping`, `font-raster`, `font-outline`, `font-hinting` |
| DSP | `dsp-filter`, `dsp-fft`, `dsp-window`, `dsp-convolve` |
| audio | `audio-mixer`, `audio-codec`, `audio-device`, `audio-wav` |
| sheet | `sheet-parse`, `sheet-formula`, `sheet-calc`, `sheet-render` |

Template rules:

- **One stack, one prefix.** Never fork prefixes within a stack
  (`car-can` + `vehicle-obd` is a violation; pick `auto-` and stay there).
- **The prefix must be earned.** A crate is domain-specific only if it could
  not be published without the domain. Retry logic inside an automotive
  service is still `loop-retry` (Rule 3), not `auto-retry`.
- **Keep the prefix minimal.** `auto-`, not `automotive-`; short prefixes
  survive long concern suffixes (`auto-uds-negotation`-class names stay
  readable).
- **Dedicated stack conventions beat general ones.** `dsp-fft` names the DSP
  implementation; the FFT as a generic primitive would be a Rule 4 short
  name. The prefix declares *whose* FFT it is.

## Naming Decision Flowchart

Apply in order; first match wins:

```
                 ┌──────────────────────────────┐
                 │  What is this crate/repo?    │
                 └──────────────┬───────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │ Is it domain-specific?            │
              │ (meaningless outside one vertical)│─── yes ──▶ {domain}-{concern}
              └─────────────────┬─────────────────┘           (decimal-money, auto-can)
                                │ no
              ┌─────────────────┴─────────────────┐
              │ Is it cross-cutting?              │
              │ (useful in many domains)          │─── yes ──▶ {concern}-kit
              └─────────────────┬─────────────────┘           (shutdown-kit, fetch-kit)
                                │ no
              ┌─────────────────┴─────────────────┐
              │ Is it a unique primitive?         │
              │ (foundational, no decomposition)  │─── yes ──▶ short name
              └─────────────────┬─────────────────┘           (chronoshift, breaker)
                                │ no
              ┌─────────────────┴─────────────────┐
              │ Is it a product?                  │─── yes ──▶ product name
              └─────────────────┬─────────────────┘           (homebite, forgeyard)
                                │ no
                                ▼
                     Escalate: raise it as an
                     engineering-standards issue.
                     Do not invent a fifth category
                     unilaterally.
```

Or as a decision list:

1. Is it domain-specific? → `{domain}-{concern}`
2. Is it cross-cutting? → `{concern}-kit`
3. Is it a unique primitive? → short name
4. Is it a product? → product name

## Renaming existing repos

The four remaining Rule 1 mismatches need **owner execution** (repo rename
requires owner/admin permission on the repository):

```bash
# graceful → shutdown-kit  (crate already publishes as shutdown-kit)
gh repo rename shutdown-kit --repo WyattAu/graceful --yes

# money → decimal-money    (crate already publishes as decimal-money)
gh repo rename decimal-money --repo WyattAu/money --yes

# auditlog → tamper-audit  (crate already publishes as tamper-audit)
gh repo rename tamper-audit --repo WyattAu/auditlog --yes

# retry-backoff → loop-retry (crate already publishes as loop-retry)
gh repo rename loop-retry --repo WyattAu/retry-backoff --yes
```

After each rename, GitHub redirects the old repo URL and git remotes
automatically, but finish the job:

```bash
# 1. Update every local clone of the repo:
git remote set-url origin https://github.com/WyattAu/<new-name>.git

# 2. Update estate registries that name the repo:
#    - scripts/estate-crates.txt and scripts/estate-tiers.json (this repo)
#    - KITS.md and site/src/lib/kits.ts (next scheduled sync)
#    - any README badge/crate table in the renamed repo

# 3. Verify CI went green on the renamed repo (workflows move with the repo;
#    third-party services pinned to the old name may not).
```

Note the asymmetry: the crate names above are already fixed and published —
the rename is repo-side only. Nothing is re-published, no version bumps, no
breaking change. That is the point of Rule 1: it converts every future
crate/repo mismatch into a zero-crate-impact repo rename.

## Rule 1 is enforced by `scripts/check-repo-crate-alignment.py`

Nothing checked this until now, which is why 17 mismatches accumulated. CI
runs fine against whatever a repo happens to be called, so the drift is
invisible until someone looks — and it is not cosmetic: a crate published as
`shutdown-kit` whose crates.io `repository` field says `.../graceful` sends
readers somewhere that does not match the crate name, and a doc link that
looks wrong is a doc link people stop trusting.

```sh
# audit every repo in the org (needs a token with repo:read)
python3 scripts/check-repo-crate-alignment.py --owner WyattAu

# audit one local checkout, no network
python3 scripts/check-repo-crate-alignment.py --cwd ../some-repo

# gate form: fail while any mismatch remains
python3 scripts/check-repo-crate-alignment.py --owner WyattAu --enforce
```

It runs in the `estate-audit` workflow (on manifest edits and nightly),
**reported and not gated** — the outstanding work is a deliberate owner
batch, and failing the run would block unrelated merges until it happens.

### Monorepos are not violations

Rule 1 applies per *published crate*, so a repo publishing several crates is
named for the product and needs no rename: `vane` (11 crates), `suture` (38),
`polyfont` (9), `plychart`, `typed-id`, `crawlkit`, `eventbus`. Telling that
apart from a single-crate repo is the whole difficulty, and the checker does
it by counting publishable workspace members.

A repository that publishes nothing at all — services, docs, dotfiles, Homebrew
taps, the standards repo itself — is likewise fine, and is listed in the
script's `NO_CRATE` set.

### Current state

| Verdict | Count |
|---|---|
| repo name == crate name | 81 |
| monorepo (named for the product) | 7 |
| **pending rename** | **17** |
| not a Rust crate (or an empty repo) | 63 |

The 17 are enumerated in the script's `GRANDFATHERED` table, each with its
exact `gh repo rename` command and the reason it drifted (a crates.io
collision forced a crate rename, or the crate was renamed inbound and the repo
never followed). Remove an entry when its rename lands; the checker then holds
that repo to Rule 1 permanently.

## Template estate (Omni)

Templates follow their own namespace, orthogonal to crate names:

- **`Omni{Lang}-template`** — the scaffold. `OmniRust`, `OmniTS`, `OmniGo`,
  `OmniHaskell`, `OmniEmbedded`, `OmniInfra`, `OmniDotfiles`, plus the
  originals (`OmniR`, `OmniLaTeX`, `OmniCPP`, `OmniFlutter`, `OmniPython`).
  `OmniR` is taken by R, hence Rust is `OmniRust` — no collisions.
- **`Omni{Lang}-{variant}`** — derivatives (`OmniLaTeX-CV`,
  `OmniLaTeX-coverletter`, `OmniCPP-docker`, `OmniLaTeX-docker`).
- **Topics**: `omni-template` + language + `template` on every member
  (+ `monorepo`, `nix`, `devcontainer` where applicable). Every Omni is a
  GitHub **template repo** so "Use this template" appears.
- **License**: Apache-2.0 across the template estate (commercial use
  expressly permitted). Crate licensing rules are unchanged.
- **Contract**: all templates conform to [OMNI-CORE.md](../OMNI-CORE.md).
