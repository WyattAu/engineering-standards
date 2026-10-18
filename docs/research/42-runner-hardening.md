# Research note 42 — runner hardening & cache poisoning

**Sources.** step-security/harden-runner (egress monitoring/blocking, the
standard GH runner hardening action); zizmor cache-poisoning audit (gated
High in this estate since loop 30); the estate's own loop 28 (OmniPython)
and loop 30 (OmniGo) cache fixes; the 2026-03 Reproducible Builds report
(bytecode-cache poisoning at PyPI scale — research note 34).

## The threat model

GitHub Actions caches (actions/cache, setup-go/setup-uv/setup-node default
caches) survive the run. A compromised workflow — or a PR that influences a
cached path — poisons the cache; every later run, including release runs,
consumes the poison. Tag-triggered release workflows are the crown jewels:
whatever they build gets published and attested.

## Estate survey (loop 42, verified per repo)

| release path | cache exposure | verdict |
|---|---|---|
| OmniPython (tags) | setup-uv with enable-cache: false (loop 28) | clean |
| OmniGo (tags) | setup-go with cache: false (loop 30) | clean |
| OmniHaskell (tags) | no cache steps in release.yml | clean |
| OmniEmbedded (tags) | no cache steps in release.yml | clean |
| OmniRust / OmniTS | registry-publish flows (crates.io / npm), no build cache | clean |

The release paths are already cache-clean. What the estate lacks is
**egress visibility**.

## Adopted policy (OMNI-CORE 11j)

1. Release workflows carry `harden-runner` (step-security) in **audit**
   egress mode as the first step — evidence collection before enforcement.
2. Release paths never enable caches (already true; now codified).
3. After an egress review window, audit flips to `block` per-workflow.

## Ready-to-apply (blocked on one mechanical step)

The insert is authored and verified for shape:

```yaml
      - name: Harden Runner
        uses: step-security/harden-runner@<40-hex SHA of v2.22.1> # v2.22.1
        with:
          egress-policy: audit
```

applied as the first step of the four tag-triggered release workflows
(Go, Haskell, Embedded, Python). Blocked only on resolving the tag's commit
SHA — the session's toolset cannot read git refs, and the estate's pin rule
(loop 24) forbids shipping a guessed SHA. First action of the next session
with shell access: `git ls-remote https://github.com/step-security/harden-runner v2.22.1`.
