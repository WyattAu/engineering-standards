/**
 * WyattAu kit registry — hand-transcribed from WyattAu/KITS.md
 * (WyattAu Kit Compatibility Matrix). Versions are read from each
 * repo's Cargo.toml and verified against vendored copies in
 * ecom-engine/crates/vendor/. Update alongside KITS.md.
 */

export type Layer = "L0" | "L1" | "L2" | "L3";

export interface Kit {
  /** crates.io package name */
  name: string;
  /** repo directory when it differs from the package name */
  repo?: string;
  version: string;
  layer: Layer;
  purpose: string;
  /** downstream kits/apps; empty when none are listed yet */
  consumers: string[];
  /** optional features of note, when any */
  features?: string;
}

export const KITS: Kit[] = [
  // ---- L0 — Leaf utilities ----
  {
    name: "salting",
    version: "1.0.0",
    layer: "L0",
    purpose: "Deterministic salt derivation for keyed hashing",
    consumers: ["suture", "Tachyon", "crawlkit", "CivitForge", "clawdius"],
  },
  {
    name: "error-codes",
    repo: "errcode",
    version: "1.0.0",
    layer: "L0",
    purpose: "Stable numeric/error-code registry",
    consumers: ["error-classify"],
  },
  {
    name: "cryptkit",
    version: "0.1.0",
    layer: "L0",
    purpose: "AEAD encryption, key handling, hashing helpers",
    consumers: ["ferro", "aether-core", "Tachyon", "CivitForge", "clawdius", "crawlkit"],
  },
  {
    name: "chronoshift",
    repo: "clock",
    version: "1.0.0",
    layer: "L0",
    purpose: "Time abstractions and clock injection",
    consumers: [],
  },
  {
    name: "typed-id-new",
    repo: "typed-id",
    version: "0.1.0",
    layer: "L0",
    purpose: "Strongly-typed identifiers",
    consumers: [],
    features: "`derive` (typed-id-derive)",
  },
  {
    name: "validkit",
    version: "1.0.0",
    layer: "L0",
    purpose: "Composable input validation primitives",
    consumers: ["ferro", "Tachyon", "CivitForge", "EvergreenShims"],
  },
  {
    name: "geo-kit",
    version: "1.0.0",
    layer: "L0",
    purpose: "Geocoding / geo utilities (UK postcode incl. GIR 0AA, etc.)",
    consumers: ["ecom-engine (vendored)"],
  },
  {
    name: "simd-tokenizer",
    version: "0.1.0",
    layer: "L0",
    purpose: "Token estimation — safe SWAR whitespace scan (5× scalar), optional tiktoken",
    consumers: [],
    features: "`tiktoken`",
  },
  {
    name: "delta-kit",
    version: "0.2.0",
    layer: "L0",
    purpose: "Rabin-rolling binary-safe delta codec (rsync-style, wire-compatible with suture)",
    consumers: [],
  },
  {
    name: "crdts-kit",
    version: "0.1.0",
    layer: "L0",
    purpose: "RGA replicated string — tombstones, causal convergence (proptest-verified), serde",
    consumers: [],
    features: "`serde`; `uuid` off for wasm",
  },
  {
    name: "model-router",
    version: "0.1.0",
    layer: "L0",
    purpose: "Cost-aware LLM routing — pricing tables, USD budget tracking, fallback chains (genai companion)",
    consumers: [],
    features: "`genai` adapter",
  },
  {
    name: "plycore",
    repo: "plychart",
    version: "0.2.0",
    layer: "L0",
    purpose: "Shared types for plychart and plycompute",
    consumers: ["plychart", "plycompute"],
  },
  {
    name: "typed-id-derive",
    repo: "typed-id",
    version: "0.1.0",
    layer: "L0",
    purpose: "Derive macro for `typed-id-new`",
    consumers: ["typed-id-new"],
  },
  {
    name: "leptos-macros",
    repo: "leptos-macro",
    version: "0.1.0",
    layer: "L0",
    purpose: "Procedural macros for Leptos components — boilerplate reduction for lib.rs, feature flags, prop defaults",
    consumers: [],
  },

  // ---- L1 — Core primitives ----
  {
    name: "error-classify",
    repo: "app-error",
    version: "0.2.0",
    layer: "L1",
    purpose: "Error trait classification; builds on `error-codes`",
    consumers: [],
  },
  {
    name: "tokenkit",
    version: "0.1.1",
    layer: "L1",
    purpose: "Token minting/verification",
    consumers: [
      "ferro",
      "aether-core",
      "accessctl",
      "barbican",
      "ws-barbican",
      "Tachyon",
      "CivitForge",
      "clawdius",
      "crawlkit",
      "suture",
    ],
  },
  {
    name: "oauth-toolkit",
    version: "0.2.0",
    layer: "L1",
    purpose: "OAuth flow helpers — PKCE, web social login, desktop loopback capture, mail-provider presets (Gmail/Outlook/Yahoo/AOL/Fastmail)",
    consumers: [],
  },
  {
    name: "loop-retry",
    repo: "retry-backoff",
    version: "0.1.0",
    layer: "L1",
    purpose: "Retry loops with backoff",
    consumers: ["crawlkit", "EvergreenShims", "ecom-engine (vendored)"],
  },
  {
    name: "shutdown-kit",
    repo: "graceful",
    version: "0.2.0",
    layer: "L1",
    purpose: "Graceful shutdown coordination",
    consumers: ["axum-stack"],
  },
  {
    name: "breaker",
    version: "1.0.0",
    layer: "L1",
    purpose: "Circuit breaker",
    consumers: ["ferro", "aether-core", "fetchkit"],
  },
  {
    name: "throttle-kit",
    repo: "ratelimit",
    version: "1.0.0",
    layer: "L1",
    purpose: "Rate limiting / throttling",
    consumers: ["ferro"],
  },
  {
    name: "shared-state",
    version: "0.1.0",
    layer: "L1",
    purpose: "Shared/app-state plumbing",
    consumers: [],
  },
  {
    name: "eventbus-kit",
    repo: "eventbus",
    version: "0.3.0",
    layer: "L1",
    purpose: "In-process event bus",
    consumers: [],
  },
  {
    name: "cas-kit",
    version: "0.1.0",
    layer: "L1",
    purpose: "BLAKE3 content-addressed blob store — packfiles, zstd, verify-on-read (zero-unwrap)",
    consumers: [],
    features: "`zstd` (default)",
  },
  {
    name: "webauthn-kit",
    version: "0.1.0",
    layer: "L1",
    purpose: "Custom CTAP2/COSE WebAuthn over `ring` — registration/authentication verification, sign-count state machine, challenge/replay store",
    consumers: [],
    features: "`serde`",
  },
  {
    name: "plychart",
    repo: "plychart",
    version: "0.2.0",
    layer: "L1",
    purpose: "Full-featured graphing library for Rust/WASM — Canvas2D rendering, zero dependencies, zero watermarks; builds on `plycore`",
    consumers: [],
  },
  {
    name: "plycompute",
    repo: "plychart",
    version: "0.2.0",
    layer: "L1",
    purpose: "Quantitative computation — portfolio analytics, risk metrics, signal processing; builds on `plycore`",
    consumers: [],
  },

  // ---- L2 — Service infrastructure ----
  {
    name: "cache-pal",
    repo: "cachekit",
    version: "0.3.0",
    layer: "L2",
    purpose: "Caching abstractions",
    consumers: [],
  },
  {
    name: "poolkit",
    version: "0.1.0",
    layer: "L2",
    purpose: "Connection/resource pooling",
    consumers: [],
  },
  {
    name: "envstack",
    version: "0.2.0",
    layer: "L2",
    purpose: "Layered env/config loading",
    consumers: ["crawlkit"],
  },
  {
    name: "otelkit",
    version: "1.0.0",
    layer: "L2",
    purpose: "OpenTelemetry setup helpers",
    consumers: ["EvergreenShims"],
  },
  {
    name: "healthkit",
    version: "1.0.0",
    layer: "L2",
    purpose: "Health/readiness endpoints",
    consumers: ["axum-stack", "ecom-engine (vendored)"],
  },
  {
    name: "webhookkit",
    version: "1.0.0",
    layer: "L2",
    purpose: "Signed outbound webhooks + HMAC verification",
    consumers: ["ecom-engine (vendored)"],
  },
  {
    name: "mailkit",
    version: "0.2.0",
    layer: "L2",
    purpose: "Transactional email sending + JWZ-lite message threading",
    consumers: ["ferro"],
  },
  {
    name: "tantivy-helper",
    repo: "tantivy-ext",
    version: "0.2.0",
    layer: "L2",
    purpose: "Tantivy search index helpers",
    consumers: [],
  },
  {
    name: "api-paginate",
    repo: "paginate",
    version: "0.1.0",
    layer: "L2",
    purpose: "Cursor/offset pagination",
    consumers: [],
  },
  {
    name: "decimal-money",
    repo: "money",
    version: "1.0.0",
    layer: "L2",
    purpose: "Decimal money type",
    consumers: ["billing-kit", "ecom-engine (vendored)"],
  },
  {
    name: "tamper-audit",
    repo: "auditlog",
    version: "0.2.0",
    layer: "L2",
    purpose: "Tamper-evident audit logging",
    consumers: [],
  },
  {
    name: "json-envelope",
    version: "0.1.0",
    layer: "L2",
    purpose: "Signed/encapsulated JSON payloads",
    consumers: [],
  },
  {
    name: "http-errors",
    repo: "http-error",
    version: "0.1.0",
    layer: "L2",
    purpose: "HTTP error mapping",
    consumers: [],
  },
  {
    name: "pid-manager",
    version: "0.1.0",
    layer: "L2",
    purpose: "PID file management for services",
    consumers: [],
  },
  {
    name: "testkit",
    version: "0.1.0",
    layer: "L2",
    purpose: "Shared test utilities/fixtures",
    consumers: [],
    features: "dev-dep only by design",
  },
  {
    name: "media-kit",
    version: "0.1.1",
    layer: "L2",
    purpose: "Media upload/processing helpers",
    consumers: ["ferro", "Tachyon", "ecom-engine (vendored)"],
  },
  {
    name: "flag-kit",
    version: "0.1.1",
    layer: "L2",
    purpose: "Feature flags",
    consumers: ["ferro"],
  },
  {
    name: "blobkit",
    version: "0.3.0",
    layer: "L2",
    purpose: "Object storage abstraction",
    consumers: ["EvergreenShims", "ecom-engine (vendored)"],
  },
  {
    name: "ws-kit",
    version: "0.3.0",
    layer: "L2",
    purpose: "WebSocket server/session management",
    consumers: ["aether-core", "ferro", "ws-barbican"],
  },
  {
    name: "billing-kit",
    version: "0.1.0",
    layer: "L2",
    purpose: "Billing/pricing primitives",
    consumers: [],
  },
  {
    name: "api-types",
    version: "0.1.0",
    layer: "L2",
    purpose: "Shared API request/response types",
    consumers: [],
  },
  {
    name: "axum-stack",
    version: "0.1.0",
    layer: "L2",
    purpose: "Opinionated axum router/middleware stack (healthkit + shutdown-kit)",
    consumers: [],
  },
  {
    name: "multi-chain-wallet",
    repo: "hdwallet",
    version: "0.1.0",
    layer: "L2",
    purpose: "Multi-chain wallet/HDWallet",
    consumers: [],
  },
  {
    name: "actor-kit",
    version: "0.2.1",
    layer: "L2",
    purpose: "Work-stealing actor runtime — OTP supervision trees, crossbeam steal, bounded backpressure; `ResourcePolicy` hook",
    consumers: [],
    features: "`serde`, `unsafe-pool` (opt-in arena), `zero-copy`",
  },
  {
    name: "docs-pipeline",
    version: "0.1.0",
    layer: "L2",
    purpose: "Markdown → HTML pipeline — pulldown 0.13, tree-sitter 0.25 highlighting (TOML+Markdown restored), TOC, sanitize, MDX",
    consumers: ["Tachyon (tachyon-renderer re-export)"],
    features: "per-language `lang-*` features",
  },

  // ---- L3 — Application frameworks ----
  {
    name: "barbican",
    version: "0.2.0",
    layer: "L3",
    purpose: "Secrets/credential custody service toolkit",
    consumers: ["ws-barbican"],
  },
  {
    name: "accessctl",
    version: "0.1.0",
    layer: "L3",
    purpose: "Access control / authorization",
    consumers: [],
  },
  {
    name: "fetchkit",
    version: "0.1.1",
    layer: "L3",
    purpose: "Hardened outbound HTTP fetcher (breaker-integrated)",
    consumers: [],
  },
  {
    name: "ws-barbican",
    version: "0.1.1",
    layer: "L3",
    purpose: "WebSocket transport to barbican (ws-kit + tokenkit)",
    consumers: ["aether-core"],
  },
];

export const LAYERS: Layer[] = ["L0", "L1", "L2", "L3"];

export const LAYER_DESCRIPTIONS: Record<Layer, string> = {
  L0: "Leaf utilities (no internal deps)",
  L1: "Core primitives",
  L2: "Service infrastructure",
  L3: "Application-level frameworks",
};

/** Aggregate stats derived from the registry data. */
export const stats = {
  crates: KITS.length,
  stable: KITS.filter((k) => !k.version.startsWith("0.")).length,
  pre10: KITS.filter((k) => k.version.startsWith("0.")).length,
  byLayer: Object.fromEntries(
    LAYERS.map((l) => [l, KITS.filter((k) => k.layer === l).length]),
  ) as Record<Layer, number>,
};
