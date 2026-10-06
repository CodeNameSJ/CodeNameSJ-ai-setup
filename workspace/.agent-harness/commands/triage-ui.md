---
description: Triage failing Voice AI UI E2E tests. Classifies each failure (environment, deployment skew, real defect), fixes at the right layer, re-runs, and reports what it could not fix.
---

Invoke the `triage-ui` skill (committed at `ai-frontend/apps/voice-ai/agent-skills/triage-ui/`) to triage $ARGUMENTS.

The skill resolves the suite by glob, then executes `ai-frontend/apps/voice-ai/agent-skills/triage-ui/references/triage-playbook.md` end to end. That playbook is the only source of procedure — do not restate or improvise it here.

Pass a report path, a spec name, or nothing to triage the last run: `/triage-ui specs/settings/voice-settings.spec.ts`

Scope is `ai-frontend/apps/voice-ai` UI automation only.

Related: `/automate-ui` authors new coverage; `/coverage` reviews a PR for coverage gaps; `/playwright` is the lower-level run/debug agent.
