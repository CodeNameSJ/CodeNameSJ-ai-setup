---
description: Author Playwright UI E2E tests for the Voice AI app. Describe the feature or change; the playbook handles flow, structure, case design, conventions, coverage registration, and verification.
---

Invoke the `automate-ui` skill (committed at `ai-frontend/apps/voice-ai/agent-skills/automate-ui/`) to author UI E2E coverage for $ARGUMENTS.

The skill resolves the suite by glob, then executes `ai-frontend/apps/voice-ai/agent-skills/automate-ui/references/authoring-playbook.md` end to end. That playbook is the only source of procedure — do not restate or improvise it here.

Describe the feature in plain language: `/automate-ui the new split prompt editor`

Scope is `ai-frontend/apps/voice-ai` UI automation only. Backend API automation lives in `ai-backend/apps/voice-ai/test_automation/` and is authored there directly, not through a workspace command. `ghl-crm-frontend/apps/voice-ai` is the retired pre-migration copy.

Related: `/playwright` runs and debugs existing tests; `/coverage` reviews a PR for coverage gaps.
