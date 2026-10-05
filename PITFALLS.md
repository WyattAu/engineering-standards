# PITFALLS.md — recurring failure modes and their fixes

Every entry here was hit for real across the estate. Each one cost a red
build; the fix is the pattern to reuse. Add new entries at the top of the
"Toolchain and ecosystem" section.

## Dependency automation

| Symptom | Cause | Fix |
|---|---|---|
| `Dependabot Updates` fails with `Unsupported bun.lock 'lockfileVersion' 2` | Dependabot's bun updater only understands lockfile v1 | Known upstream gap. Action bumps (the `github-actions` ecosystem) still work, so security updates flow; **package** updates must be applied by hand until Dependabot (or a Renovate `bun` manager) supports v2. Verify each major locally before landing it — that is the only review path left for package deps. |
|---|---|---|
| A toolchain job starts testing the wrong language version (e.g. `msrv` suddenly builds with a version that does not exist) | Dependabot reads `some/action@1.85.0` as an *action version* and bumps it to `@1.120.0` | Keep the version in an **input**, not the ref: `dtolnay/rust-toolchain@master` + `with: {toolchain: "1.85.0"}`. Dependabot has nothing to bump. |
| `--frozen-lockfile` fails with "lockfile had changes, but lockfile is frozen" | A dependency was added to `package.json` without refreshing the lock | Always run the installer in the same commit as the manifest change; CI's frozen install is the gate that proves it. |
| A major bump lands and a gate explodes (e.g. knip crashing with `Cannot read properties of undefined`) | The new major of a *dev tool* is incompatible with the pinned *language* toolchain | Reproduce locally before merging a major; when the language toolchain itself is the blocker, pin the toolchain and add a documented dependabot `ignore` until upstream support lands (see TypeScript below). |

## Language toolchains

- **TypeScript 7 (native port) ships no programmatic compiler API.** Both
  `astro check` and knip's module resolution crash on it. Pin `typescript` to
  the newest `6.x` and add to `dependabot.yml`:
  ```yaml
  ignore:
    - dependency-name: typescript
      versions: [">=7.0.0"]
  ```
  with a comment linking the upstream tracking issue
  (https://github.com/withastro/roadmap/discussions/1321). Unpin the moment
  Astro exposes support.
- **`ghcup`/`elan` bootstrap beats action features** for language managers: the
  official installers are scriptable and never 401.
- **GHCR devcontainer features are not anonymous-safe.** Both
  `devcontainers-extra/features/nix:1` and `oven-sh/bun:1` returned 401/403 in
  practice. Install in `postCreateCommand` with the official script instead;
  CI then actually exercises the install.

## Docs publishing

- `mkdocs gh-deploy` pushes a `gh-pages` **branch**. When Pages is enabled with
  `build_type=workflow`, that push fails (`git push` exit 128) — the two
  mechanisms conflict. Use the artifact flow like every other docs job:
  `mkdocs build --strict --site-dir site` → `actions/upload-pages-artifact` →
  `actions/deploy-pages`.

## Advisory jobs (the graduation pattern)

- Job-level `continue-on-error: true` keeps the **workflow run** conclusion
  green while the job still shows red. Read the run conclusion, not the job
  matrix, when auditing the estate.
- `zizmor` exits **14** when it finds anything; with `continue-on-error` the
  run stays green and the job is the signal. Findings are the report — don't
  `|| true` them away.
- New advisory jobs stay advisory for exactly one loop, then graduate to a
  blocking gate (see `LOOP.md`).

## Shell/sweep scripting

- Never pass markdown containing backticks as a **double-quoted** shell
  argument: the backticks execute as command substitution and silently
  restructure your arguments. Use single quotes.
- A function called with an argument it doesn't reference still expands it if
  the heredoc names `$1`; verify generated YAML with a parser before pushing.
