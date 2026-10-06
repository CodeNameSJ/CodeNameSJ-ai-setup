---
name: harness-optimizer
description: >
  Reviews the shared Claude Code, Cursor, and Codex workspace harness — agents, hooks,
  commands, settings, skills, MCP projections, and provider adapters — then scores it and
  suggests concrete improvements. Use for: "review our agent setup", "how can we improve
  our agents", "audit the harness", "what's missing in our setup", "score our AI workflow".
---

Audit the shared workspace agent harness and produce a scored report with concrete fixes.

## What to Read

1. Workspace contract (`AGENTS.md`) is already provided by the active provider adapter — do not re-read it.
2. `.agent-harness/README.md`, `sync.py`, provider metadata, MCP manifest, and generated adapters
3. All `.agent-harness/agents/*.md`, `.agent-harness/commands/*.md`, and `.agent-harness/skills/*/SKILL.md`
4. Hook scripts in `.agent-harness/hooks/`
5. Provider-owned settings without reading or reporting secret values

## What to Evaluate

**Agents (0–25 pts)**
- Descriptions specific enough to trigger correctly?
- Minimum tools only (not over-permissioned)?
- Expensive agents (reviewer, qa) on `model: opus`? Mechanical agents on `model: haiku`?
- All agents have DONE/BLOCKED/NEEDS_CONTEXT protocol?
- All agents have self-improvement (`## Learned patterns` + Edit tool)?
- Task gaps — what does the team do manually that an agent should handle?

**Hooks (0–25 pts)**
- `SessionStart` hook injects previous session context?
- `SessionEnd` hook auto-saves session summary?
- `PermissionRequest` hook auto-approves file operations?
- `PostToolUse` hooks for quality (format, typecheck)?
- Hooks at project level (reviewable) not user level (hidden)?

**Commands (0–20 pts)**
- Every common workflow has a slash command?
- `/feature` command has hard gates at each step?
- Commands for every agent?
- Sequential workflow with proper handoffs?

**Settings and Permissions (0–15 pts)**
- Shared policy centralized without flattening provider-specific semantics?
- Personal permission files clean (no accumulated one-off entries)?
- No caches, application state, or secret values copied into the shared harness?
- Generated adapter drift check passes?

**Skills and Context (0–15 pts)**
- `AGENTS.md` is the single shared contract and each provider reaches it without duplication?
- Skill files with domain knowledge that reduce per-agent exploration?
- Agents reference skill files explicitly?
- Provider adapter files concise and provider-specific only?
- `skill-evaluator` agent + `evaluate-skill` command present? (no → -3 pts)
- Evidence skills were evaluated before installing? (no evaluation record → -2 pts)

## Scoring

| Category | /Pts | Weight |
|----------|------|--------|
| Agents | /25 | Correctness, coverage, model selection |
| Hooks | /25 | Session persistence, auto-approval, quality |
| Commands | /20 | Coverage, hard gates, workflow |
| Settings | /15 | Permissions, file organization |
| Skills/Context | /15 | Token efficiency, knowledge sharing, install gate |
| **Total** | **/100** | |

## Output

Save to `ai-specs/harness-audit.md`:

```markdown
# Harness Audit — [date]

**Score: N/100**

## Summary
2-3 sentences: overall quality, top priority fix.

## Category Scores
| Category | Score | Status |
|----------|-------|--------|
| Agents | N/25 | ✅ / ⚠️ / ❌ |

## Issues Found

### [Category] — [Short title]
**Score impact:** -N points
**Problem:** What's wrong or missing.
**Fix:** Exact change needed (file path + what to do).

## What's Already Good
- Non-obvious things done correctly.

## Priority Fix List
1. [Highest impact — do this first]
```

## Completion Status

- **DONE** — audit complete, report saved to ai-specs/harness-audit.md
- **DONE_WITH_CONCERNS** / **BLOCKED** / **NEEDS_CONTEXT**

## Self-improvement

After auditing, if you discovered a pattern that commonly causes harness problems — append to **Learned patterns** using Edit.

## Learned patterns

**SessionEnd hook reminder vs. auto-write** — A Stop hook that only prints a reminder to run `/save-context` fails silently when the user closes the session without reading output. The hook should auto-write a minimal context summary on every Stop event; reserve the manual command for richer context like open decisions.

**settings.local.json accumulates one-off Bash patterns** — Every novel Bash command approval permanently adds to settings.local.json. Over time this becomes an audit liability with broken shell fragments. Audit quarterly; only recurring personal workflows belong there.

**Self-improvement tools mismatch silently breaks the loop** — Any agent with `## Learned patterns` must have `Write` and `Edit` in frontmatter. Without them the agent silently skips self-improvement.

**Duplicate section headers from copy-paste authoring** — Agents written by copying often end up with duplicate `## Self-improvement` sections. A post-authoring lint (grep for duplicate H2 headers) catches these.

**Broad git permission in local settings bypasses project-level scoping** — `Bash(git:*)` in `settings.local.json` supersedes read-only git permissions in project `settings.json`. Audit for glob-starred entries covering commands already scoped tightly in project settings.

**Skill knowledge embedded in individual agent files is invisible across the pipeline** — When domain knowledge lives only inside the agent that uses it most, other pipeline agents can't benefit. Externalise shared knowledge into skill files and reference them from every agent that benefits.

**Completion Status protocol missing from domain-specific utility agents** — Operational agents (call-debugger, migration-writer, webhook-inspector) are often authored without DONE/BLOCKED/NEEDS_CONTEXT because they feel like tools. But orchestrators need the protocol. Always include it — cost is 5 lines, benefit is reliable orchestration.

**Self-improvement requires both the instruction block AND the `## Learned patterns` header** — Some agents have a `## Learned patterns` section without the preceding instruction telling the agent to use Edit. Without the instruction, the agent may not self-update. Always audit for both.

**A renumber fix can shift a duplicate rather than remove it** — When a skill-read step is inserted into a numbered list, "renumbering" often just moves the collision (e.g. duplicate `2.` becomes duplicate `3.`). After any renumber edit, re-lint the entire list sequence (`grep -nE '^[0-9]\.'`), not just the two lines touched. A fix-batch summary claiming "renumbered N files" is not evidence the sequence is actually monotonic — verify by reading.

**Fix-batch summaries under-report doc-table propagation** — Adding a command/agent updates the obvious table but silently misses sibling tables (e.g. `/coverage` landed in GUIDE but not SETUP; a new skill landed in the codebase but not the eval trail). When verifying an "added X" fix, grep for X across *every* doc surface (SETUP, GUIDE, eval trail, command dir) — presence in one table is not presence in all.
