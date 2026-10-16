# Research note 39 — merge queues & trunk-based discipline

**Sources.** GitHub Docs, *Managing a merge queue* (merge_group semantics,
FIFO, required checks against the grouped future state); GitHub community
#203246 (REST merge API bypasses "require merge queue" — a documented hole);
#154383 (merge queue incompatible with wildcard branch-protection patterns);
Mergify docs (batch vs in-place checks; "require up-to-date branches" fights
batch queues); rust-lang's bors/homu lineage (the original batch queue).

## What a merge queue actually buys

The failure mode it removes: PR A and PR B are both green in isolation; A
merges; B is now stale and its checks no longer describe reality. Classic
protection answers with "require up-to-date branches", which serializes merges
behind rebase-and-recheck churn. A merge queue replaces that with batched
validation of the *future* state of main: A+B are checked together as a
temporary `gh-readonly-queue/...` branch and land FIFO only if green.

## Estate-specific findings

1. **The CI trigger gap (fixed this loop).** Queued PRs are validated on
   `merge_group` events; none of the estate's workflows listened for them, so
   an enabled queue would wait forever for checks that never report. All
   loop-owned repos now trigger CI + security on `merge_group` (no-op until
   the queue is enabled — the arm-by-default principle).
2. **The estate's protections are bypassable by admin**, and this loop itself
   pushed straight to main using that bypass (recorded deviation: the
   no-stop loop mandate vs PR-review latency). "Require merge queue" +
   `enforce_admins` would close it — an owner decision, exactly like
   UPDATE_TOKEN. Documented, not hidden.
3. **Wildcards**: merge queues require exact-branch protection rules; the
   estate's rules target `main` exactly, so no conflict.
4. **REST hole**: `PUT /repos/{o}/{r}/pulls/{n}/merge` can land PRs outside
   the queue for actors without bypass grants (community #203246). Monitor;
   file with GitHub if observed.

## Enablement runbook (owner)

Settings → Branches → `main` protection: *Require merge queue* (merge method:
squash; grouping: default), keep `Require up-to-date` OFF (the queue replaces
it), and enforce for admins if the bypass escape hatch should close. The
`merge_group` triggers shipped this loop make the estate queue-ready.
