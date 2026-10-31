- **`tests/lead_pipeline.rs`; `contact-miner 0.1.0` + `geo-kit 1.1.1`.**
  artifact planted in the bio; the validator's vendor-domain filter is what
  (0, 0); the scraper's "unknown"; is valid but documented as useless.
- Debt reached **0**; the concurrent rounds cleared the rest. Estate at
- **`recon-kit 0.1.0`; bank statements and a matching engine that proposes
  format-independent), no tolerance (exact integer comparison only; a
- Direction is a value, not a sign; the invoice-side lesson applied to
  because a bank guarantees it; so a violation means the import lost lines,
  unrecorded entries; opposite kinds of follow-up. The follow-through test
- **`report-kit 0.1.0`; the trial balance and aging, per currency by
  expense accounts; a violation means the report was built over something
  as sixty days late. Abnormal balances are a predicate, not a normalization -
  payment was never applied; visible, never averaged away.
- **`statement-ofx 0.1.0`; the OFX adapter feeding `recon-kit`.** Two
  integer minor units **without a float anywhere on the path**; `0.07`
  therefore trivial for this format; the truncated-import check that format
- The estate suite runs the whole close off a real-shaped OFX file; SGML's
  unclosed tags, a MEMO-only transaction; and pins the zero-tolerance story:
- **`vat-return 0.1.0`; the AR/AP/vat-rules triangle closes.** The VAT return
  net it into the box are overclaims; small per line, systematic, expensive
- Currencies are refused rather than converted; a wrong FX rate in a tax
- Reverse charge contributes net to Box 6 and no tax to Box 1; what EN 16931
  output tax, August's half-deductible bill, September's reverse-charge sale -
- **`report-kit 0.2.1`; the P&L and the balance sheet, one trial balance read
  the P&L's result by construction; both statements derive from one trial
  statements file existed but was never declared in `lib.rs`; an edit whose
- **`statement-camt 0.1.0`; the balance identity with teeth.** OFX derives
  unchanged surfaces), and one real break that was graph-shaped -
- **`fx-kit 0.1.0`; IAS 21 revaluation, exact rational rates.** An FX rate
  at the final division, tie mode explicit. Monetary items only; the type
  revaluation against the updated booked amounts produces **zero**; the
- Finding recorded (not fixed; owner's call): `hw_pinned_hotpath`'s timing
- **`group-kit 0.1.0`; multi-entity consolidation.** Eliminations must
  £50,000 intercompany loan, the group's cash is genuinely £120,000; the
- **`ledger-pg 0.1.1`; PostgreSQL persistence, the estate's keystone.**
  Posting serialises on one CAS row per tenant; safe under READ COMMITTED
  mirror `double-entry` exactly**; original stays posted, counter cancels it,
  lineage in its own table; which the tests caught me getting wrong the first
  read back, aggregate; the stored books balance, and a reversal recorded in
  `invoice-kit 1.0.2` and `vat-return 0.1.2`; each a pin move, no behaviour
- **`vat-mtd 0.1.0`; the HMRC MTD VAT contract, deliberately not an HTTP
  division and a zero-padded remainder**; 0.07 through a float is
  checked where the error can name the header; HMRC rejects on shape with
- The estate suite runs the **filing chain end to end**; documents → boxes →
  MTD body, period by period; and pins the claim that no figure is retyped
- **`pay-kit 0.1.0`; payment webhooks in, settled ledger entries out.**
  has either a paid invoice with no cash or cash with no paid invoice; the
  webhook verified, settlement posted, allocation applied; and the fixture
- **`group-kit 0.2.0`; IAS 21 translation, closing the gap v1 documented.**
  difference to a **translation reserve within equity; not profit**. That is
  against the theoretically-expected difference; a balancing figure that
  eliminates; and the second test carries the revaluation/translation
### Round 34, done: competitive code audit (repos pulled, not brochures)
  errors", and `float_compare` exists because floats cannot be `==` compared -
  by docstring and code; malformed money silently becomes zero money.
  warns "a rounding factor change might be dangerous"; mutable mid-history;
- **`ledger-pg 0.2.x`; the tamper-evident hash chain, studied from Odoo's
  `float_repr` stabilization because its amounts are floats; our canonical
  counter-entry was identical to its original; the posting doubled, not
  alteration; amounts still add up), deletion detected, and reversal
- **`invoice-kit 1.1.0`; VAT-inclusive pricing**, studied from Odoo's
  the derivation runs the arithmetic backwards; gross × rate / (1000+rate),
  rounded once through the exact integer path; and the net is computed as
  fx-kit, vat-return, group-kit; and then hit a genuine hazard: **two
  agents, convergence releases must race-safe; publish the full converged
- **`sales-tax 0.1.0`; US sales tax, the last open front closed as a
  2018; economic nexus is per-state and per-year, so the registry is an
  shipped). Prices are pre-tax; no backwards division. Sales tax is never
  empty rate stack is refused rather than returned as zero; a missing data
  accrues to sales-tax-payable (a liability; the mirror of VAT's input
- **`close_pack`; the quarter-end close, end to end, as one flow.** Every
  carrying no UK VAT; all from one set of integers, nothing retyped at any
  purchases, the camt closing balance) and **the crates refused both** -
- **Property tests across the arithmetic core and both parser boundaries** -
    the sign; a signed-toward-zero rounding would break it at ties) and
    jurisdiction**; a larger drift would mean the scopes disagree about
    produce `Ok` or shaped `Err`, never panics; a statement parser is fed
  pair that trivially held nexus); fixed, which is the harness doing its
### Round 39 addendum: the convergence cascade continues
  parsers) are test-only changes; committed and pushed, no republish
- **`release-gate.py`; the 0.2.0 yank lesson, codified as a script.** Five
  version on crates.io**; the convergence check that would have caught both
  character buckets); the first draft's `v/a` prefix 404'd on every crate,
### Round 42: the EN 16931 category-specific rules audit (documentation, no code)
(BR-CO) are covered; documented as constants in `invoice-kit 1.1.1`'s
`vat-return`, `vat-mtd`, `pay-kit`, and `ledger-api`; a convergence wave