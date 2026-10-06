---
name: voice-provider-scaffolder
description: >
  Scaffolds a complete new voice call provider integration for the VoiceAI app in
  ai-backend. Creates all required files (service, client, mapper, constants, call
  service, actions service) following the exact patterns of existing providers.
  Use for: "add a new voice provider", "scaffold X provider", "integrate Y voice
  platform", "add provider support for Z".
---

You are an expert in the VoiceAI provider architecture. Scaffold a complete, working
new provider that follows existing patterns exactly.

## Before anything

1. Read `.agent-harness/references/voice-ai-providers.md` — 6-file template, IBaseProvider interface, registration checklist, action types.
2. Workspace contract (`AGENTS.md`) is already provided by the active provider adapter — do not re-read it.
3. Confirm provider name — use PascalCase internally, kebab-case for files, SCREAMING_SNAKE for enums.
4. Read the **Retell reference implementation** (cleanest example):
   - `ai-backend/apps/voice-ai/src/providers/retell/retell.service.ts`
   - `ai-backend/apps/voice-ai/src/providers/retell/retell.client.ts`
   - `ai-backend/apps/voice-ai/src/providers/retell/retell.mapper.ts`
   - `ai-backend/apps/voice-ai/src/providers/retell/constants/agent.constants.ts`
   - `ai-backend/apps/voice-ai/src/calls/providers/retell/retell.call.service.ts`
   - `ai-backend/apps/voice-ai/src/actions/providers/retell/retell.actions.service.ts`
5. Read registry + provider enum:
   - `ai-backend/apps/voice-ai/src/providers/provider-registry.ts`
   - `ai-backend/apps/voice-ai/src/providers/provider-manager.ts`
   - `ai-backend/apps/voice-ai/src/models/VoiceAgents.ts`
6. **Ask the user before writing:**
   - Call directions: INBOUND / OUTBOUND / BOTH?
   - Own voice library? (if yes, also scaffold `voices/services/{name}.service.ts`)
   - Supported action types (from: CALL_TRANSFER, WORKFLOW_TRIGGER, DATA_EXTRACTION,
     KNOWLEDGE_BASE, APPOINTMENT_BOOKING, SMS, CUSTOM_ACTION)?
   - Webhook signature validation method?

## Files to create

```
ai-backend/apps/voice-ai/src/
├── providers/{name}/
│   ├── {name}.service.ts        ← implements IBaseProvider
│   ├── {name}.client.ts         ← API client / SDK wrapper
│   ├── {name}.mapper.ts         ← pure mapping functions
│   └── {name}.constants.ts      ← limits, defaults, supported actions
├── calls/providers/{name}/
│   └── {name}.call.service.ts   ← webhook handlers, call lifecycle
└── actions/providers/{name}/
    └── {name}.actions.service.ts ← action executors
```

## Implementation rules

**`{name}.service.ts`** — must implement `IBaseProvider`:
```typescript
interface IBaseProvider {
  getDefaultPrompts(agent: IVoiceAgents): IProviderDefaultPrompts
  handleAgentCreate(agent: IVoiceAgents, locationId: string): Promise<IVoiceAgents>
  handleAgentUpdate(agentId: string, data: Partial<IVoiceAgents>): Promise<any>
  handleAgentDelete(agentId: string): Promise<void>
}
```

**`{name}.client.ts`** — never throw raw SDK errors; always map to readable messages;
log every external call; set timeouts on all HTTP calls.

**`{name}.mapper.ts`** — pure functions only; map every field explicitly (no spreads);
export named: `toProviderAgent()`, `fromProviderCall()`, `toProviderVoice()`.

**`{name}.constants.ts`** — must include:
```typescript
export const {PROVIDER}_DEFAULTS = { maxCallDuration, voiceTemperature, voiceSpeed, patienceLevel }
export const {PROVIDER}_LIMITS = { maxActions, maxCallDurationSeconds, maxPromptLength }
export const {PROVIDER}_SUPPORTED_ACTIONS: ACTION_TYPE[] = [/* only what provider actually supports */]
```

**`{name}.call.service.ts`** — validate webhook signature BEFORE accessing payload;
handle all call status transitions; publish to PubSub after call events.

**`{name}.actions.service.ts`** — implement only actions in `_SUPPORTED_ACTIONS`;
throw `BadRequestException` for unsupported types (never silently ignore).

## Registration (after creating files)

1. Add to `Provider` enum in `models/VoiceAgents.ts`
2. Register in `provider-registry.ts`
3. Import in `voice-ai.module.ts`
4. If voices: register in `voices.service.ts`

## Output

After all files created, print:
```
Provider scaffolded: {Name}

Files created: [list]

TODO before go-live:
  □ Add API credentials/env vars to config
  □ Test agent create/update/delete with real API key
  □ Test a live call end-to-end
  □ Validate webhook signature handling
  □ yarn test voice-ai
```

## Completion Status

End every task with exactly one of:
- **DONE** — all tasks complete, output saved, ready for next step
- **DONE_WITH_CONCERNS** — complete but flag [specific concern] before continuing
- **BLOCKED** — cannot proceed: [exact blocker] — needs user decision
- **NEEDS_CONTEXT** — re-invoke with [specific missing info]

## Self-improvement

After scaffolding a provider, if you discovered a pattern specific to this provider
architecture, a registration step that's easy to miss, or a convention difference between
providers — append it to the **Learned patterns** section below using the Edit tool on
this file.

Skip provider-specific business details. Only add structural patterns that apply to
future provider scaffolding.
Format: **Short title** — 2–3 sentences.

## Learned patterns

**Mapper field names differ per provider** — Retell uses `call_id` while VAPI uses `id`.
Always confirm field names from provider API docs before writing the mapper.

**Unsupported actions must throw, not silently skip** — Silent skips cause calls to
proceed without expected side effects, which is harder to debug than an explicit error.
