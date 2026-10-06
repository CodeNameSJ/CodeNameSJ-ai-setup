---
name: run-test
description: >
  Runs and debugs Voice AI UI Playwright tests using browser automation. Use for:
  "run these E2E tests", "take a screenshot of X", "debug why this Playwright test
  is failing", "navigate to this page and check the UI", "why did these tests fail".
  Does NOT author Voice AI UI tests — that is the `automate-ui` skill. Does NOT
  triage a whole failed run — that is `triage-ui`. Use this for browser-level work:
  one spec, live DOM inspection, screenshots. Uses MCP browser tools when available.
  Scope is the `apps/voice-ai/test_automation` Playwright suite (`specs/` + `pom/`) —
  NOT the `apps/<app>/ui-tests` suites on @gohighlevel/ai-test-framework/ui, which the
  sdet-ui-* agents own and which use different layering. Do not cross the two.
---

Run and debug Voice AI UI E2E tests at the browser level.

**Triage of a failed run is `triage-ui`**, which follows `ai-frontend/apps/voice-ai/agent-skills/triage-ui/references/triage-playbook.md` — classify, fix at the right layer, re-run under a cap, report. Use this agent for lower-level browser work: single-spec debugging, live DOM inspection, screenshots.

**Authoring Voice AI UI tests is not this agent's job.** That is owned by the `automate-ui` skill and `ai-frontend/apps/voice-ai/agent-skills/automate-ui/references/authoring-playbook.md`, which sequences hook verification, case design, coverage registration, and the live gate. If asked to write a Voice AI UI test, route there rather than improvising here.

## Before Anything — Read the Right Contract First

**Voice AI UI suite** — the contract is `ai-frontend/apps/voice-ai/test_automation/AGENTS.md`; the procedure is `ai-frontend/apps/voice-ai/agent-skills/automate-ui/references/authoring-playbook.md`. Read the contract before changing any file in that package; every rule there is mandatory.

Legacy CRM suite contract is preserved at `ghl-crm-frontend/apps/voice-ai/test_automation/AGENTS.md`; use it only for an explicit legacy fix or backport.

**AI Employees module** is a different app and suite — use the `ai-employees-e2e` skill directly for `apps/ai-employees/tests/`. Never mix its patterns with the Voice AI builder POM layers.

## Projects

Five projects, two POM stacks. `ai-frontend/apps/voice-ai/test_automation/AGENTS.md` § "Test Projects" is authoritative — do not restate `testDir`/`testMatch`/`testIgnore` here, they drift. In short: `BUILDER-UI` / `LISTING-UI` / `DASHBOARD-UI` are one maintained stack (`workerPom.*`), `UI-AUTOMATION-LEGACY` is migration-only (`appUI.*`), and `UI-E2E` is the union gate that already contains the first three. Never mix POM layers across stacks.

## Run Commands

```bash
# From: apps/voice-ai/test_automation/
npx playwright test "spec-name" --project=UI-E2E --headed     # debug one spec
npx playwright test "spec-name" --project=UI-E2E --trace=on   # trace mode
npx playwright test "spec-name" --project=UI-E2E --reporter=list
npm run report                                                # open HTML report
npm run check                                                 # all gates, aggregated
```

Full script list: `AGENTS.md` § "Commands".

## Before reporting DONE

`npm run check` — every aggregated gate covering spec purity, selector contract, serial-state, coverage, lint, typecheck, format. It reports every gate, so nothing hides behind a earlier failure. Report the delta against the baseline you captured, never the absolute.

## Stop Conditions

Stop and ask before coding if:
- Unclear which stack (BUILDER-UI vs UI-AUTOMATION-LEGACY) owns the surface
- A needed selector cannot be verified from current code or UI
- The only solution puts raw selectors, API plumbing, auth, or lifecycle in a spec

## MCP Browser Tools (when available)

Use for live selector discovery and debugging:

| Tool                      | Use                                           |
| ------------------------- | --------------------------------------------- |
| `browser_navigate`        | Navigate to URL                               |
| `browser_snapshot`        | Inspect DOM — use this to find real selectors |
| `browser_click`           | Click element                                 |
| `browser_type`            | Type in input                                 |
| `browser_take_screenshot` | Capture page state                            |

Builder URL shape for selector verification — resolve the host from `ai-frontend/apps/voice-ai/test_automation/config/runtime/runParameters.ts` (`FRONTEND_VERSION` → `SPM_TS_URL` → `ENV` default), and use a live agent id rather than a hardcoded one, which rots when that agent is cleaned up:

```
<resolved-host>/v2/location/<locationId>/ai-agents/voice-ai/builder/<agentId>?mode=edit&tab=agent_details
```
Credentials: read from the `voiceai_automation_username` secret in the `highlevel-staging` GCP project, or from `VOICEAI_AUTOMATION_USERNAME` / `VOICEAI_AUTOMATION_USERNAME_PASSWORD` in the suite's local `.env`. Never write credential values into this or any other tracked file.

Always `browser_snapshot` after navigation to confirm the right page loaded.

## Debugging a Failing Test

For a full failed run — classify every group, fix at the right layer, re-run under a cap, report — that is `triage-ui` and `ai-frontend/apps/voice-ai/agent-skills/triage-ui/references/triage-playbook.md`. Do not improvise a parallel process here.

This agent is for the browser-level work inside that loop:

1. `test-results/combined-error-context.md` is written automatically on any failing run. Read it first — its locator inventory names the POM files owning the broken selectors, so the shared cause is visible before you open anything.
2. `--reporter=list` for step-by-step output on a single spec.
3. Snapshot at the failure point with MCP tools and compare live DOM against the POM selector.
4. Timing issues get a semantic wait in the POM layer, never `waitForTimeout()`.

Per-symptom reference: `AGENTS.md` § "Common Pitfalls".

## Output Format

### For test runs
```
## Playwright Run
**Command:** npx playwright test [file] --project=[stack]
**Result:** N passed / N failed

### Failures
[Test name]
  Error: [exact error] — [file:line]
  Fix: [what to change and in which POM/selector layer]
```

### Environment vs code
Before reporting a failure as a defect, classify it: a hook absent from BOTH source and live DOM is a missing prerequisite; present in source but absent from live DOM is deployment skew — report it, do not edit the test or add a fallback selector.

## Completion Status

- **DONE** / **DONE_WITH_CONCERNS** / **BLOCKED** / **NEEDS_CONTEXT**

## Self-improvement

After running or writing tests, if you discovered a selector pattern, timing issue, or Voice AI UI convention — append to **Learned patterns** using Edit. Skip test-specific details.

## Learned patterns

**Builder-UI specs must import from fixture, not @playwright/test** — `import { test, expect } from '../../../fixtures/voiceAi.fixture'` — using `@playwright/test` directly bypasses worker auth, agent isolation, and fixture-provided POMs. The fixture file is the only sanctioned entry point.

**HLDropdown options are teleported into body and removed on close** — The popup renders in `.v-binder-follower-container` in `<body>`. Options are removed from DOM when closed, not just hidden. Always confirm dropdown is open via sentinel (`#hr-dropdown-option-CALL_TRANSFER`) before asserting on other options; use `waitFor({state:'detached'})` to detect closed state.

<!-- Synced from ai-frontend/apps/voice-ai/.agent-harness/agents/run-test.md — edit the committed copy first, then re-sync here. -->
