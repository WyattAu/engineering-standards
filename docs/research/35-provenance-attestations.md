# Research note 35 — provenance & attestations

**Sources.** SLSA build track (source → build → provenance non-falsifiability);
Sigstore/in-toto (the attestation formats GitHub artifact attestations emit);
PEP 740 (PyPI attestations, generated on upload by pypa's publish action);
npm provenance (registry-generated in-toto bound to workflow OIDC). Reference
repo: Google OSS Rebuild (rebuild-and-attest at fleet scale).

## State of the art, compressed

Provenance is only as strong as its binding: an attestation must be signed by
an identity the *verifier* can attribute to the build platform (OIDC), not
uploaded by hand. GitHub artifact attestations, npm `--provenance`, and PyPI
PEP 740 attestations all bind to the workflow's OIDC identity — that is the
non-falsifiable part, and it is free on hosted runners.

## Delta analysis — estate vs state of the art

| Template | Publisher | Before loop 35 | After |
|---|---|---|---|
| OmniPython | PyPI (trusted publishing) | attest-build-provenance on artifacts | unchanged (PEP 740 attestations also generated on upload) |
| OmniGo | goreleaser | attest-build-provenance | unchanged |
| OmniEmbedded | gh-release | attest-build-provenance | unchanged |
| OmniHaskell | gh-release | attest-build-provenance | unchanged |
| OmniRust | release-plz -> crates.io | **nothing, no id-token** | **id-token: write + attest of target/package/*.crate** |
| OmniTS | changesets -> npm | **claimed provenance, never passed the flag** | **bun publish --provenance explicit** |
| OmniInfra | none (Terraform modules, git-ref consumed) | N/A — documented | N/A |
| OmniDocs | none (Pages site) | N/A — documented | N/A |
| OmniDotfiles / OmniLean | none | N/A — documented | N/A |

## vs the reference repos

- Typical OSS: no attestations at all; provenance is the release manager's
  word. The estate now attests every distributable artifact class it produces.
- Google OSS Rebuild: rebuilds upstream artifacts on their own infrastructure
  and publishes the evidence at fleet scale — strictly stronger than
  attesting your own build. Filing cross-infrastructure rebuild as an
  owner-scale follow-up (same item as research note 34).
- SLSA framing: with OIDC-bound attestations on hosted runners, each publisher
  now meets the SLSA "non-falsifiable provenance" property for its artifacts.

## The claim-vs-reality finding

OmniTS's release workflow *said* "publishes with npm provenance" while its
publish script never passed `--provenance` and relied on an npm-specific env
variable that bun's publish may or may not honour. A comment is not a control.
Fixed by passing the flag where the tool reads it.
