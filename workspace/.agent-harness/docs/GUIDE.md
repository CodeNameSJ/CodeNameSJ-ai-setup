# Workspace Agent Harness — User Guide

## The Mental Model

```
raw idea → requirements → PRD → [design] → plan → code → review → QA
```

Claude Code and Cursor expose each workflow as `/command`. Codex exposes the same
workflow as `$command` (or by matching natural language). `/feature`/`$feature` runs the
whole pipeline.
All output files land in `ai-specs/<feature-name>/`.

**You don't have to use commands** — natural language works too. Commands are
shortcuts with built-in hard gates. Both routes invoke the same agents.

---

## General Commands

| Command | Input | What it does |
|---------|-------|-------------|
| `/requirements <notes>` | Raw brain dump | Structures messy input into `requirements.md` |
| `/prd [name]` | Feature name | Product spec from requirements + codebase exploration |
| `/feature-brainstorm [name]` | Feature name | Design session: 2-3 approaches, approved before planning |
| `/plan [name]` | Feature name | File-by-file implementation plan |
| `/code [name]` | Feature name | Implements the plan (requires plan to exist) |
| `/review-changes [name/file]` | Name or file | Structured code review with verdict |
| `/qa [name]` | Feature name | P0/P1/P2 bug hunt, ship verdict |
| `/test <file>` | File or feature | Writes real regression tests *(inactive)* |
| `/debug <error>` | Error/trace/description | Root cause + fix for code errors |
| `/feature-docs <system>` | System name | Comprehensive developer documentation |
| `/i18n` | *(reads git diff)* | Syncs all locale files after en_US.json change |
| `/impact <change>` | What you're changing | Cross-repo impact analysis before touching shared APIs |
| `/migrate <app> <desc>` | App + description | Write/review MongoDB migrations |
| `/feature <description>` | Raw idea or name | Full pipeline, automated |
| `/harness [focus]` | Optional focus | Audit and score the workspace agent harness |
| `/playwright <test/url>` | Test file, URL, or description | Run/debug/generate Playwright E2E tests with browser automation |
| `/save-context` | *(none)* | Save session state for next session |

## VoiceAI Commands

| Command | What it does |
|---------|-------------|
| `/scaffold-provider <name>` | Scaffold all 7 files for a new voice call provider |
| `/debug-call <id or symptom>` | Trace a specific call through the system |
| `/test-webhook <provider> <event>` | Generate/validate provider webhook payloads |
| `/preflight <agent> <contact>` | Simulate all 5 outbound validators before dialing |
| `/coverage <PR#>` | Review PR for E2E automation coverage gaps (add `--legacy` for ghl-crm-frontend PRs) |

---

## Pipeline Reference

### `/requirements <raw notes>`
Takes unstructured input (voice-to-text, bullet dump, notes). Does NOT read codebase.
**Output:** `ai-specs/<name>/requirements.md`

### `/prd [name]`
Reads requirements, explores codebase, writes business-focused spec. No code, no file paths.
**Output:** `ai-specs/<name>/prd-{topic}.md`

### `/feature-brainstorm [name]`
For complex features: new data models, multi-repo, async flows, security implications.
Proposes 2-3 approaches. **HARD GATE** — won't proceed to plan without your approval.
**Output:** `ai-specs/<name>/design-{topic}.md`

### `/plan [name]`
Reads PRD + codebase, writes file-by-file task list. Required before `/code`.
**Output:** `ai-specs/<name>/plan-{topic}.md`

### `/code [name]`
Implements the plan. **HARD GATE** — stops if no plan exists. Runs tests before claiming done.
**Output:** Production code changes

### `/review-changes [name]`
Runs `git diff main`, reads every changed file. Verdict: Approve / Approve with suggestions / Request changes.
**Output:** `ai-specs/<name>/review-{topic}.md`

### `/qa [name]`
5 angles: happy path, failure paths, edge cases, race conditions, security/multi-tenant.
Verdict: SHIP / SHIP WITH MITIGATIONS / DO NOT SHIP.
**Output:** `ai-specs/<name>/qa-{topic}.md`

### `/migrate <app> <description>`
Write: scaffolds full migration with `up()` + `down()`, batching for large collections, index creation.
Review: checks reversibility, unbounded queries, missing indexes.
```
/migrate contacts add-voice-opt-in-field
/migrate review apps/contacts/migrations/20240101-add-field.ts
```

### `/impact <change>`
Searches ai-backend, ai-frontend, ghl-crm-frontend legacy, ghl-revex-frontend for every caller.
Run this before renaming endpoints, changing shared interfaces, or modifying enums.

### `/playwright <test/url/description>`
Runs, debugs, or generates Playwright E2E tests. Uses MCP browser tools when available
(headless Chromium with `browser_navigate`, `browser_click`, `browser_screenshot`, etc.).
Falls back to CLI (`npx playwright test`) when MCP is not configured.

```
/playwright run src/AI Employee/VoiceAI/agent-create.spec.ts
/playwright debug "why is the agent form test failing"
/playwright "write a test that creates an agent and verifies it appears in the list"
/playwright run all
```

### `/save-context`
Writes `.claude/session-context.md` — active feature, files changed, open decisions, next step.
Next session starts warm via the SessionStart hook.

---

## VoiceAI Command Details

### `/scaffold-provider <name>`
Creates all 7 provider files following the Retell reference pattern, registers in enum + registry.
Ask before running: which call directions and action types does the provider support?

### `/debug-call <id or symptom>`
For "a live call behaved wrong" — different from `/debug` (which handles code errors).
Symptom → layer: transcript missing → `handleCallEnd()`; action didn't fire → `actions.service.ts`;
call never started → outbound validators; workflow not triggered → PubSub publishing.

### `/test-webhook <provider> <event>`
```
/test-webhook retell call-ended           # generate mock + curl command
/test-webhook validate retell <payload>   # validate a real payload
```
Also checks for missing signature validation (security issue).

### `/preflight <agent> <contact>`
Runs all 5 outbound validators without dialing. Most common blocker: consent.

---

## Session Persistence

`.claude/session-context.md` is injected at every session start (SessionStart hook).
Run `/save-context` at the end of any session with active work.

---

## MCP Integrations

Configured canonically in `.agent-harness/mcp/servers.json` and projected into native
provider files. Claude agent tool restrictions live in
`.agent-harness/provider-agent-metadata.json`; Cursor and Codex use provider-native
availability rules.

### Graph tooling — removed

`code-review-graph` was uninstalled after measurement: its
`get_impact_radius_tool` returned each file's own imports instead of its dependents,
missing all 6 real callers of `consent.validator.ts` and reporting `0 files affected` for
a helper with 13 importers — while labelling both `risk: low`. Graphs, registry entries,
and the stale pipx installation were removed.

**To retest a future CRG release:** install it temporarily, pick a file, get ground truth with
`grep -rn "<basename>" apps --include="*.ts"`, then compare against
`get_impact_radius_tool`. If the returned files are ones the target *imports*, the
direction bug is still present.

Use Grep for caller questions. `graphify-out/<scope>/graph.json` provides useful
`source`/`target` edge records, but the current graphs are serialized with
`directed: false`; do not treat traversal direction as authoritative until they are
regenerated with `--directed`. Recall is also partial, so confirm with Grep before acting.

### Playwright MCP (`@playwright/mcp`)
Headless Chromium for `/playwright`, granted to `run-test`: `browser_navigate`,
`browser_snapshot`, `browser_click`, `browser_type`, `browser_fill_form`,
`browser_wait_for`, `browser_take_screenshot`, `browser_console_messages`,
`browser_network_requests`, `browser_evaluate`. For a visible browser, drop
`"--headless"` from the args in `.mcp.json`.

Use `browser_snapshot` (accessibility tree) over screenshots for selector discovery —
it is far cheaper and gives you the actual hooks.

---

## Agent Model Assignments

| Model | Agents |
|-------|--------|
| `claude-opus-5` | code-reviewer, qa-bug-hunter, brainstorm, documentation-writer, api-impact, harness-optimizer |
| `claude-sonnet-5` (default) | code-writer, implementation-planner, debug, migration-writer, voice-provider-scaffolder, call-debugger, webhook-inspector, run-test, review-coverage |
| `claude-haiku-4-5-20251001` | requirement-writer, i18n-writer |

Opus = adversarial reasoning (review, QA, impact). Sonnet = coding and planning.
Haiku = deterministic formatting tasks.

---

## Active vs Inactive

Anything under `.claude/inactive/` is dormant: Claude Code never scans it, so it costs no
context and cannot be auto-selected — but it is one command away, not deleted.

```bash
zsh .agent-harness/scripts/toggle.sh                  # list active + inactive
zsh .agent-harness/scripts/toggle.sh off <name>       # make dormant
zsh .agent-harness/scripts/toggle.sh on  <name>       # bring back
```

Currently dormant: `test-writer` / `/test`, `skill-evaluator` / `/evaluate-skill`.
An agent and its command are separate files under the same name — toggling hits both.
Start a new session for a change to register.

## Do's and Don'ts

**Do:**
- Run `/impact` before touching any shared interface, endpoint, or enum
- Run `/feature-brainstorm` before `/plan` on complex features (new models, multi-repo, async flows)
- Run `/save-context` when switching tasks or ending a long session
- Pass the feature name when multiple features are in `ai-specs/`
- Run `/backup-harness` periodically — learned patterns in `.agent-harness/agents/` are lost if the harness is deleted, and nothing else backs it up

**Don't:**
- Run `/code` without a plan (hard gate will stop you anyway)
- Use `/feature` for bug fixes or one-liners — it's for new features
- Ignore HARD GATEs — answer the question before continuing
- Run `git add` or `git commit` without confirming — these are no longer auto-approved
