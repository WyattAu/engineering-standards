# COMMITS: the commit contract

> **Status: PROPOSED (v0.1.0, 2026-11-09).** Ratification: ADR-0014.
> Gate: `scripts/check-commits.py`. Model: `STANDARDS-MODEL.md`.

**Applies to:** every commit on a shared branch in every repository.
**Oracle:** `scripts/check-commits.py --range <A..B>` (git is the store).

## Why a commit standard

Commit messages are the only record that survives a rebase, a squash, and a
migration between forges. The estate already writes them by convention:
`feat(standards):`, `fix(cli):`, `chore(deps):` appear throughout history.
Convention without a gate decays quietly, and the cost lands on the person
reading `git log` at 2am, who cannot tell a behaviour change from a
formatting pass.

The rules below are the subset of Conventional Commits 1.0.0 that this
estate actually uses, plus the two properties that make history machine
readable: a stable type vocabulary and a bounded subject.

## CS-1 Header grammar

**MUST.** `<type>[(<scope>)][!]: <subject>`

- Evidence: `GATE` (`check-commits.py`, code `header`)
- Why: the type and scope are what release tooling parses to decide whether
  a change is a patch, a feature, or a break. Prose first lines ("update
  stuff") are unparseable and belong in the body.

## CS-2 Type vocabulary is closed

**MUST.** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`. A new type requires an ADR.

- Evidence: `GATE` (`type`)
- Why: a closed set is what makes `git log --grep '^fix'` meaningful and
  lets release-plz decide a version bump without a human guess. An open
  vocabulary degrades into adjectives.

## CS-3 Subject is at most 50 characters, no trailing period, imperative

**MUST.** <= 50 characters, no terminal punctuation, mood as a command
("add", not "added" or "adds").

- Evidence: `GATE` (`subject-length`, `subject-period`), `REVIEW` (mood)
- Why: 50 is the length that survives `git log --oneline` in an 80-column
  terminal with the hash and date, which is how the message is actually
  read. Imperative mood matches the sentence "this commit will ...".

## CS-4 Header and body are separated by exactly one blank line

**MUST.** An empty line follows the header when a body exists.

- Evidence: `GATE` (`blank-line`)
- Why: `git log`, `format-patch`, and every mail-based tool treat the first
  blank line as the header/body boundary. Without it the body becomes part
  of the subject and the subject is truncated everywhere.

## CS-5 Body wraps at 72 columns

**SHOULD.** Body lines <= 72 characters, except a line with no spaces
(a URL, a hash, a path) which may run long.

- Evidence: `GATE` (`body-width`)
- Why: 72 leaves room for the 4-space indent `git log` adds, so wrapped
  text stays inside 80 columns instead of hard-wrapping mid-word.

## CS-6 Breaking changes are declared

**MUST.** A breaking change is marked with `!` after the type or scope, or
with a `BREAKING CHANGE: <description>` footer (uppercase, colon, space).

- Evidence: `GATE` (`breaking-format`)
- Why: this is the one token that changes a version number automatically
  (OMNI-CORE 11). Lowercase `breaking change:` is silently ignored by every
  parser, which turns a major release into a patch release.

## CS-7 Trailers are last, each on its own line

**MUST.** `Refs:`, `Co-Authored-By:`, `Signed-off-by:`, `Reviewed-by:` and
similar trailers appear after the body, one per line, `Token: value`.

- Evidence: `GATE` (`trailer-position` when a body follows a trailer)
- Why: `git interpret-trailers` and `git commit --trailer` only parse the
  final paragraph. A trailer in the middle of prose is invisible to tooling
  and to anyone scanning for authorship.

## CS-8 Signature status is reported, never assumed

**SHOULD.** Commits are signed (SSH or GPG). `check-commits.py` reports the
signature state of every commit it checks; `--require-signature` makes an
unsigned or unverifiable commit a failure.

- Evidence: `MEASURE` (signature counts per run), `GATE` when the flag is on
- Why: provenance for what is shipped is already an attestation
  (OMNI-CORE 11c). A signed commit is a weaker but continuous signal that
  the author is who the email says. Reporting first is deliberate: turning
  it on estate-wide before keys exist would block every contributor.

## CS-9 One logical change per commit

**SHOULD.** A commit does one thing; a rename and a behaviour change are
two commits.

- Evidence: `REVIEW`
- Why: a mixed commit cannot be reverted, bisected, or reviewed
  independently. The 2026-11-09 sweep found commits where a dependency
  bump and a feature gate landed together, so a red CI could not be
  attributed without reading the diff.

## Measured baseline (2026-11-09)

Run against the six most recent commits of this repository:

| Check | Result |
|---|---|
| Commits checked | 6 |
| Findings | 15 |
| Subject over 50 characters | 3 |
| Body line over 72 characters | 10 |
| Type outside the closed set | 2 (`fresco`, an agent identity, not a change type) |
| Signed commits | 0 good, 6 unsigned, 0 bad |

The rules were not lowered to fit the history. The gate is advisory on
history and applies to new ranges, and this table is the evidence that the
standard is currently aspirational rather than satisfied. A `fresco` commit
should be `chore(fresco): ...`; rewriting published history to prove a
point would cost more than it teaches.

## Running the gate

```sh
python3 scripts/check-commits.py --range origin/main..HEAD
python3 scripts/check-commits.py --range HEAD~5..HEAD --require-signature
git log --oneline -20   # the surface this standard protects
```
