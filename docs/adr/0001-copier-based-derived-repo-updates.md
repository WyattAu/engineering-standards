# ADR-0001: Copier adoption for derived-repo updates

- **Status**: Accepted (loop 9) — **phase 2 complete (loop 21)**: answers file ships as `.copier-answers.yml.jinja` rendering `_copier_answers`; update channel verified end-to-end
- **Date**: 2026-10-08 (loop 21 amendment 2026-10-09)

## Context

GitHub *template repos* copy once. Everything the Omni estate has built since —
265 pinned actions, perf/repro gates, licensing manifests — reaches a derived
repo only if that repo re-clone-and-diffs by hand. The one structural feature
the market leaders have that we lack is **in-place updates of derived repos**.
`copier update` is that feature: it replays template changes onto a derived
repo while preserving the answers and local edits.

## Decision

**Adopt Copier in two phases, without breaking what exists.**

1. **Phase 1 (loop 10): answers contract.** Every template gains a
   `.copier-answers.yml` schema (project slug, language tier, feature flags)
   and a `copier.yml` question set whose defaults reproduce today's template
   exactly. `copier copy` output must be **byte-identical to the current
   template** — verified in CI by copying into a scratch dir and diffing
   against the repo. Zero behavior change is the acceptance test.
2. **Phase 2 (loop 11): drift service.** A scheduled workflow copies each
   template with pinned answers and opens a PR when the diff is non-empty —
   the estate's own update channel, dogfooding the same gates.

Non-goals: converting consumers' local edits into template variables;
supporting Copier < 9.

## Amendment (loop 21): the answers file must be a `.jinja` template

Loops 10–12 shipped a **static** `.copier-answers.yml` (to make scaffolds carry
it). That was a latent defect: copier renders only `*.jinja` files, so the
static file — with its baked `_commit` — was replayed verbatim on every update,
pinning every derived repo's merge base to the bake-time commit. Untracking the
file instead makes `copier update` delete it (the old-version diff reads the
removal literally), and the update diff hard-excludes the answers path, so
nothing self-heals. Audit finding: 9 of 10 templates had never received the
file at all — their scaffolds could not update, period.

The corrected contract, verified end-to-end (mini-repo v1→v2, then a real
static→jinja transition where `_commit` advanced `ccad64b → v0.1.9`):

- every template ships `.copier-answers.yml.jinja` = `{{ _copier_answers|to_nice_yaml -}}`
- the scaffold invariant excludes both `.copier-answers.yml` (rendered) and
  `.copier-answers.yml.jinja` (archive) from the byte comparison
- `update.yml` needs no flags: rendered answers advance `_commit` themselves
- template improvements reach derived repos when the template cuts a release
  (copier resolves the newest non-prerelease tag) — releases are the channel

## Consequences

- **Good**: derived repos get `copier update` with three-way merge; the estate
  gains a machine-checkable "template == scaffold" invariant it does not
  currently have.
- **Cost**: two sources of truth for one file set (repo file vs Jinja
  template) during migration — the byte-identical diff test is the control.
- **Cost**: `{{ }}` delimiters collide with workflow expression syntax
  (`${{ }}`); the migration must set Copier's `skip_if_exists`/renderer
  options per file type.
- **Not chosen**: `degit`-style re-scaffold (loses local history and edits).

## Amendment (loop 23): derived-repo runbook

Proven end-to-end on a second template (OmniPython, `omni-python-e2e`): the
channel requires two one-time settings in each derived repo:

1. **Allow GitHub Actions to create pull requests** — default OFF for
   personal-account repos; set via `PUT /repos/{repo}/actions/permissions/workflow`
   with `can_approve_pull_request_reviews: true`. Non-workflow drift (the
   common case) needs nothing else.
2. **UPDATE_TOKEN** (PAT, `workflow` scope) — only for replays that touch
   `.github/workflows/*`; see loop 22.
3. **GitHub Pages enabled** (`build_type: workflow`) — templates that deploy
   docs inherit the docs gate, and `deploy-pages` 404s on repos where Pages
   was never enabled. Set via `POST /repos/{repo}/pages`. Verified: both e2e
   repos went fully green after enabling (loop 23).
4. **Close Dependabot's `github-actions` PRs** — action pins are
   template-managed; merging divergent pins breeds conflicts with every
   future replay. Ecosystem deps (cargo/uv) stay Dependabot-managed
   per-repo. The template's `dependabot.yml` carries this note (loop 24).
