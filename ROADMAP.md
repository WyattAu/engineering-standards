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