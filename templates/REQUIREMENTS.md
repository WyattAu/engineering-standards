# Requirements — <crate>

Numbered, testable requirements. Every requirement maps to at least one named
test; every security-relevant test cites at least one requirement. Doc
comments on the implementing public item carry `REQ-<CRATE>-NNN` tags.

## Functional

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-<CRATE>-001 | <Single testable statement: input → observable outcome> | MUST |

## Security

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-<CRATE>-100 | <e.g. Verification rejects malformed input with Err, never panics> | MUST |
| REQ-<CRATE>-101 | <e.g. Secret-dependent comparison is constant-time> | MUST |

## Robustness

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-<CRATE>-200 | <e.g. Concurrent calls sharing one handle maintain documented invariants> | MUST |

## Traceability Matrix

| Requirement | Test (fn, file) | Property class |
|-------------|-----------------|----------------|
| REQ-<CRATE>-001 | `<test_name>` (`tests/x.rs`) | unit |
| REQ-<CRATE>-100 | `<test_name>` | fuzz |
