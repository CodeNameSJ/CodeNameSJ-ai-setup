# GoHighLevel Workspace

Single source of truth for every agentic tool. Claude Code loads this via `CLAUDE.md`;
Codex reads it directly; Cursor reads it via `.cursor/rules/workspace.mdc`.
Do not duplicate these rules into tool-specific files — point at this one.

Independent repositories, not a monorepo. Voice AI is the primary active area.
Use the Node and package manager resolved by Volta in each repository.

## Repository Routing

| Scope             | Path                                                                      | Use for                                                 |
| ----------------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| Voice AI backend  | `ai-backend/apps/voice-ai/`                                               | Backend features; specs colocated at `src/**/*.spec.ts` |
| Voice AI API E2E  | `ai-backend/apps/voice-ai/test_automation/`                               | Playwright API automation                               |
| Voice AI frontend | `ai-frontend/apps/voice-ai/`                                              | New Voice AI frontend work                              |
| Voice AI UI E2E   | `ai-frontend/apps/voice-ai/test_automation/`                              | Playwright builder and CRM UI automation                |
| Voice AI host     | `spm-ts/`                                                                 | Shell and module-federation host                        |
| Legacy only       | `ghl-crm-frontend/apps/voice-ai/`                                         | Explicit legacy fixes and backports                     |
| Agent Builder     | `ai-frontend/apps/agent-builder/`                                         | Only when the task explicitly targets it                |
| Workflows         | `automation-workflows-{backend,frontend}/`                                | Workflow product                                        |
| RevEx             | `ghl-revex-{backend,frontend}/`                                           | RevEx product                                           |
| Marketplace       | `marketplace-frontend/`                                                   | Marketplace frontend                                    |
| Platform          | `platform-backend/`, `platform-jenkins-shared-library/`, `sdet-platform/` | Platform, CI, test tooling                              |

New Voice AI frontend work belongs in `ai-frontend/apps/voice-ai/`. Read
`ghl-crm-frontend/apps/voice-ai/` only to compare prior behavior. When a prompt names a
repository, stay in it unless a cross-repo dependency is established.

## Contract Map — where the real rules live

Rules live next to the code they govern. Read the contract for the scope you are touching
**before** editing it; do not preload them all.

| Editing                                   | Contract                                                   | Procedure                        |
| ----------------------------------------- | ---------------------------------------------------------- | -------------------------------- |
| `ai-frontend/apps/voice-ai/src`, `remote` | `apps/voice-ai/AGENTS.md` (source UI hooks)                | `apps/voice-ai/CLAUDE.md` router |
| Voice AI UI E2E                           | `apps/voice-ai/test_automation/AGENTS.md`                  | `apps/voice-ai/agent-skills/automate-ui/` |
| Voice AI UI triage                        | same                                                       | `apps/voice-ai/agent-skills/triage-ui/`   |
| Voice AI API E2E                          | `ai-backend/apps/voice-ai/test_automation/AGENTS.md`       | —                                |
| Legacy CRM UI E2E                         | `ghl-crm-frontend/apps/voice-ai/test_automation/AGENTS.md` | Backports only                   |

Each of those directories also carries `.cursor/rules/*.mdc` pointers and its own
`.cursor/mcp.json`, so Cursor and Codex resolve the same contract from inside the repo.

**Skills:** `automate-ui` (author UI E2E) and `triage-ui` (triage a failed run) are
committed once in `ai-frontend/apps/voice-ai/agent-skills/`. Workspace and Voice AI
application-level `.agents/skills/`, `.claude/skills/`, and `.cursor/skills/` entries
point to those same definitions so Codex, Claude Code, and Cursor discover identical
workflows from the workspace, Voice AI, or its test-automation directory. Use
`$automate-ui`/`$triage-ui` in Codex and
`/automate-ui`/`/triage-ui` in Claude Code or Cursor. Invoke the skill; do not
improvise a parallel procedure.

## Workspace Agent Harness

Reusable agent configuration is canonical under `.agent-harness/`, not under a
provider directory:

- `agents/` — shared agent instructions; Claude/Cursor consume Markdown and Codex gets
  generated TOML adapters
- `commands/` — shared workflows; Claude/Cursor expose `/name`, while Codex gets the
  same workflows as generated skills
- `skills/`, `references/`, `hooks/`, and `scripts/` — shared content and implementations
- `mcp/servers.json` — shared MCP inventory with provider-specific projections

After editing agents, commands, or MCP definitions, run:

```bash
python3 .agent-harness/sync.py
python3 .agent-harness/sync.py --check
```

Provider runtime settings, permissions, hook event manifests, caches, extensions, and
secrets remain provider-owned. Do not edit generated Codex adapters or generated command
skills directly. Full ownership rules are in `.agent-harness/README.md`.

A missing source hook is authored, not escalated — one primary hook plus the state
attributes a test must await, per
`ai-frontend/apps/voice-ai/test_automation/docs/selector-contract.md` §
"Source-change boundary".
Renaming an existing hook is a compatibility change needing the 6-place search first, and
carries a deploy dependency.

## Context Tooling

**Grep is the source of truth for "who calls this".** It is exact; the graph tools are not.

`graphify-out/<scope>/graph.json` is a useful _starting set_ — it holds real
`imports_from`, `calls`, `references`, and `indirect_call` edge records. The current
graphs were rebuilt on 2026-09-25 with Graphify 0.9.68, deterministic AST extraction,
and `directed: true`, so inbound traversal is the fast way to form a caller candidate
set. Extraction is still incomplete: measured 2026-09-09, the prior graph returned the
3 real production callers of `consent.validator.ts` correctly, but only 6 of 13 importers
for `redisKeys.helper.ts`. Confirm candidates and negative conclusions with Grep; never
conclude "nothing depends on this" from the graph alone.

`GRAPH_REPORT.md` in the same directory is orientation-level — community hubs, god nodes,
import cycles. Worth reading when entering an unfamiliar area; useless for lookups.

Regenerate all three code-only directed indexes without LLM tokens using
`~/.local/pipx/venvs/graphifyy/bin/python .agent-harness/refresh_graphs.py`. The script
backs up the existing graph/report/HTML together and records its roots and generation
time in each scope's `manifest.json`. Check that timestamp and current repository commits
before relying on a report.

`code-review-graph` was removed on 2026-09-09: its `get_impact_radius_tool` traversed
dependencies instead of dependents, missing every real caller while reporting
`risk: low`. Do not reinstall it without re-verifying that against Grep first.

## Setup, Commands, and Architecture

Command reference and the backend/Voice AI/frontend architecture map live in
`.agent-harness/references/setup-and-architecture.md` — read it when you need a
command or the system shape, not on every session.

## Conventions

- NestJS logging: `log.info/warn/error` with `[ClassName.methodName]` and a `payload`
  object. Never `console.log`.
- Vue: all user-visible strings via `t('key')` from `useI18n`. ESLint rules come from
  `@platform-ui`.
- Locales: `ai-frontend/apps/{app}/src/locales/en.json`; legacy CRM uses `en_US.json`.
- MongoDB migrations need `down()` and a `YYYYMMDDHHMMSS-kebab-case.ts` name.
- Feature specs live in `ai-specs/{feature-name}/`.
- `spm-ts` hosts AI micro-frontends; `agentBuilderApp` is the remote name for
  `ai-frontend/apps/agent-builder/` only.

## Graphify

Outputs live in `graphify-out/` at the workspace root, outside application repositories.
Run `/graphify` from the workspace root.

| Scope                       | Report                                           |
| --------------------------- | ------------------------------------------------ |
| Voice AI backend            | `graphify-out/voice-ai-backend/GRAPH_REPORT.md`  |
| Voice AI frontend           | `graphify-out/voice-ai-frontend/GRAPH_REPORT.md` |
| AI frontend / Agent Builder | `graphify-out/GRAPH_REPORT.md`                   |

`/graphify query "<question>"` reads `graphify-out/graph.json`.
