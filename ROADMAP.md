# ROADMAP: loop 2

Recreated 2026-10-05, after the research step in [LOOP.md](LOOP.md). Loop 1
hardened the *templates*. Loop 2 hardens the *library estate* and starts the
product that the estate exists to serve.

The premise of this loop: **a published crate is a claim, not a proof.** Every
crate in the manifest is published, versioned, documented, and green on CI, and
five of them were still wrong in ways that cost users money or lock them out.
This loop therefore treats *dogfooding across crate boundaries*: and *checking
implementations against primary sources rather than against themselves*: as the
primary work, not a side effect of it.

## What loop 1 produced (and why loop 2 exists)

Loop 1's gates are green across the templates: Scorecard, zizmor, osv-scanner,
macOS/Windows legs, the nix devcontainer. The estate's own audit reports
**0 errors and 0 pin drift** over 182 repos and 161 crates.

That clean bill of health was misleading, and the gap is the whole reason for
this loop:

| Crate | Green CI said | Reality |
|---|---|---|
| `multi-chain-wallet` | 41 tests passing | **Every BIP-39 phrase shorter than 24 words was refused.** A wallet's recovery phrase did not restore. Two of its own suites asserted the limitation as intended behaviour. |
| `webauthn-kit` | 166 tests passing, 6 red | The red ones were *fixtures with the wrong COSE label*, so they could never have agreed with a real authenticator. `clippy --all-targets` failed on master. |
| `webauthn-kit` | sign-count check "monotonic" | Accepted an equal counter: the signature of a replayed assertion. |
| `actor-kit` | `pause()` documented | A permanent deadlock. Then, once fixed, messages queued during suspension were silently never processed. |
| `hdwallet`/`actor-kit`/`shared-state` | fix merged to `main` | Fixes **never released**. The pinned versions still carried the bugs. |

Three failure modes, each worth a permanent defence:

1. **A suite that encodes the bug as the contract.** `proptest.rs` asserted that
   the word-count argument *must be ignored*; a fuzz test asserted that an equal
   counter *must* be accepted. Green forever, wrong forever. → **Defence: a
   finding may only be pinned by a test that states the specification.** Where a
   spec disagrees with the code, the suite is the defect.
2. **Fixtures built from the implementation, not the spec.** Wrong COSE labels,
   self-generated BIP-39 phrases, a `zoo … wrong` "invalid vector" that is in
   fact a *valid* specification vector. → **Defence: every crypto crate pins at
   least one primary-source vector verbatim.** Published bytes cannot drift.
3. **A fix on `main` that is not a release.** Three fixes, zero releases.
   → **Defence: the audit treats "pinned version < fixed version" as drift, and
   the loop's release step is part of the loop, not an afterthought.

## Research step (2026-10-05)

Primary sources pulled and analysed. The findings that change what we build:

- **OAuth 2.1 `draft-ietf-oauth-v2-1-16` §7.5.2 forbids PKCE `plain` outright.**
  The justification for dropping it: *"obsoleted by OAuth 2.1's requirement for
  TLS 1.2+, which mandates SHA-256… Any device capable of implementing OAuth 2.1
  necessarily supports SHA-256."* Our `oauth-toolkit` takes the method as a
  `&str`, so a typo'd method is indistinguishable from a wrong verifier.
- **WebAuthn L3 is a W3C Recommendation (2026-08-25).** §7.2 step 18: a counter
  that does not increase is *"a signal, but not proof"*: and explicitly
  includes *"a race condition where the Relying Party is processing assertion
  responses in an order other than the order they were generated."* This
  **corrects our own 0.3.6 fix**: hard-failing on `<=` will produce spurious
  lockouts for any RP that processes assertions concurrently.
- **WebAuthn L3 §7.2 last step:** state updates (`signCount`, `backupState`,
  `uvInitialized`) SHOULD be deferred until after additional security checks
  succeed. And §2.4 makes CTAP2 canonical CBOR a MUST, with duplicate map keys
  to be rejected.
- **`bip32` 0.6.0 removed the `bip39`/`mnemonic` features outright** (upstream
  PR #1394). Root cause of our bug: `bip32 0.5.3` types entropy as `[u8; 32]`,
  so 128-bit entropy is *unrepresentable*, not merely unvalidated. There is no
  upstream issue. Our move to standalone `bip39` is the forward-compatible one.
- **BIP-32 mandates rejecting invalid keys**, including 16 vectors in test
  Vector 5, and states that a parent xpub plus any non-hardened child private
  key **is** the parent private key.
- **Rounding authorities conflict, and the hardware default picks a side.**
  IEEE 754's default is half-even; ZATCA E-Invoicing vF §10 mandates half-up.
  ISO 2 §3.3 and GB/T 8170-2008 §3.3.1 both forbid successive rounding. → No
  default rounding mode in a money type.
- **ISO 4217 is wrong for two live currencies.** MRO and MGA are 1/5-scaled but
  coded as exponent `2`, so integer+exponent cannot represent their subunit.
- **ISO 20022 requires the currency on the amount** (`Ccy` mandatory,
  `fractionDigits 5`, `minInclusive 0`) with negativity carried by `CdtDbtInd`,
  never a minus sign.
- **PostgreSQL SERIALIZABLE can raise a unique violation that true serial
  execution never would** (§13.2.3), and the docs say check-then-insert is
  *provably insufficient* under SSI. → The ledger's posting path is designed
  from this, not retrofitted to it.
- **SCIM PATCH is atomic and mostly optional**, `remove` with no filter destroys
  every value of a multi-valued attribute, and `Operations` is capitalised.
- **FAPI 2.0** (Final, 2025-02-22): auth codes ≤ 60 s, PAR mandatory,
  sender-constrained tokens, ≥ 128-bit credential entropy.

### Where the sources disagree: the most valuable findings

- `plain` PKCE: forbidden by OAuth 2.1 `-16` and FAPI 2.0, still permitted by
  RFC 7636. Our crate followed the oldest document.
- Rounding: ISO 80000-1 / ASTM E29 / OPC UA say half-even; ZATCA and the
  European Pharmacopoeia say half-up. "Swiss rounding" is not an ISO term.
- BIP-39's checksum catches ~255/256 of errors: the checksum is
  error-*detection*, not a security property, so 24 words is 2²⁵⁶ bits of
  entropy, never 264. The real attack surface is the entropy source (Milk Sad /
  CVE-2023-39910 drained 227k+ addresses).

## Loop 2 backlog

Ordered by (correctness impact × how often it bites).

### Now: security, primary-source-backed

1. `oauth-toolkit`: reject `plain` at the AS; `S256` only. Distinguish an unknown
   method from a wrong verifier. *(OAuth 2.1 -16 §7.5.2)*
2. `webauthn-kit`: counter regression is a **signal, not proof**. Expose a
   policy so an RP can score rather than lock out, defaulting to fail-closed;
   document the out-of-order race. Defer credential state updates past
   additional checks. *(L3 §7.2)*
3. `webauthn-kit`: reject duplicate CBOR map keys; enforce CTAP2 canonical
   ordering where we encode. *(L3 §2.4)*
4. `multi-chain-wallet`: upgrade `bip32` 0.5 → 0.6 (borrowing `XPrv` APIs, no
   mnemonic features); pin BIP-32 Vector 3/4/5 including all 16 invalid-key
   vectors; refuse to derive a non-hardened child from an exported account
   xpub, since BIP-32 says that is the parent private key.

### Now: money correctness

5. `decimal-money`: `RoundingMode` becomes an explicit parameter with **no
   default**; a named `round_at` boundary type so a caller cannot round twice.
   Add the `97.46 → 97.5 → 98` successive-rounding regression.
6. Currency: model `minor_unit: Option<u8>` (ISO 4217 `n.a.` ≠ `Some(0)`), and
   quarantine MRO/MGA, whose subunit is 1/5 and cannot be represented as an
   integer at exponent 2.
7. Serialisation: amount + currency together; no bare decimal on the wire.

### Round 15, done

- `multi-chain-wallet 0.3.0`: `bip32 0.6` + `k256 0.14`, with the BIP-32
  conformance suite written *before* the upgrade so it could prove the migration
  rather than follow it. All four derivation vectors match the specification byte
  for byte; derived addresses are unchanged.
- **Vector 5 measured, not assumed:** `bip32 0.6.0` accepts four of the sixteen
  invalid extended keys. The wallet now enforces all sixteen itself.
- **`k256 0.14` removed `sign_prehash_recoverable`** and offers a replacement
  that *hashes* its input: a silent, total signature failure for a wallet.
  `signing_prehash` signs the prehash directly, with a regression test asserting
  the two paths differ.
- **`webhookkit 2.2.0` stopped compiling** with no change to its own manifest,
  because `k256 → sec1 → hybrid-array/subtle` enables an `Array::ct_eq(&Array)`
  impl that shadows `subtle`'s slice impl, and feature unification is
  workspace-wide. Fixed in `2.2.1`. This is the clearest argument yet for
  composing crates in one graph.
- Six repos appeared from another wave while this loop worked; all six are now in
  the manifest with the status their nature implies, including a *private* TeX
  repo recorded as `personal` rather than quietly omitted.

### Round 17, done

- **`invoice-kit 0.1.0`: the product's AR layer**, published with a consumer
  suite in the same loop. Three orthogonal document states because EN 16931
  defines no lifecycle at all; direction on the document type because Peppol's two
  credit conventions must never be mixed; a required `RoundingPolicy` because four
  jurisdictions mandate mutually incompatible arithmetic; integer-minor-unit
  allocation because three production incidents in a deployed accounting system
  were caused by float arithmetic on allocation.
- **Five bugs caught by its own tests before publication**, the worst being a
  division that inflated every quotient by a power of ten, and a line arithmetic
  that used `rescale_exact` where the specification requires a *rounding*: so
  any unit price that was not an exact multiple of its base quantity produced no
  amount at all.
- **Three money types now in the workspace** that disagree about what an amount
  is: a decimal value (`ledger-kit`), an integer count of minor units
  (`double-entry`), and an integer at an explicit scale (`invoice-kit`). The
  sharpest consequence is pinned: 1000 minor units is $10.00 and ¥1000 depending
  only on the exponent, and the two do not even render as the same string.

### Now: the product

The estate's library work has reached the point where the remaining defects are
in the *product* semantics, not the primitives. So the product starts now.

8. New repo, immutable double-entry core: append-only journals, balanced
   debits/credits enforced at post time, `draft → posted → void` states,
   **reversal by counter-entry** rather than deletion or mutation, period close,
   and audit trail. No standard defines draft/posted/void for journal entries:    TigerBeetle is the closest implementable model and IFRS specifies only
   recognition/derecognition: so this is a documented decision, not a derived
   one.
9. Posting concurrency designed from PostgreSQL §13.2.3: the ledger must not
   rely on check-then-insert under SERIALIZABLE, because SSI can raise a unique
   violation that true serial execution never would.
10. New domain crates as the product grows: `invoice-kit` (AR), AP, tax,
    reconciliation, reports. Each gets an estate-integration suite from the day
    it is published: a crate with no suite is not finished.


### Round 18, done

- **`vat-rules 0.1.0`: the tax vocabulary both sides of a ledger share.**
  Extracted from invoice-kit rather than duplicated, because AP needs the same
  UNCL5305 categories, CEF `VATEX-*` reasons, UNTDID 1001 codes and rounding
  regimes. Zero dependencies by design: `TieMode` is policy vocabulary, not
  arithmetic machinery, so a table of tax codes does not depend on a
  double-entry engine to say "round ties away from zero".
- **`invoice-kit 0.2.0/0.2.1`: re-exports plus a real rounding fix.** The
  0.2.1 finding matters more than the extraction: **the three Australian
  rounding modes were one algorithm wearing three names.** `GstTotalInvoice`
  rounded per (category, rate) group, so it was `En16931Group` with a different
  label, but GST Act s9-90's total-invoice method adds *unrounded* GST per
  supply and rounds once: two lines of 5c at 10% and 5c at 30% are 3c per-group
  and 2c total-invoice. Real money. `GstTaxableSupply` rounded per group, not
  per supply. Under a single rounding the breakdown cannot be built from
  independently-rounded groups and still satisfy BR-S-08/S-09, so the residual
  is attributed to the largest unrounded group. `Decimal::round_div` also lost
  a cent on negative ties: the tie comparison runs on the magnitude now, because
  truncation toward zero makes "which neighbour is even" ill-defined for a
  negative quotient. Six new tests; three fail against the previous code.
- **`ap-kit 0.1.0/0.1.1`: accounts payable, where tax is a three-way split.**
  A purchase bill produces three outcomes, not two, because the gross payable
  always includes the full tax whether or not Article 168 lets the business
  claim it back: payable (gross), deductible tax (asset), non-deductible tax
  (expense). Two documented asymmetries: recoverability never changes what is
  owed to the supplier; and the supplier's line net is **authoritative data**,
  not a derivation: AP receives documents, it does not issue them. Rates above
  100% are refused, because 19% entered as 1900 per-mille is a 190% posting no
  other check catches.
- **The estate suite caught a half-done extraction on its first run**: ap-kit
  did not re-export the shared vocabulary, so a consumer of both crates could
  not name one `TaxCategory` through either path. Fixed in 0.1.1 and now
  asserted at runtime: the suite requires `invoice_kit::TaxCategory ==
  ap_kit::TaxCategory` to compile.
- The payable suite also pins the ledger identity behind a VAT return: the same
  19.00 is a credit to output VAT when charged and a debit to input VAT when
  reclaimed, so the two net to zero by construction. Six `double-entry`
  integration tests post the original-then-reversal pair for a supplier credit
  note, which is where the optimistic-concurrency guard earned its keep.
- Estate at 196 repos, 169 crates, 83 exact pins, 0 errors, 0 drift, debt 14.
  All-features: 40 test groups green, clippy clean, fmt clean.
- Two concurrent repos (`audiobook-shelf`, `crawlkit-testbed`) registered on
  sight; `media` is not a schema area, so audiobook-shelf is `personal`.


### Round 19, done

- **`tests/ipc_stack.rs`: the IPC stack, clearing three debt crates at once.**
  `axum-stack 0.2.0` (health routes), `poolkit 0.1.2` (sqlite pool behind the
  `Any` facade) and `uds-kit 0.1.0` compose in the shape a real local service
  takes: HTTP over a Unix domain socket, backed by pooled storage, with a
  client that formats its own HTTP/1.0 frames because uds-kit is transport only.
- The deadline tests run against live peers, not mocks: ENOENT must surface as
  an immediate `UdsError::Io` and never as `ConnectTimeout`: collapsing the two
  would make a misconfigured path indistinguishable from a hung one: and a
  peer that accepts and stays silent must hit the read deadline rather than the
  test timeout, which is the exact ClamAV-shaped hang the crate was written to
  close.
- The health check is a real `SELECT 1` through the pool, so an unhealthy
  database makes `/health` unhealthy instead of the check being a constant.
  Working detail worth knowing before designing around `DbPool`: it is not
  `Clone`, so shared state carries an `Arc` and the health closure clones the
  inner sqlx pool.
- Debt 14 → 11. Estate at 197 repos, 169 crates, 86 exact pins, 0 errors,
  0 drift. 41 test groups green, clippy clean, fmt clean.
- `hosting-dashboard` registered on sight (area `app`).


### Round 20, done

- **`tests/spreadsheet_diff.rs`: `sheet-xlsx 0.1.1` + `delta-kit 0.2.1`,
  clearing two more debt crates.** A versioned spreadsheet needs two diffs that
  agree: the semantic one a user is shown, and the byte one history stores. The
  suite computes both and closes the loop: the byte reconstruction is read
  back through `read_xlsx` and its semantic diff must equal the original's,
  because byte equality alone proves only that two `Vec`s matched.
- Documented rather than worked around: delta-kit has **no inverse in its
  API**. Undo is the forward delta from target back to base, computed at save
  time before the old bytes are gone: an API-shaped fact worth writing down.
- Corruption pinned at every cut point: a truncated delta is an error at 0,
  half, and len-1; the empty delta has its own variant; a delta applied to the
  wrong base must never silently pass as the target.
- Debt 11 → 9, 88 exact pins, 42 test groups green, clippy clean, fmt clean.


### Round 21, done

- **`tests/lead_pipeline.rs`; `contact-miner 0.1.0` + `geo-kit 1.1.1`.**
  A lead-gen pipeline mines contacts out of profile pages, validates them, and
  files them with a postal address. The composition gate is the point: a lead
  is stored only if its email validates **and** its postcode parses, and
  neither crate can enforce that alone.
- The fixture carries what real scraped pages carry, including an anti-bot
  artifact planted in the bio; the validator's vendor-domain filter is what
  keeps it out of the store, which is the crate's own knowledge proving itself
  against a live fixture. `display_name` comes from `og:title` metadata, not
  headings, which the first fixture got wrong and the parser correctly refused
  to invent.
- UK postcodes normalise on the way in (`S118PM` and `S11 8PM` land
  identically); an impossible postcode closes the gate; coordinates are
  validated before reaching a lead, and latitude beyond ±90 is refused while
  (0, 0); the scraper's "unknown"; is valid but documented as useless.
- A concurrent agent shipped `tests/geo_contacts.rs` for the same pair; the
  merge kept one pin set and both suites, which now cover the pair from
  extraction and storage angles respectively.
- Toolchain note: the merge brought `egui`/`comfyui-kit` pins requiring
  rustc ≥ 1.95; the box's default was 1.94.1, so estate-integration now runs
  under a directory-local override to 1.97.1. Global default untouched.
- Debt reached **0**; the concurrent rounds cleared the rest. Estate at
  227 repos, 195 crates, 124 exact pins across 3 consumer repos, 0 errors,
  0 drift. 55 test groups green, clippy clean, fmt clean.


### Round 22, done

- **`recon-kit 0.1.0`; bank statements and a matching engine that proposes
  instead of guessing.** Three deliberate absences: no format parsing (OFX,
  CAMT.053 and the forty CSV dialects are adapters; the model beneath them is
  format-independent), no tolerance (exact integer comparison only; a
  one-cent allowance hides drift that compounds while the recon report looks
  clean), and no silent auto-matching (`Proposal::Ambiguous` surfaces both
  candidates instead of picking one; a wrong auto-match misattributes money in
  the books while the reconciliation still balances, so nothing downstream
  ever catches it).
- Direction is a value, not a sign; the invoice-side lesson applied to
  statements. OFX signs amounts, CAMT carries an indicator;
  `Direction::from_signed` normalises at the boundary and the sign convention
  never reaches the engine.
- The balance identity (`opening + Σ(±lines) == closing`) is the import check,
  because a bank guarantees it; so a violation means the import lost lines,
  which is exactly the failure that looks like fine individual rows. Day
  arithmetic is Hinnant's `days_from_civil`, pinned against leap years and
  century boundaries.
- The estate suite runs a real month-end close: invoice-kit prices the
  invoices, double-entry posts the settlements, the statement matches against
  the postings, and the leftovers split into in-transit lines versus
  unrecorded entries; opposite kinds of follow-up. The follow-through test
  enters the missing card charge and re-closes: the ledger's movement then
  equals the statement's movement to the penny. And matching never mutates the
  ledger, because the close is a report.
- Estate at 228 repos, 196 crates, 125 pins, 0 errors, 0 drift, debt 0.
  56 test groups green, clippy clean, fmt clean.


### Round 23, done

- **`report-kit 0.1.0`; the trial balance and aging, per currency by
  construction.** Summing a GBP bank account with a JPY fee account is a
  number in no currency; the double-entry invariant is stated per posting, so
  debits-equal-credits is checked per currency, and a ledger balanced in GBP
  and unbalanced in JPY is reported as exactly that.
- The accounting equation (`assets + expenses == liabilities + equity +
  revenue`) is a runtime check at any cut-off. It holds without closing
  entries because the period's result is still sitting in the revenue and
  expense accounts; a violation means the report was built over something
  that is not a balanced ledger, and the correct response is to stop, never
  to fudge a row.
- Aging runs from the **due date**, not the issue date: net-60 terms are
  current for two months, and aging from issue would show a healthy customer
  as sixty days late. Abnormal balances are a predicate, not a normalization -
  a credit balance on a bank account is an overdraft, a real state a reader
  can find.
- The estate suite pins the composition's quiet invariant: the aging
  population derived from the invoices equals the debtor balance derived from
  the postings. If they ever disagree, an invoice was never posted or a
  payment was never applied; visible, never averaged away.
- Estate at 229 repos, 197 crates, 126 pins, 0 errors, 0 drift, debt 0.
  57 test groups green, clippy clean, fmt clean.


### Round 24, done

- **`statement-ofx 0.1.0`; the OFX adapter feeding `recon-kit`.** Two
  normalisations, performed exactly: signs become `Direction` at the boundary
  (the invoice-side lesson applied to bank files), and decimal strings become
  integer minor units **without a float anywhere on the path**; `0.07`
  through a float is `6.999999999999999`, and which way that rounds decides
  whether a statement line matches. More fraction digits than the declared
  scale is an error, not a truncation: a truncated penny is a line that no
  longer matches.
- Recorded rather than papered over: OFX publishes the closing balance but not
  the opening one, so the adapter derives it and the balance identity is
  therefore trivial for this format; the truncated-import check that format
  can offer is CAMT.053's, which carries both balances.
- Scale is explicit because OFX does not declare it; JPY statements parse at
  scale 0, and the default-2 assumption would have moved every decimal point
  in the file.
- The estate suite runs the whole close off a real-shaped OFX file; SGML's
  unclosed tags, a MEMO-only transaction; and pins the zero-tolerance story:
  one penny of drift in the bank's file stops the line matching at any window,
  with both sides naming the discrepancy.
- Estate at 230 repos, 198 crates, 127 pins, 0 errors, 0 drift, debt 0.
  58 test groups green, clippy clean, fmt clean.


### Round 25, done

- **`vat-return 0.1.0`; the AR/AP/vat-rules triangle closes.** The VAT return
  computed from the documents themselves, and the rule the crate exists to
  enforce: **only deductible input tax reaches Box 4.** A bill's gross
  includes tax the business may never reclaim (Article 168), and returns that
  net it into the box are overclaims; small per line, systematic, expensive
  when an authority finds them. The crate takes bills, not numbers, so it
  cannot be handed a raw tax total by mistake; the non-deductible part's net
  still counts in Box 7, because the cost is a purchase even when the tax is
  not reclaimable.
- Currencies are refused rather than converted; a wrong FX rate in a tax
  filing is worse than a missing filing. A document outside the period is a
  loud error, because a wrongly pre-filtered return shifts tax between periods
  silently.
- Reverse charge contributes net to Box 6 and no tax to Box 1; what EN 16931
  puts on the document. UK domestic reverse-charge filing rules are out of
  scope and documented, rather than half-guessed.
- The estate suite runs a whole quarter period-by-period: July's £24,000
  output tax, August's half-deductible bill, September's reverse-charge sale -
  and Box 1 is asserted to be the same tax the invoices charged, to the penny.
- Estate at 231 repos, 199 crates, 128 pins, 0 errors, 0 drift, debt 0.
  59 test groups green, clippy clean, fmt clean.


### Round 26, done

- **`report-kit 0.2.1`; the P&L and the balance sheet, one trial balance read
  two ways.** A balance sheet drawn mid-period does not satisfy
  `assets == liabilities + equity`, because the period's profit is still
  sitting in the revenue and expense accounts. The honest statement adds the
  **retained result** where it actually is:
  `assets == liabilities + equity + retained result`. The retained result is
  the P&L's result by construction; both statements derive from one trial
  balance, so a profit on the P&L that is missing from the balance sheet is a
  bug the structure cannot express. `is_balanced` refuses to plug an
  "unexplained difference" line.
- **The process finding of the round: 0.2.0 shipped without the module.** The
  statements file existed but was never declared in `lib.rs`; an edit whose
  target string rustfmt had reordered failed silently, the file compiled into
  nothing, and the release went out as 0.1.0 under a new number. The tell was
  the test count: 8, not 13. Recorded in the changelog so nobody trusts the
  version; the feature is 0.2.1. Lesson: a silent `str.replace` is not an
  edit, and a test count that does not move when a feature lands is a feature
  that did not land.
- Estate suite pins the composition: the P&L result equals the balance
  sheet's retained result, the sheet balances, and the revenue is the same
  pennies invoice-kit priced.
- Estate at 231 repos, 199 crates, 128 pins, 0 errors, 0 drift, debt 0.
  59 test groups green, clippy clean, fmt clean.


### Round 27, done

- **`statement-camt 0.1.0`; the balance identity with teeth.** OFX derives
  the opening balance, which makes the balance identity trivially true and
  the truncated-import check inert. CAMT.053 carries both balances
  (`OPBD`/`CLBD`), so the adapter reads them at face value and an import that
  loses an entry fails **on arrival** with `BalanceIdentityFailed` naming all
  three numbers. The estate suite proves the contrast: dropping an entry from
  the CAMT file while keeping the declared balances is refused with the
  numbers; the same loss in OFX is invisible.
- Booked entries only: a `PDNG` entry is money the bank has seen but may
  still reverse; a missing status block fails closed. Signs come from the
  format's own `CdtDbtInd`. Namespace-agnostic across `camt.053.001.02–.08`.
- The estate also reconciled the 2026-10-23 release wave: six pin bumps
  (`invoice-kit 1.0.0` and `ledger-kit 1.0.0` are API-stability signals on
  unchanged surfaces), and one real break that was graph-shaped -
  `vat-return` bound `invoice-kit 0.2.1` while the estate moved to 1.0.0,
  carrying two non-interoperable `Invoice` types. `vat-return 0.1.1`
  republishes against 1.0.0.
- Estate at 233 repos, 200 crates, 129 pins, 0 errors, 0 drift, debt 0.
  60 test groups green, clippy clean, fmt clean.


### Round 28, done

- **`fx-kit 0.1.0`; IAS 21 revaluation, exact rational rates.** An FX rate
  is a rational number, and every float on the path from quoted rate to
  posted difference corrupts it; a thousand-row revaluation turns "not" into
  visible pennies of phantom gain. Rates parse from decimal strings into
  exact reduced rationals; restatement multiplies in i128 and rounds **once**
  at the final division, tie mode explicit. Monetary items only; the type
  name makes passing non-monetary items a type error, not a silent
  misstatement. Base-currency rows and missing rates are errors, not 1:1 or
  zero.
- The estate suite pins the idempotence property that matters: re-running the
  revaluation against the updated booked amounts produces **zero**; the
  classic double-revaluation bug is a second gain, and nothing downstream
  catches it. The ledger test posts the differences and proves debits still
  equal credits afterwards.
- Finding recorded (not fixed; owner's call): `hw_pinned_hotpath`'s timing
  tolerance flakes ~1-in-3 under build load (median vs fastest 2x drift).
- Environment note: a concurrent agent's stricter audit methodology
  (CONSUMERS list, branch-ref consumers, a sqlite-side split manifest) landed
  mid-round; the transitional audit shape is theirs to settle.
- Estate at 234 repos, 201 crates. 61 test groups green, clippy clean, fmt
  clean.


### Rounds 29–30, done

- **`group-kit 0.1.0`; multi-entity consolidation.** Eliminations must
  cancel, and anything that does not cancel is surfaced, never guessed: a
  mirror with a disagreeing amount is `IntercompanyMismatch` naming both
  figures, a missing mirror is `OneSidedIntercompany`. The worked example in
  the tests carries the arithmetic a reader checks: after eliminating a
  £50,000 intercompany loan, the group's cash is genuinely £120,000; the
  elimination removes the IC pair, not the cash. Unbalanced entity books are
  refused before any elimination, because two cancelling imbalances could
  launder into a balanced group.
- **`ledger-pg 0.1.1`; PostgreSQL persistence, the estate's keystone.**
  Posting serialises on one CAS row per tenant; safe under READ COMMITTED
  because the `UPDATE` takes the lock, so eight concurrent posters get eight
  distinct versions with no lost writes. Balance is validated inside the
  transaction; a refused entry consumes no version. **The reversal semantics
  mirror `double-entry` exactly**; original stays posted, counter cancels it,
  lineage in its own table; which the tests caught me getting wrong the first
  time: marking the original reversed flips the balance instead of zeroing it.
  `into_ledger` takes the account class chart explicitly after 0.1.0's
  asset-default silently zeroed a P&L. Tests run against a real PostgreSQL
  (container harness, `TEST_DATABASE_URL` override).
- The estate pins **persistence through to the reports**: post to Postgres,
  read back, aggregate; the stored books balance, and a reversal recorded in
  the database moves the reports the same way it moves the books. The
  reversal's date property is pinned too: a correction is dated when it was
  made, so a July cut-off shows July as July reported it.
- **The release wave (2026-10-23/24) split the graph across two exact
  versions of `double-entry`**: `invoice-kit 1.0.0` held 0.1.0 while the
  estate's other crates moved to 0.1.1. Converged by patch releases across
  `ap-kit 0.1.3`, `report-kit 0.2.2`, `group-kit 0.1.2`, `ledger-pg 0.1.3`,
  `invoice-kit 1.0.2` and `vat-return 0.1.2`; each a pin move, no behaviour
  change, each keeping exactly one version of the money crate in the graph.
- Estate at 237 repos, 205 crates, 133 pins, 0 errors, 0 drift from this
  loop's crates. 64 test groups green, clippy clean, fmt clean. ~40 remaining
  drift entries are the concurrent wave's own pins, owned by their publishers.


### Round 31, done

- **`vat-mtd 0.1.0`; the HMRC MTD VAT contract, deliberately not an HTTP
  client.** Coupling a tax contract to a framework choice makes the contract
  harder to test and the framework harder to change; every type serialises
  with serde, so a transport is a few lines at the call site and the
  contract's tests are fixture-exact.
- Money goes from integer minor units to 2dp decimal strings by **integer
  division and a zero-padded remainder**; 0.07 through a float is
  `6.999999999999999`, and this is a filing. Value boxes carrying pence are
  **refused rather than truncated**: dropping 50p is a decision, not a
  default.
- Fraud-prevention headers typed per connection method (`DESKTOP_APP`,
  `WEB_APP`), with value shapes (UUID device IDs, `vendor=x.y.z` versions)
  checked where the error can name the header; HMRC rejects on shape with
  errors that do not.
- `digitalSubmission` is always `true` from this crate: the figures came from
  digital records, and claiming otherwise is not a configuration.
- The estate suite runs the **filing chain end to end**; documents → boxes →
  MTD body, period by period; and pins the claim that no figure is retyped
  anywhere: the pence HMRC receives are the pence the invoices charged. A nil
  return still finalises; HMRC wants the nil, not silence.
- Estate at 238 repos, 206 crates, 134 pins, 0 errors, 0 drift from this
  loop's crates. 65 test groups green, clippy clean, fmt clean. The ~40
  remaining drift entries are the concurrent 2026-10-24 wave's own pins,
  owned by their publishers.


### Round 32, done

- **`pay-kit 0.1.0`; payment webhooks in, settled ledger entries out.**
  One crate because the seam between verification and settlement is where
  payment fraud lands: a webhook that verifies but does not reconcile is a
  notification; one that reconciles without verifying is a remote posting
  API. Verification composes `webhookkit`'s constant-time HMAC; Stripe's
  scheme adds a replay-tolerance window and key rotation (any matching `v1`
  passes, so old and new secrets both work mid-rotation), and a stale
  timestamp is named as a **replay**, not a signature failure, so the caller
  can alert rather than log noise.
- The ordering rule is the security property: **verify first, parse second,
  post last.** The signature covers the raw bytes, so parse-before-verify
  hands an attacker a parse gadget on unauthenticated input.
- `post_settlement` and `allocate` are deliberately separate: the posting is
  a *cash* act, the allocation a *documents* act, and a caller doing only one
  has either a paid invoice with no cash or cash with no paid invoice; the
  split makes the half-done state nameable.
- The estate suite closes the payment loop end to end: invoice priced,
  webhook verified, settlement posted, allocation applied; and the fixture
  caught itself, the webhook's £144 against a £1,440 invoice surfacing as a
  failed allocation before it could surface as a customer statement.
- Estate at 239 repos, 207 crates, 135 pins, 0 errors, 0 drift from this
  loop's crates. 66 test groups green, clippy clean, fmt clean.


### Round 33, done

- **`group-kit 0.2.0`; IAS 21 translation, closing the gap v1 documented.**
  Assets and liabilities at the **closing** rate, income and expenses at the
  **average** rate, equity at **historical** rates, and the cumulative
  difference to a **translation reserve within equity; not profit**. That is
  the sharp distinction from `fx-kit`'s monetary-item revaluation: revaluing
  cash you hold is a P&L event; re-presenting a whole subsidiary's books is
  an ownership-of-net-assets event, and putting its effect through P&L would
  report currency noise as trading performance.
- The reserve is a balancing figure by construction, so the tests pin it
  against the theoretically-expected difference; a balancing figure that
  absorbs anything is the unexplained-difference line this estate refuses
  elsewhere. The fixture caught the reserve being double-negated into a
  debit, which would have made every strengthened-currency close report a
  spurious loss.
- The estate suite runs the **full multi-currency group close** over the
  released artifacts: `fx-kit`'s exact rates translate the subsidiary,
  `report-kit` reads the translated books, `group-kit` consolidates and
  eliminates; and the second test carries the revaluation/translation
  distinction: a moved closing rate changes the reserve and leaves every P&L
  row at its average rate.
- Three concurrent repos registered on sight (`ai-memory`, `detonate-mcp`,
  `memory-handoff-skill`). Estate at 242 repos, 207 crates, 135 pins, 0
  errors. 67 test groups green, clippy clean, fmt clean.


### Round 34, done: competitive code audit (repos pulled, not brochures)

Cloned and read the actual accounting implementations: `odoo` (sparse:
addons/account, addons/base, odoo/tools), `frappe` + `erpnext`, `akaunting`.
Findings with citations, all verified against current main:

- **Odoo's money is floats**, and the code admits it: `float_utils.py`'s
  `float_round` docstring is "minimizing IEEE-754 floating point representation
  errors", and `float_compare` exists because floats cannot be `==` compared -
  with a documented warning that `float_is_zero(a-b)` is not equivalent to
  `float_compare(a,b)==0` for e.g. 0.006 vs 0.002 at 2 digits.
- **ERPNext's `flt()` returns 0.0 for malformed input**: `flt("a")` → `0.0`,
  by docstring and code; malformed money silently becomes zero money.
  Precision is a global setting (`self.precision(field)`).
- **Both keep rounding policy mutable**: Odoo's company-level
  `tax_calculation_rounding_method` (`round_per_line` / `round_globally`,
  default round-globally) plus a `display_rounding_warning` that literally
  warns "a rounding factor change might be dangerous"; mutable mid-history;
  ERPNext's precision is likewise a setting. Ours persists the policy per
  document because EN 16931, GST s9-90 and HMRC §17.5 mandate different
  arithmetic, and the arithmetic differs by real money (round 18's fixture).
- **Posted-entry mutability**: Odoo's `button_draft` resets posted moves to
  draft (guarded by lock-dates/flags); its e-invoice cancel comment says the
  guarantee for government-sent documents is by state transition. ERPNext
  regenerates GL entries on repost (`from_repost`). Ours: append-only,
  reversal-by-counter-entry, lineage table.
- **Auto-matching that decides**: Odoo's `account.reconcile.model` presets
  carry `auto_reconcile` triggers. Ours proposes and surfaces ambiguity.
- **Where the ERPs are genuinely ahead**: Odoo's `account.tax` trees with
  repartition lines are far more *general* than our per-jurisdiction
  vocabulary (arbitrary tax compositions vs deep specific regimes); Odoo's
  `account_edi` country formats and ERPNext's India IRP are working e-invoice
  transports; ERPNext's breadth (perpetual stock GL, assets, payroll) is
  enormous; both run millions of real filings. Breadth and battle, not
  correctness discipline.
- Akaunting: PHP `(float)` casts on balances in overview paths.

This audit updates the standing competitive claim: the estate's edge is not
"no floats" as a slogan but that every place a competitor documents *minimising*
representation error, the estate *excludes* the representation; every place a
competitor warns a setting "might be dangerous", the estate persists the policy
per document; every place a competitor auto-decides, the estate surfaces. Full
chat-delivered comparison of 2026-10-25/26; pull commits current as of today.


### Round 35, done

- **`ledger-pg 0.2.x`; the tamper-evident hash chain, studied from Odoo's
  `account.move` inalterability hash.** SHA-256 over the previous entry's
  hash plus a canonical serialization of the entry and every line; reversals
  join the chain; `verify_chain` walks in version order and reports the
  version, entry and reason of the first break. Odoo's design requires
  `float_repr` stabilization because its amounts are floats; our canonical
  form is deterministic by construction.
- **The round's process finding, and it is serious: 0.2.0 shipped a
  double-flipped reversal.** The chain work introduced flipped line tuples;
  the insert loop still bound a `match side` on top, so the stored
  counter-entry was identical to its original; the posting doubled, not
  reversed. The chain detected its own release defect on every verify, and
  the ledger-balance assertion caught the doubling. `cargo publish` verifies
  the library build only, so the broken integration paths never ran before
  the release. 0.2.0 yanked, 0.2.1/0.2.2 published with the fix, and the
  loop rule extended: **a release does not go out until the suite covering
  the change has run green**, even for "just plumbing".
- The estate suite pins the chain over the released artifact: clean walk,
  amount tamper detected at its version, memo tamper detected (the quiet
  alteration; amounts still add up), deletion detected, and reversal
  linkage covered.
- Five concurrent repos registered on sight. Estate at 246 repos, 207
  crates, 135 pins, 0 errors. 67 test groups green, clippy clean, fmt clean.
- Index-lag note: 0.2.1's upload raced the sparse index ("already uploaded"
  while absent), so 0.2.2 carries identical content; 0.2.0 yanked.


### Round 36, done

- **`invoice-kit 1.1.0`; VAT-inclusive pricing**, studied from Odoo's
  `price_include` tax handling. UK retail quotes prices with VAT in them;
  the derivation runs the arithmetic backwards; gross × rate / (1000+rate),
  rounded once through the exact integer path; and the net is computed as
  gross − vat, so the pieces always sum to the gross even when the tax
  rounds. Credit-note magnitudes split symmetrically; a rate of 100%+ is
  refused as degenerate, matching ap-kit's gate.
- **The vat-rules convergence cascade, and the version race it exposed.**
  invoice-kit 1.1.0 moved to vat-rules 0.1.1, which cascaded through ap-kit,
  fx-kit, vat-return, group-kit; and then hit a genuine hazard: **two
  agents published `vat-return 0.1.6` with divergent pins** (same version
  number, different contents). Resolved by a converged 0.1.7 carrying the
  full pin set: invoice-kit 1.1.0, ap-kit 0.1.5, vat-rules 0.1.1,
  double-entry 0.1.1. The lesson recorded: with exact pins and multiple
  agents, convergence releases must race-safe; publish the full converged
  set together, and the audit's drift check is the detector.
- Estate at 246 repos, 207 crates, 135 pins, 0 errors. 67 test groups green,
  clippy clean, fmt clean. The remaining ~58 drift entries are the
  concurrent wave's pins, owned by their publishers.


### Round 37, done

- **`sales-tax 0.1.0`; US sales tax, the last open front closed as a
  research-first crate.** The research framing is the product: US sales tax
  is structurally not VAT with different field names, and the types encode
  the five differences. Nexus gates collection (*South Dakota v. Wayfair*,
  2018; economic nexus is per-state and per-year, so the registry is an
  input; a hardcoded threshold table would be wrong the first month it
  shipped). Prices are pre-tax; no backwards division. Sales tax is never
  reclaimable, which is why `ap-kit`'s `Recoverability` has no US
  counterpart. Taxability is an input per line. And the rate is a
  jurisdiction stack remitted level by level.
- `JurisdictionRate::from_percent` via `fx-kit 0.1.4`'s new
  `Rate::parse_percent`: US rate data is quoted as percents, and parsing
  `"6.25"` as a multiplier makes every rate a hundred times too large.
- Per-document vs per-line rounding scope is explicit and pinned: two
  $0.10 lines at 5% are £0.02 per-line and £0.01 per-document. Nexus with an
  empty rate stack is refused rather than returned as zero; a missing data
  feed must not dress up as a legitimate no-tax sale, while a no-nexus
  destination is a *legal* zero and is reported as such.
- The estate suite posts the till through `double-entry`: collected tax
  accrues to sales-tax-payable (a liability; the mirror of VAT's input
  side) and clears on remittance. The fixture caught its own arithmetic:
  the till total forgot the untaxable line's net.
- Environment finding, recorded: the shared tmpfs filled (13GB of debris
  from a killed concurrent run), which surfaced as `cc` and fingerprint
  write failures masquerading as a toolchain fault. Cleared; runs stable.
- Estate at 247 repos, 208 crates, 136 pins, 0 errors. 68 test groups
  green, clippy clean, fmt clean.


### Round 38, done

- **`close_pack`; the quarter-end close, end to end, as one flow.** Every
  piece has its own focused suite; none proved the pieces form one close.
  This one does: the quarter's invoices and bills produce the VAT boxes per
  month, the camt bank import reconciles against the same postings to the
  penny, September's boxes file as the MTD body (£51.00 payable, finalised,
  digital), and the reverse-charge sale counts its net in box 6 while
  carrying no UK VAT; all from one set of integers, nothing retyped at any
  boundary.
- The fixture arithmetic was wrong twice on the way in (September's
  purchases, the camt closing balance) and **the crates refused both** -
  which is the suites doing their job.
- Estate at 247 repos, 208 crates, 136 pins, 0 errors. 70 test groups green,
  clippy clean, fmt clean.


### Round 39, done

- **Property tests across the arithmetic core and both parser boundaries** -
  the cheapest round on the board, and the one that protects the brand
  systematically rather than by worked example.
  - `fx-kit`: identity rate restates exactly; restatement is sign-symmetric
    (guaranteed only because the arithmetic rounds the magnitude and restores
    the sign; a signed-toward-zero rounding would break it at ties) and
    monotone at any positive rate; `parse_percent` is `parse` over exactly
    100; the parser boundary never panics on arbitrary strings.
  - `sales-tax`: taxes never negative under any tie mode; the per-line vs
    per-document scope difference is **bounded by half a unit per line per
    jurisdiction**; a larger drift would mean the scopes disagree about
    what is taxable, a real defect; no-nexus is always a legal zero; the
    rate parser never panics.
  - `invoice-kit`: `split_vat_inclusive` always accounts for the gross at
    every amount, rate and tie mode; the tax share is bounded by the rate;
    credit notes split symmetrically; `round_div` never panics, stays within
    one divisor step, never inverts a sign; exact rescaling is lossless up
    and refuses lossy down.
  - `statement-camt` / `statement-ofx`: arbitrary bytes and hostile tag soup
    produce `Ok` or shaped `Err`, never panics; a statement parser is fed
    the internet by definition, and a panic there is a denial of service in
    the reconciliation path.
- One test bug of my own caught by the properties (a registry/destination
  pair that trivially held nexus); fixed, which is the harness doing its
  job.
- Test-only changes: committed and pushed; no republish needed, since the
  released artifacts are byte-identical.
- Estate at 247 repos, 207 crates. 74+ property/test groups green, clippy
  clean, fmt clean.



### Round 39 addendum: the convergence cascade continues

- `statement-camt 0.1.3` and `statement-ofx 0.1.3` published against
  `recon-kit 0.2.0` (the reference-matching release; `LedgerSide` gains a
  `memo` field). The estate's recon-kit pin moved to =0.2.0 in the same
  wave. `group-kit 0.2.3` published against `fx-kit 0.1.4`
  (`Rate::parse_percent`).
- **`typed-id-new 0.1.0` was yanked between lock file updates**, making a
  fresh `Cargo.lock` impossible to generate. Restored from git HEAD (which
  has the yanked version resolved), so the builds work. The concurrent
  agent that owns `typed-id-new` needs to publish a non-yanked release.
- Round 39's property tests (fx-kit, sales-tax, invoice-kit, statement
  parsers) are test-only changes; committed and pushed, no republish
  needed, the released artifacts are byte-identical.


### Round 40, done

- **`release-gate.py`; the 0.2.0 yank lesson, codified as a script.** Five
  gates before a publish can run: the publish dry-run compiles, the crate's
  own all-features suite is green, clippy with `-D warnings` is clean, fmt
  is clean, and **every exact pin on an estate crate is the latest live
  version on crates.io**; the convergence check that would have caught both
  the vat-rules 0.1.1 cascade and the double-entry 0.1.1 cascade at publish
  time rather than at the next estate test run.
- Proven both ways against `sales-tax`: all gates green on the clean tree;
  then a deliberately stale `vat-rules =0.1.0` pin fires the pin-drift gate
  before a publish can split the graph across two versions.
- The sparse-index URL follows crates.io's resolvable-path rules (1/2/3/4+
  character buckets); the first draft's `v/a` prefix 404'd on every crate,
  which the smoke test caught before the gate was trusted.
- Estate at 247 repos, 208 crates, 136 pins, 0 errors. All suites green.


### Round 42: the EN 16931 category-specific rules audit (documentation, no code)

**Audited** the estate's invoice validation against EN 16931's
category-specific rules (BR-S through BR-Z). The general calculation rules
(BR-CO) are covered; documented as constants in `invoice-kit 1.1.1`'s
`br_co` module. The category-specific rules are where the gap lives:

- **Enforced**: BR-16 (at least one line), BR-27 (no negative price),
  the category/rate consistency gate (Standard/ReverseCharge > 0,
  ZeroRated/Exempt/NotSubject/IntraCommunity/FreeExport/CanaryIslands/
  CeutaMelilla = 0), and the duplicate line id check.
- **Not enforced**:
  - **BR-AE-02**: Reverse-charge supply requires the buyer's VAT identifier.
    The estate has `Invoice.buyer_vat_id` (added in 1.1.0 for the
    reverse-charge test) but `validate()` does not check it.
  - **BR-E-02 / BR-E-03**: Exempt supply requires a documented reason
    (statutory citation). The estate has `IssueReason` (ZATCA's five
    reasons) but does not cross-check it against the tax category.
  - **BR-IC-02**: Intra-community supply requires an actual delivery date.
    The estate has `supply_date` but does not enforce it for
    `TaxCategory::IntraCommunity`.
  - **BR-S-08/BR-Z-08**: The VAT breakdown's taxable amount must equal the
    sum of the line amounts in that category. The `tax_groups` method
    computes this, but does not cross-check it against the line-level sums.

**Decision**: document the gap rather than implement it, because the fix
requires a `invoice-kit 1.2.0` release that will cascade through
`vat-return`, `vat-mtd`, `pay-kit`, and `ledger-api`; a convergence wave
that needs a fresh session's context to manage properly. The gap is
recorded here so it cannot be forgotten.

### Standing rules for this loop

- Every crypto crate pins a primary-source vector **verbatim**, in the crate's
  own tests and in the estate-integration suite.
- Every finding in `estate-integration/README.md` carries: the crate, the
  version, what breaks, the spec citation, and the ask.
- A fix is not done until the version is **published**, the pin is **bumped**,
  the audit is **clean**, and the suite asserts the *repaired* behaviour.
- New crates are published into `estate.yml` in the same commit that publishes
  them, and the audit's coverage rule applies from birth.

### Explicitly not doing

- No UI. The product is API-first; the v1 client is a CLI and HTTP.
- No archiving of dormant repos. Honest status banners instead.
- No payroll, no inventory costing, no FX revaluation in v1.