# REPO-HYGIENE: repository housekeeping files

> **Status: ACCEPTED (v0.1.0, 2026-11-09).** Ratification: ADR-0019.
> Implements [OMNI-CORE.md](./OMNI-CORE.md) invariant 8 ("GitHub
> housekeeping: ... CODEOWNERS, issue templates, PR template, SECURITY.md,
> ... hygiene is not per-repo taste").

A repository that invites contribution or publishes artifacts must make
ownership, vulnerability reporting, and change intake discoverable in
standard locations. This standard defines the minimum machine-checkable
shape; it does not prescribe policy content beyond a working reporting
path.

Machine check: `scripts/check-hygiene.py`. Rule IDs: `RH-*`.

## RH-1. A vulnerability reporting path exists

The repository MUST contain a `SECURITY.md` in a standard location
(repository root, `.github/SECURITY.md`, or `docs/SECURITY.md`).

The file MUST be non-empty and MUST include a reporting path: at least
one of a mailto/contact address, a URL, or explicit coordinated-
disclosure/reporting instructions. It MUST NOT direct reporters to open
a public issue as the only or primary path.

Reference template: [`templates/SECURITY.md`](./templates/SECURITY.md).

## RH-2. Code ownership is declared

The repository MUST contain a `CODEOWNERS` file in a standard location
(repository root, `.github/CODEOWNERS`, or `docs/CODEOWNERS`).

The file MUST contain at least one non-empty, non-comment ownership
rule (an owner assignment such as `* @owner` or a path rule). A file
that is only comments or blank lines does not satisfy this requirement.

Reference template: [`templates/CODEOWNERS`](./templates/CODEOWNERS).

## RH-3. Issue intake has a template

The repository MUST provide at least one issue template: a file under
`.github/ISSUE_TEMPLATE/` (any non-hidden file, or a `config.yml`), or
a single `.github/ISSUE_TEMPLATE.md` / `.github/ISSUE_TEMPLATE.yml`.

A template directory that contains only `config.yml` counts when the
config is non-empty (it may route intake to external links).

Reference templates:
[`templates/ISSUE_TEMPLATE/bug_report.md`](./templates/ISSUE_TEMPLATE/bug_report.md),
[`templates/ISSUE_TEMPLATE/feature_request.md`](./templates/ISSUE_TEMPLATE/feature_request.md).

## RH-4. Pull request intake has a template

The repository MUST contain a pull request template in a standard
location: `.github/PULL_REQUEST_TEMPLATE.md`,
`.github/pull_request_template.md`,
`docs/PULL_REQUEST_TEMPLATE.md`,
`docs/pull_request_template.md`, or a non-empty
`.github/PULL_REQUEST_TEMPLATE/` directory.

The template file MUST be non-empty.

Reference template:
[`templates/PULL_REQUEST_TEMPLATE.md`](./templates/PULL_REQUEST_TEMPLATE.md).

## Scope and limits

`check-hygiene.py` validates presence and minimal shape in one target
repository path. It does not judge whether named owners are current,
whether the security contact is monitored, or whether template prompts
are high quality. Those are review concerns. Estate-wide adoption
percentages are measured separately (the STANDARDS-INDEX adoption
column) and are not computed by the per-repo check.
