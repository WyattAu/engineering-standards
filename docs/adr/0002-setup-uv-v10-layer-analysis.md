# ADR-0002: adopt setup-uv v10.3.0: read the layer before you fear the number

- **Status**: Accepted (loop 29)
- **Date**: 2026-10-13
- **Supersedes**: the loop-28 deferral of the `astral-sh/setup-uv` 7.6.0 → 10.3.0 bump

## Context

Loop 28 received a Dependabot wave and closed this PR as "three majors of the
tool that owns `sync`/`lock`/`build`: that is an ADR plus a measurement, not
a bot merge". The deferral was correct procedure, and the conclusion behind it
was wrong.

## The measurement

`setup-uv` has two independent layers, and the version numbers belong to
different ones:

| Layer | Version in play | Source of truth |
|---|---|---|
| the **action** (`astral-sh/setup-uv`) | 7.6.0 → 10.3.0 | the action's own releases |
| the **uv tool** it installs | 0.13.0 in both cases | `version:` input, default `latest` |

Facts measured in loop 29:

1. Both action versions declare `version: {default: ""}`: "Defaults to the
   version in pyproject.toml or 'latest'".
2. `astral-sh/uv`'s latest release is **0.13.0** (2026-10-09): the exact
   version this repo's `uv.lock` (`revision = 5`) is already validated
   against in green CI, and the exact version on the maintainer's machine.
3. Every input this estate passes (`python-version`, `enable-cache`) still
   exists in v10.3.0.
4. v10.3.0 runs on **node24**; the v7 line ran on the deprecated node20: the
   same deprecation class loop 28 just eliminated for `setup-python`.

So the bump changes the wrapper's runtime and its code, not the resolver.
Lockfile handling, resolver behaviour, and reproducibility are untouched.

## Decision

**Adopt `astral-sh/setup-uv` v10.3.0** estate-wide (OmniPython, the shared
`python-kit.yml`, and the derived e2e repos), pinned by SHA with the exact tag
as its comment.

The general lesson is the ADR's real content, and it is recorded in
`PITFALLS.md` as *"read the layer before you fear the number"*: a deferral
whose justification was a version number is not yet a measurement. Before
deferring a dependency bump, establish which layer the number describes and
what the *other* layer's current version is.

## Consequences

- Node 20 deprecation warnings stop for the Python kit.
- The resolver is unchanged, so the existing lock and its byte-for-byte
  reproducibility gate stay valid: verified by CI, not assumed.
- Dependabot's setup-uv PRs close themselves as superseded; the estate keeps
  one SHA per action (`check-pin-consistency`).
