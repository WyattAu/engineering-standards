# Research note 41: agent-facing repo interfaces

**Sources.** agents.md (the open AGENTS.md standard, adopted by OpenAI Codex
CLI and others); Anthropic Claude Code (CLAUDE.md with `@path` imports;
native AGENTS.md support landing); Cursor (.cursor/rules); llms.txt
(llmstxt.org spec); the estate's own loops 1/25/40 (AGENTS.md + llms.txt +
the placeholder gate).

## The convention landscape, settled

| agent | file it reads | estate coverage |
|---|---|---|
| OpenAI Codex, Google Jules, many others | AGENTS.md (open standard) | ships since loop 1 |
| Claude Code (new) | AGENTS.md natively | automatic |
| Claude Code (older) | CLAUDE.md, supports `@path` imports | **added loop 41: CLAUDE.md = `@AGENTS.md`** |
| Cursor | .cursor/rules | filed, not forced (one more vendor file; revisit if the fleet adopts Cursor) |
| any LLM | llms.txt | ships since loop 1, gated since loop 25 |

## The principle the estate standardizes on

**One contract, many projections.** AGENTS.md is the single source of truth;
CLAUDE.md is a pointer (`@AGENTS.md`), never a fork; a fork would drift and
two agents would receive different contracts. The loop-25 llms gate already
enforces the same discipline for the llms.txt projection.

## Shipped (loop 41)

CLAUDE.md pointer added to all 11 loop-owned repos. Verification: the file is
a single import line, so there is nothing to drift.
