# ROADMAP — loop 2

Recreated 2026-10-05, after the research step in [LOOP.md](LOOP.md). Loop 1
hardened the *templates*. Loop 2 hardens the *library estate* and starts the
product that the estate exists to serve.

The premise of this loop: **a published crate is a claim, not a proof.** Every
crate in the manifest is published, versioned, documented, and green on CI, and
five of them were still wrong in ways that cost users money or lock them out.
This loop therefore treats *dogfooding across crate boundaries* — and *checking
implementations against primary sources rather than against themselves* — as the
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
| `webauthn-kit` | sign-count check "monotonic" | Accepted an equal counter — the signature of a replayed assertion. |
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
  that does not increase is *"a signal, but not proof"* — and explicitly
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

### Where the sources disagree — the most valuable findings

- `plain` PKCE: forbidden by OAuth 2.1 `-16` and FAPI 2.0, still permitted by
  RFC 7636. Our crate followed the oldest document.
- Rounding: ISO 80000-1 / ASTM E29 / OPC UA say half-even; ZATCA and the
  European Pharmacopoeia say half-up. "Swiss rounding" is not an ISO term.
- BIP-39's checksum catches ~255/256 of errors — the checksum is
  error-*detection*, not a security property, so 24 words is 2²⁵⁶ bits of
  entropy, never 264. The real attack surface is the entropy source (Milk Sad /
  CVE-2023-39910 drained 227k+ addresses).

## Loop 2 backlog

Ordered by (correctness impact × how often it bites).

### Now — security, primary-source-backed

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

### Now — money correctness

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
  that *hashes* its input — a silent, total signature failure for a wallet.
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

- **`invoice-kit 0.1.0` — the product's AR layer**, published with a consumer
  suite in the same loop. Three orthogonal document states because EN 16931
  defines no lifecycle at all; direction on the document type because Peppol's two
  credit conventions must never be mixed; a required `RoundingPolicy` because four
  jurisdictions mandate mutually incompatible arithmetic; integer-minor-unit
  allocation because three production incidents in a deployed accounting system
  were caused by float arithmetic on allocation.
- **Five bugs caught by its own tests before publication**, the worst being a
  division that inflated every quotient by a power of ten, and a line arithmetic
  that used `rescale_exact` where the specification requires a *rounding* — so
  any unit price that was not an exact multiple of its base quantity produced no
  amount at all.
- **Three money types now in the workspace** that disagree about what an amount
  is: a decimal value (`ledger-kit`), an integer count of minor units
  (`double-entry`), and an integer at an explicit scale (`invoice-kit`). The
  sharpest consequence is pinned: 1000 minor units is $10.00 and ¥1000 depending
  only on the exponent, and the two do not even render as the same string.

### Now — the product

The estate's library work has reached the point where the remaining defects are
in the *product* semantics, not the primitives. So the product starts now.

8. New repo, immutable double-entry core: append-only journals, balanced
   debits/credits enforced at post time, `draft → posted → void` states,
   **reversal by counter-entry** rather than deletion or mutation, period close,
   and audit trail. No standard defines draft/posted/void for journal entries —
   TigerBeetle is the closest implementable model and IFRS specifies only
   recognition/derecognition — so this is a documented decision, not a derived
   one.
9. Posting concurrency designed from PostgreSQL §13.2.3: the ledger must not
   rely on check-then-insert under SERIALIZABLE, because SSI can raise a unique
   violation that true serial execution never would.
10. New domain crates as the product grows: `invoice-kit` (AR), AP, tax,
    reconciliation, reports. Each gets an estate-integration suite from the day
    it is published — a crate with no suite is not finished.


### Round 18, done

- **`vat-rules 0.1.0` — the tax vocabulary both sides of a ledger share.**
  Extracted from invoice-kit rather than duplicated, because AP needs the same
  UNCL5305 categories, CEF `VATEX-*` reasons, UNTDID 1001 codes and rounding
  regimes. Zero dependencies by design: `TieMode` is policy vocabulary, not
  arithmetic machinery, so a table of tax codes does not depend on a
  double-entry engine to say "round ties away from zero".
- **`invoice-kit 0.2.0/0.2.1` — re-exports plus a real rounding fix.** The
  0.2.1 finding matters more than the extraction: **the three Australian
  rounding modes were one algorithm wearing three names.** `GstTotalInvoice`
  rounded per (category, rate) group, so it was `En16931Group` with a different
  label, but GST Act s9-90's total-invoice method adds *unrounded* GST per
  supply and rounds once — two lines of 5c at 10% and 5c at 30% are 3c per-group
  and 2c total-invoice. Real money. `GstTaxableSupply` rounded per group, not
  per supply. Under a single rounding the breakdown cannot be built from
  independently-rounded groups and still satisfy BR-S-08/S-09, so the residual
  is attributed to the largest unrounded group. `Decimal::round_div` also lost
  a cent on negative ties: the tie comparison runs on the magnitude now, because
  truncation toward zero makes "which neighbour is even" ill-defined for a
  negative quotient. Six new tests; three fail against the previous code.
- **`ap-kit 0.1.0/0.1.1` — accounts payable, where tax is a three-way split.**
  A purchase bill produces three outcomes, not two, because the gross payable
  always includes the full tax whether or not Article 168 lets the business
  claim it back: payable (gross), deductible tax (asset), non-deductible tax
  (expense). Two documented asymmetries: recoverability never changes what is
  owed to the supplier; and the supplier's line net is **authoritative data**,
  not a derivation — AP receives documents, it does not issue them. Rates above
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