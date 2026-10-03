# Estate layer model — L0–L3

Every crate published under the WyattAu crates.io owner belongs to exactly one
layer. Layers constrain **estate-internal dependencies only** — external
dependencies (tokio, axum, reqwest, serde, …) are unconstrained and curated
separately via `cargo-deny` (`bans`, `advisories`, `licenses`).

**Estate-internal** means: published under the WyattAu crates.io owner. The
authoritative list is [`scripts/estate-crates.txt`](../scripts/estate-crates.txt);
the authoritative per-crate layers are [`scripts/estate-tiers.json`](../scripts/estate-tiers.json)
(both regenerated from the crates.io ownership API — see below).

## The layers

### L0 — leaf
Zero runtime estate-internal dependencies. Minimal, curated external
dependencies; `no_std`-capable where the domain allows. The only estate
dependency an L0 crate may have is its own **proc-macro companion** (host
codegen, no runtime edge — e.g. `typed-id-new` → `typed-id-derive`).

Examples: `decimal-money`, `typed-id-new`, `chronoshift`, `simd-tokenizer`,
`salting`, `error-codes`, `geo-kit`, `json-envelope`.

### L1 — substrate
Runtime/platform infrastructure and core primitives; depends on L0 (plus
essential external infra like tokio). Linux/platform-scoped crates are allowed
here with declared `#[cfg(target_os)]` targets.

Examples: `metrics-kit`, `cas-kit`, `shm-rings`, `uds-kit`, `tokenkit`,
`shutdown-kit`, `wire-kit`, `clock-kit`, `hw-kit` (future: `uring-kit`).

### L2 — domain
Domain logic with estate semantics; depends on L0/L1 and other L2 kits
(same-layer composition is normal and legal — e.g. `outbox-kit` → `breaker`).

Examples: `breaker`, `throttle-kit`, `webhookkit`, `outbox-kit`,
`idempotency-kit`, `healthkit`, `config-kit`, `flag-kit`
(reserved for future: `ledger-kit`, `policy-kit`).

### L3 — composition
Composes L0–L2 plus the external world: HTTP clients, frameworks, servers,
UI frameworks, application front-ends.

Examples: `fetch-kit`, `telemetry-init`, `worker-kit`, `scim-kit`,
`oauth-toolkit`, `axum-stack`, `vane-proxy`.

## Rules

1. **No upward dependencies.** A crate may only depend on estate crates at its
   own layer or below. A crate's effective layer is the *ceiling* of its
   estate dependencies:
   `layer(crate) >= max(layer(d) for d in estate deps)`.
   Dependencies must never point up the stack. Same-layer estate dependencies
   are permitted (kits compose); a crate whose estate deps max out at L2 may
   declare L2 or L3 — never L1.
2. **L0 is strict.** An L0 crate has zero *runtime* estate dependencies. Its
   only permitted estate dependency is a proc-macro companion crate.
3. **Dev-dependencies are exempt** (test-only edges do not create runtime
   coupling). Normal and build dependencies count, including
   platform/target-scoped ones.
4. **Path dependencies count.** An estate crate reached via `path = ...`
   (e.g. inside a monorepo workspace) is matched by package name exactly like
   a registry dependency.
5. **Exceptions: none.** There is no waiver, allowlist, or suppression
   mechanism. If a dependency direction is wrong, restructure: split the
   crate, move the shared code down a layer, or invert the dependency with a
   trait.

## Declaring a crate's layer

Each crate's `Cargo.toml` carries its layer in package metadata:

```toml
[package.metadata.layers]
tier = "L2"
```

`cargo package` preserves `[package.metadata]`, so the declaration ships with
the published `.crate`. The declaration lives in the manifest — not in a
central file — so the crate's repo CI gates the crate's own layer claim.

A missing declaration is a **warning** during the rollout (undeclared crates
are not enforced against). Once the estate is fully declared, undeclared
estate crates with estate dependencies should be treated as review blockers.

## Enforcement

The shared CI workflow [`.github/workflows/rust-kit.yml`](../.github/workflows/rust-kit.yml)
runs a `layer` job on every kit repo. The job checks out this repo (public) and
runs [`scripts/check-layers.py`](../scripts/check-layers.py), which:

1. Reads each workspace member's declared tier from its `Cargo.toml`.
2. Runs `cargo metadata --format-version 1` and resolves every workspace
   member's **transitive** dependency set (normal + build edges; path and
   registry deps treated identically by package name).
3. Looks up each estate dependency's layer in `scripts/estate-tiers.json`
   (falling back to the dep's manifest for crates not yet in the table).
4. **Fails** when a crate declared L0/L1/L2 depends on an estate crate at a
   higher layer, or when an L0 crate has a runtime estate dependency.
5. **Logs only** for L3 crates, undeclared crates, and deps of undeclared
   crates (rollout mode).

The checker is pure stdlib (`json` + `subprocess` to `cargo metadata`) — no
third-party Python deps, nothing to install in kit repos.

Regenerate the estate list and tier table after publishing or reclassifying:

```sh
curl -s 'https://crates.io/api/v1/crates?user_id=404181&per_page=100&page=1' \
  | jq -r '.crates[].name' >> scripts/estate-crates.txt   # + page 2
```

`scripts/estate-tiers.json` is updated in this repo together with the table
below.

## Classification (147 crates, 2026-10-03)

Derived from the actual estate dependency graph (crates.io `dependencies`
endpoint, fixpoint over the graph) and the kit registry in `site/src/lib/kits.ts`;
task-normative anchors from this document's layer examples override registry
drift. Justifications are one line per crate.

| Crate | Layer | Justification |
|---|---|---|
| `chronoshift` | L0 | Time abstraction leaf, critical-section only (task §3 anchor) |
| `crawlkit-plugin-sdk` | L0 | Plugin contract types, serde only; no runtime |
| `crdts-kit` | L0 | Pure CRDT types, serde+wasm (kits.ts L0) |
| `cryptkit` | L0 | AEAD/hash primitives (kits.ts L0) |
| `decimal-money` | L0 | Decimal money type leaf, rust_decimal only (task §1 anchor) |
| `delta-kit` | L0 | Binary delta codec leaf, no estate deps |
| `error-classify-derive` | L0 | Proc-macro companion (host codegen leaf) |
| `error-codes` | L0 | Stable numeric error-code registry leaf (task candidate errcode) |
| `geo-kit` | L0 | Geocoding utils, thiserror only (kits.ts L0) |
| `http-errors` | L1 | Re-export shim over error-codes L0; runtime estate dep forbids L0 (mirrors error-classify) |
| `hw-kit` | L1 | Linux-only hardware substrate (topology/pinning/NUMA/hugepages); zero estate deps, `libc`-only external edge |
| `i18n-kit` | L0 | Runtime i18n catalogs; thiserror-only leaf |
| `json-envelope` | L0 | API envelope types; http+serde only (task candidate verified) |
| `leptos-derive` | L0 | Proc-macro companion (host codegen leaf) |
| `leptos-macros` | L0 | Proc-macro for Leptos components (kits.ts L0) |
| `model-router` | L0 | LLM routing core, pricing tables; thiserror only (kits.ts L0) |
| `plycore` | L0 | Shared charting types leaf (kits.ts L0) |
| `polyfont-core` | L0 | Font IR core, serde only |
| `polyfont-fonts` | L0 | Font data catalog, toml/tracing only |
| `salting` | L0 | Deterministic salt derivation leaf (kits.ts L0) |
| `sieve-kit` | L0 | Pure rule engine, regex only; no estate deps |
| `simd-tokenizer` | L0 | SWAR tokenizer leaf, optional tiktoken (task §3 anchor) |
| `suture-common` | L0 | Shared leaf utils, blake3/serde |
| `suture-plugin-sdk` | L0 | Plugin SDK contract, serde only |
| `typed-id-derive` | L0 | Proc-macro companion (host codegen leaf) |
| `typed-id-new` | L0 | Typed ID newtypes; only estate dep is proc-macro companion (task §3 anchor) |
| `validkit` | L0 | Validation newtypes; only estate dep is proc-macro companion (kits.ts L0) |
| `validkit-derive` | L0 | Proc-macro companion (host codegen leaf) |
| `vane-observe` | L0 | Observability primitives, tracing/rand only |
| `cas-kit` | L1 | CAS blob-store substrate; zero estate deps verified (task §1 L1 anchor) |
| `clock-kit` | L1 | Precision time substrate over chronoshift L0 (optional bridge edge); libc only otherwise (spec clock-kit.md) |
| `error-classify` | L1 | Error taxonomy on error-codes L0; runtime estate dep forbids L0 (kits.ts L1) |
| `eventbus-kit` | L1 | In-process event bus substrate (kits.ts L1) |
| `loop-retry` | L1 | Retry/backoff substrate primitive (kits.ts L1) |
| `metrics-kit` | L1 | Lock-free metrics substrate; zero estate deps (task §1 L1 anchor) |
| `ply-viz` | L1 | Wasm viz helper on plycore L0, ply family at L1 |
| `plychart` | L1 | Zero-dep Canvas2D charting on plycore L0 (kits.ts L1) |
| `plycharts` | L1 | Wasm charts on plycore L0, ply family at L1 |
| `plycompute` | L1 | Quant analytics on plycore L0 (kits.ts L1) |
| `polyfont-config` | L1 | Font config layer over polyfont-core L0 |
| `polyfont-parse` | L1 | Font parser over polyfont-core L0 |
| `polyfont-render` | L1 | Font renderer over polyfont-core L0 |
| `polyfont-scope` | L1 | Font scoping over polyfont-core L0 |
| `polyfont-themes` | L1 | Theme layer over polyfont-config L1 |
| `shared-state` | L1 | Shared-state plumbing substrate (kits.ts L1) |
| `shm-rings` | L1 | Shared-memory ring substrate (task §1 L1 anchor) |
| `shutdown-kit` | L1 | Graceful shutdown coordination substrate (kits.ts L1) |
| `slab-pool` | L1 | Lock-free memory pool substrate, shm-rings sibling |
| `suture-core` | L1 | Suture core over suture-common L0 |
| `suture-driver` | L1 | Driver SPI over suture-core L1 |
| `suture-driver-csv` | L1 | CSV format driver over suture-driver L1 |
| `suture-driver-docx` | L1 | DOCX driver over suture-driver+ooxml L1 |
| `suture-driver-example` | L1 | Example driver over suture-driver L1 |
| `suture-driver-feed` | L1 | Feed driver over suture-driver L1 |
| `suture-driver-html` | L1 | HTML driver over suture-driver L1 |
| `suture-driver-ical` | L1 | iCal driver over suture-driver L1 |
| `suture-driver-image` | L1 | Image driver over suture-driver L1 |
| `suture-driver-json` | L1 | JSON driver over suture-driver L1 |
| `suture-driver-markdown` | L1 | Markdown driver over suture-driver L1 |
| `suture-driver-otio` | L1 | OTIO driver over suture-driver L1 |
| `suture-driver-pdf` | L1 | PDF driver over suture-driver L1 |
| `suture-driver-pptx` | L1 | PPTX driver over suture-driver+ooxml L1 |
| `suture-driver-sql` | L1 | SQL driver over suture-driver L1 |
| `suture-driver-svg` | L1 | SVG driver over suture-driver L1 |
| `suture-driver-toml` | L1 | TOML driver over suture-driver L1 |
| `suture-driver-xlsx` | L1 | XLSX driver over suture-driver+ooxml L1 |
| `suture-driver-xml` | L1 | XML driver over suture-driver L1 |
| `suture-driver-yaml` | L1 | YAML driver over suture-driver L1 |
| `suture-git-bridge` | L1 | Git bridge lib over common/core L0-L1 |
| `suture-merge` | L1 | Merge ops over suture-driver L1 |
| `suture-ooxml` | L1 | OOXML codec over suture-driver L1 |
| `suture-protocol` | L1 | Wire protocol over suture-common L0 |
| `suture-raft` | L1 | Raft consensus substrate (tokio) |
| `suture-wasm-plugin` | L1 | wasmtime plugin-host support substrate |
| `tokenkit` | L1 | Token mint/verify substrate primitive (kits.ts L1) |
| `uds-kit` | L1 | Tokio UDS transport substrate |
| `vane-client-sdk` | L1 | Client SDK over vane-shm L1 |
| `vane-kernel` | L1 | Proxy kernel substrate on slab-pool L1 |
| `vane-plugins` | L1 | Plugin host over vane-observe L0 |
| `vane-proto` | L1 | Wire protocol types over vane-observe L0 |
| `vane-router` | L1 | Router core over vane-observe L0 |
| `vane-shm` | L1 | Shm segments over shm-rings L1 |
| `vane-tls` | L1 | TLS termination over shm-rings L1 |
| `webauthn-kit` | L1 | CTAP2/COSE verification substrate (kits.ts L1) |
| `wire-kit` | L1 | Zero-copy SBE/FIX wire codec substrate; zero estate deps (spec §Cross-references: estate's edge-format leaf) |
| `actor-kit` | L2 | Actor runtime/supervision domain semantics (kits.ts L2) |
| `api-paginate` | L2 | Cursor/offset pagination primitives (kits.ts L2) |
| `api-types` | L2 | Shared API request/response DTOs (kits.ts L2) |
| `axum-stack` | L2 | Axum middleware stack on healthkit+shutdown-kit (kits.ts L2) |
| `billing-kit` | L2 | Pricing primitives over decimal-money L0 (kits.ts L2) |
| `blobkit` | L2 | Object-storage trait w/ S3/local backends (kits.ts L2) |
| `breaker` | L2 | Circuit-breaker estate semantics; task §1 L2 anchor |
| `cache-pal` | L2 | Caching abstractions (kits.ts L2) |
| `chaos-kit` | L2 | Deterministic fault injection domain kit (kits.ts L2) |
| `config-kit` | L2 | Layered typed configuration, service-config domain (kits.ts L2) |
| `docs-pipeline` | L2 | Markdown->HTML rendering pipeline (kits.ts L2) |
| `envstack` | L2 | Layered env/config loading (kits.ts L2) |
| `flag-kit` | L2 | Feature flags domain kit over validkit L0 (kits.ts L2) |
| `healthkit` | L2 | Health/readiness domain kit; task §1 L2 anchor |
| `idempotency-kit` | L2 | Idempotency keys domain kit; task §1 L2 anchor |
| `mail-sync-kit` | L2 | IMAP/JMAP/SMTP sync engines, mailkit sibling (L2) |
| `mailkit` | L2 | Transactional email + threading (kits.ts L2) |
| `media-kit` | L2 | Image pipeline domain kit (kits.ts L2) |
| `multi-chain-wallet` | L2 | HD wallet domain primitives (kits.ts L2) |
| `otel-stack` | L2 | Wraps otelkit L2; no direct exporter deps |
| `otelkit` | L2 | OpenTelemetry setup helpers (kits.ts L2) |
| `outbox-kit` | L2 | Transactional outbox domain kit; breaker L2 dep same-layer legal (task §1 anchor) |
| `percentile-kit` | L2 | Latency budget gates domain kit (kits.ts L2) |
| `pid-manager` | L2 | PID-file service management (kits.ts L2) |
| `poolkit` | L2 | Connection/resource pooling service infra (kits.ts L2) |
| `suture-s3` | L2 | S3 client backend, blobkit-consistent service infra |
| `tamper-audit` | L2 | Tamper-evident audit log (kits.ts L2) |
| `tantivy-helper` | L2 | Tantivy search index helpers (kits.ts L2) |
| `throttle-kit` | L2 | Rate limiting domain kit; task §1 L2 anchor |
| `vane-control` | L2 | Proxy control plane; max estate dep envstack L2 |
| `vane-filters` | L2 | Filter engine over breaker/throttle-kit L2 |
| `webhookkit` | L2 | Signed webhook domain kit; idempotency-kit L2 dep same-layer legal (task §1 anchor) |
| `ws-kit` | L2 | WebSocket server/session management (kits.ts L2) |
| `accessctl` | L3 | Authz service composition on tokenkit (kits.ts L3) |
| `barbican` | L3 | Secrets-custody service toolkit (kits.ts L3) |
| `contact-miner` | L3 | Crawling app: tokio+rusqlite+web scraping (external world) |
| `crawlkit-engine` | L3 | Crawl engine: reqwest/scraper/wasmtime (external world) |
| `fetch-kit` | L3 | Resilient outbound HTTP client, reqwest stack (task §1 anchor) |
| `leptos-capital-markers` | L3 | Leptos UI component on leptos-leaflet-wyatt L3 |
| `leptos-crypto-ws` | L3 | Leptos component over ws-kit L2 + leptos framework |
| `leptos-leaflet-wyatt` | L3 | Leptos/Leaflet framework composition |
| `leptos-map-search` | L3 | Leptos UI component (framework world) |
| `leptos-sparkline` | L3 | Leptos UI component (framework world) |
| `leptos-stale-indicator` | L3 | Leptos UI component (framework world) |
| `oauth-toolkit` | L3 | OAuth2/OIDC flows over reqwest/JWKS (task §1 L3 anchor) |
| `polyfont-cli` | L3 | Polyfont CLI application (clap front-end) |
| `polyfont-lsp` | L3 | tower-lsp server composition |
| `resilient-fetch` | L3 | reqwest HTTP client stack; superseded by fetch-kit |
| `scim-kit` | L3 | SCIM 2.0 provisioning w/ optional axum router (task §1 L3 anchor) |
| `suture-cli` | L3 | Suture application CLI (clap+tui front-end) |
| `suture-connector-airtable` | L3 | Airtable API connector (reqwest, external world) |
| `suture-connector-notion` | L3 | Notion API connector (reqwest, external world) |
| `suture-daemon` | L3 | Suture application daemon (tokio+reqwest) |
| `suture-hub` | L3 | Hub server: axum+tonic+raft composition |
| `suture-lsp` | L3 | tower-lsp server composition |
| `suture-platform` | L3 | Platform app: axum+jsonwebtoken composition on hub L3 |
| `suture-tui` | L3 | ratatui front-end composition |
| `suture-vfs` | L3 | VFS over axum+fuse3 (external world) |
| `telemetry-init` | L3 | One-call observability bootstrap (task §1 L3 anchor) |
| `vane-proxy` | L3 | L4/L7 proxy composition: axum + full estate (max dep L2) |
| `worker-kit` | L3 | Job scheduling composition over breaker L2+shutdown-kit L1 (task §1 L3 anchor) |
| `ws-barbican` | L3 | WS transport to barbican; barbican L3 dep same-layer legal (kits.ts L3) |

## Notes and flagged ambiguities

- **Proc-macro companions at L0.** `typed-id-new` and `validkit` are L0 with a
  single estate dep each — their derive-macro companions. The checker exempts
  proc-macro targets at L0. `error-classify` builds on `error-codes` (a
  *runtime* lib dep) and is therefore L1, not L0.
- **kits.ts registry drift corrected.** The hand-transcribed registry in
  `site/src/lib/kits.ts` carries a few stale placements that conflict with the
  layer definitions; this table is authoritative: `decimal-money` is L0 (not
  L2), `breaker`/`throttle-kit` are L2 (not L1), `metrics-kit` is L1 (not L2),
  `telemetry-init`/`worker-kit` are L3 (not L2), `oauth-toolkit` is L3 (not
  L1). Update `kits.ts` alongside its next `KITS.md` sync.
- **suture family (pre-kit taxonomy).** The `suture-*` libraries sit at their
  graph-derived minimum (L0/L1); composition surfaces with servers, UIs, or
  external APIs (`suture-cli`, `suture-daemon`, `suture-hub`, `suture-platform`,
  `suture-tui`, `suture-lsp`, `suture-vfs`, `suture-connector-*`) are L3.
  If the family is ever re-kitted, re-derive from the graph.
- **Borderline calls.** `slab-pool` is L1 (lock-free memory substrate, sibling
  of `shm-rings`) though it would also satisfy L0's letter; `suture-s3` is L2
  (S3 client backend, consistent with `blobkit`) though its only estate dep is
  L0. Both are safe under the ceiling rule; lift only, never lower.
- **No cycles.** The estate dependency graph is acyclic (verified over all 186
  estate-internal edges). A cycle would make classification impossible — flag
  it immediately rather than forcing a layer.
- **Sweep reclassification.** `http-errors` started as an L0 candidate but its
  repo HEAD turned it into a thin re-export shim over `error-codes` — a
  runtime estate dep — so it is declared **L1** (the same shape as
  `error-classify`). Found by the checker itself on the first estate-wide run;
  the crate's repo carries the L0→L1 commit.
- **Published but absent from repo HEAD.** Four crates were published and
  classified from their crates.io dependency graph, but no longer exist under
  those names in their repo's default branch: `ply-viz` and `plycharts`
  (plychart), `leptos-derive` (leptos-macro), and `resilient-fetch`
  (superseded by `fetch-kit`; only `fetch-kit` remains). Their tiers are
  recorded in `scripts/estate-tiers.json` — registry consumers are still
  checked — but their repos cannot carry a manifest declaration. Two more
  were renamed in HEAD: `typed-id-new` → `typedids` (declared L0) and
  `suture-git-bridge` → `git-remote-suture` (declared L1); the tier follows
  the crate, and the rename should be reflected on crates.io at the next
  publish.
- **Crate/repo naming.** Several crates publish under names that differ from
  their repo (`money` → `decimal-money`, `clock` → `chronoshift`,
  `errcode` → `error-codes`, `ratelimit` → `throttle-kit`, `graceful` →
  `shutdown-kit`, `cachekit` → `cache-pal`, `auditlog` → `tamper-audit`,
  `paginate` → `api-paginate`, `hdwallet` → `multi-chain-wallet`,
  `eventbus` → `eventbus-kit`, `retry-backoff` → `loop-retry`,
  `http-error` → `http-errors`, `typed-id` → `typed-id-new`,
  `app-error` → `error-classify`, `fetchkit` → `resilient-fetch`,
  `tantivy-ext` → `tantivy-helper`, `leptos-leaflet` → `leptos-leaflet-wyatt`).
