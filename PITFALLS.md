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


## Pipelines and scaffolding (loop 10)

| Symptom | Cause | Fix |
|---|---|---|
| `tar: Exiting with failure status` inside a CI step that "clearly pipes the archive in" | `git archive \| mkdir X && tar -x` binds as `(archive \| mkdir) && tar` — tar reads an empty stdin | Put the extraction target on its own line: `mkdir -p X` then `git archive HEAD \| tar -x -C X -f -` |
| The scaffold diff flags directories that "aren't in the repo" | The *working tree* carries untracked debris (`dist/`, `node_modules/`, `.venv/`); `copier copy` of a fresh clone does not | Compare against `git archive HEAD` (tracked content), not the working tree |



| Symptom | Cause | Fix |
|---|---|---|
| `reuse lint` passes on 9 repos and one extra file appears (`criterion.json`) | Benchmark reports land in the tree; REUSE covers `**` so it is fine, but scratch artifacts still belong in `.gitignore` | Keep the emitter output ignored; the REUSE manifest covers whatever is tracked |
| A pin script writes an unresolved placeholder into a workflow | The API hiccuped and the error body was treated as a SHA | **Never write a value that has not passed a full-SHA assertion** — assert `[0-9a-f]{40}` before substituting, and grep the tree for the failure marker afterwards |
| An e2e job is ~50% red with identical code | The browser install is a single unguarded CDN download | Move the install into the canonical e2e script with retry + fallback; CI runs the same script developers do |



| Symptom | Cause | Fix |
|---|---|---|
| The image-flavor container build 404s inside the `common-utils` feature (`E: Failed to fetch ... sudo_...deb`) | The feature apt-installs packages without refreshing the mirror index first, so a stale mirror fails the build | Drop the feature on `mcr.microsoft.com/devcontainers/base:*` images — the base image already contains common-utils. Less network, less flake, same capability |
| A workflow parse error CI-side while PyYAML validated the file locally | PyYAML silently allows duplicate mapping keys (last wins); GitHub Actions does not | Validate workflow YAML with a duplicate-key-rejecting loader — `yaml.safe_load` is not enough |
| Scratch clones vanish between sessions | `/tmp` is disposable; only pushed state survives | Re-clone from origin and continue — the repos are canonical. Never let unpushed work accumulate past one verified commit |

## Haskell / criterion (loop 4)

| Symptom | Cause | Fix |
|---|---|---|
| A benchmark reports ~4ns for a batch of 1,000 operations | The batch was a top-level CAF that was only *returned*, so every iteration after the first timed nothing | `nf f x` — criterion applies the argument per iteration. `nfIO`/`whnfIO` take a plain `IO` action and will happily measure a hoisted constant |
| `cabal test all` fails with `Cabal-7043` after adding a bench component | The new `criterion` dependency backtracks the solver's whole plan | `cabal build/test all --disable-benchmarks`; there is no `benchmarks:` field in `cabal.project` (that parse error is real) |
| A `.hi`/report JSON parse fails after a criterion upgrade | 1.6.x writes `["criterion", "<version>", [{reportAnalysis: {anMean: {estPoint}}, ...}]]`, not the older flat `mean` | Walk the report for mean-bearing nodes and understand both shapes (see `emit-criterion-bench.py`); keep the emitter as its own script so it is testable without GHC |
| A CI lint job fails on a file that "looks fine" | Each repo's own formatter config differs — OmniDotfiles runs `shfmt -i 4` over `scripts/` while the estate uses `-i 2` | Format with the *target repo's* setting, and check with it before pushing |



| Symptom | Cause | Fix |
|---|---|---|
| A gate ships in a permissive mode ("report, never fail") because the toolchain "can't" be deterministic | The reason was plausible, not measured - and wrong in all three cases (GHC `.hi`, firmware ELF, `tofu plan` all hashed identically) | Measure first, then choose the mode. If a permissive mode is ever needed, the evidence belongs in the ADR next to the claim |



| Symptom | Cause | Fix |
|---|---|---|
| A determinism script exists, is named in an ADR, and nothing runs it | It was written but never wired | A claim needs a verb *and* a job: `make repro` + the `repro` CI job. Wire it or delete it |
| `uv build` fails with `setuptools ... get_requires_for_build_sdist` in a uv workspace | A bare `uv build` tries to build the `package = false` root | `uv build --all-packages` (and exclude uv's own `.gitignore` from the out-dir) |
| A reproducibility check fails only on the *second* run, with a phantom "first run only" line | chezmoi's `run_once_` scripts print to **stdout**, which you captured | Redirect the tool's chatter (`>&2`) and point `HOME` at the scratch dir so the render is hermetic |
| `site-bytes` differs by hundreds of KB between machines | Pagefind (Starlight search) is generated via `npx`; without node on PATH the site is silently smaller | Measure where CI measures; say so in the baseline file header |



| Symptom | Cause | Fix |
|---|---|---|
| `cargo bench --workspace --benches -- <args>` fails with `Unrecognized option` | Cargo hands `--` args to **lib test harnesses** too, and libtest rejects criterion flags | Resolve bench targets from `cargo metadata --no-deps` and run `cargo bench -p <pkg> --bench <name> --` per target |
| `bench is not a function` in a vitest 5 `.bench.ts` | vitest 5 dropped the top-level `bench` DSL (no `bench` export at all) | Don't fight it: gate the metrics users feel (shipped bytes + build time) and keep the TSV contract for a later CodSpeed/mitata swap |
| A committed byte baseline is "regressed" by +251% on one machine only | Starlight generates its Pagefind search index through **npx**; a machine without node on PATH silently ships a smaller site | Record baselines from **CI** (the supported toolchain) and say so in the file header; the metric must measure the environment users actually get |
| A naive `+10% fails` perf gate flips red on identical code | Two identical consecutive Astro builds differed by **18% and 88%** wall-clock; CodSpeed measures a 7% gate at ~1% false positives on shared runners | Gate on **statistics + exactness**: z-test noise bands for microbenchmarks, exact byte budgets for sizes, `mode=info` (reported, never failing) for bare wall-clock |
| A 1-microsecond benchmark has ~120% relative variance | Single-call timing is dominated by timer and loop overhead | Batch the work inside the benchmark (1,000 iterations) so the mean is well above the noise |
| `shfmt -d` fails in CI after adding a script | The estate uses `-i 2`, but **OmniDotfiles lints `scripts/` with `-i 4`** | Format with the *target repo's* setting: `shfmt -w -i 2` everywhere except Dotfiles (`-i 4`) |
| `go test -bench=.` produces no output | The template ships no `Benchmark*` functions, and `-run=^$` skips tests | Ship a `*_bench_test.go` with batched benchmarks (`b.Loop()`, `b.ReportAllocs()`) as the gate's input |
| A CI matrix leg fails at `cabal update` with `403 ... hackage-mirror` | The Hackage mirror 403s intermittently; nothing to do with the code | Retry `cabal update` three times with a 15s backoff before failing the leg |


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


### Evaluating a tool is not the same as configuring it

Loop 8 rejected `ty` for "14 false positives" that were entirely missing `[tool.ty.environment]` config — the same version passes cleanly once configured. Before recording a tool as unfit, check its configuration surface: a rejection measured against a default config measures the defaults, not the tool. Any "X does not support Y" claim in an ADR must be re-checked with Y configured.

## Shell/sweep scripting

- Never pass markdown containing backticks as a **double-quoted** shell
  argument: the backticks execute as command substitution and silently
  restructure your arguments. Use single quotes.
- A function called with an argument it doesn't reference still expands it if
  the heredoc names `$1`; verify generated YAML with a parser before pushing.
