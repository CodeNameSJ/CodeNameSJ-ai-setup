# Skill: VoiceAI Providers

Shared reference for all VoiceAI provider-related agents. Read this instead of
re-discovering provider structure from the codebase.

## The 4 providers

| Provider | Enum value | Direction |
|----------|-----------|-----------|
| Synthflow | `SYNTHFLOW` | INBOUND + OUTBOUND |
| Retell | `RETELL` | INBOUND + OUTBOUND |
| VAPI | `VAPI` | INBOUND + OUTBOUND |
| Bolna | `BOLNA` | OUTBOUND only |

## 6-file template per provider

All paths relative to `ai-backend/apps/voice-ai/src/`:

```
providers/{name}/{name}.service.ts        — implements IBaseProvider
providers/{name}/{name}.client.ts         — API client / SDK wrapper (never throw raw SDK errors)
providers/{name}/{name}.mapper.ts         — pure mapping functions: toProviderAgent(), fromProviderCall(), toProviderVoice()
providers/{name}/{name}.constants.ts      — {PROVIDER}_DEFAULTS, {PROVIDER}_LIMITS, {PROVIDER}_SUPPORTED_ACTIONS
calls/providers/{name}/{name}.call.service.ts    — webhook handlers, call lifecycle, handleCallEnd()
actions/providers/{name}/{name}.actions.service.ts — action executors (throw BadRequestException for unsupported types)
```

## IBaseProvider interface

```typescript
interface IBaseProvider {
  getDefaultPrompts(agent: IVoiceAgents): IProviderDefaultPrompts
  handleAgentCreate(agent: IVoiceAgents, locationId: string): Promise<IVoiceAgents>
  handleAgentUpdate(agentId: string, data: Partial<IVoiceAgents>): Promise<any>
  handleAgentDelete(agentId: string): Promise<void>
}
```

## Registration checklist (after creating files)

1. Add to `Provider` enum in `models/VoiceAgents.ts`
2. Register in `providers/provider-registry.ts`
3. Import in `voice-ai.module.ts`
4. If own voices: register in `voices/services/voices.service.ts`

## Outbound validator chain (sequential — first failure stops)

| # | File | Key checks |
|---|------|-----------|
| 1 | `calls/outbound/validators/agent.validator.ts` | ACTIVE status, OUTBOUND direction |
| 2 | `calls/outbound/validators/contact.validator.ts` | has phone, not on DNC |
| 3 | `calls/outbound/validators/consent.validator.ts` | TCPA configured, consent present |
| 4 | `calls/outbound/validators/constraints.validator.ts` | working hours, frequency, concurrent limit |
| 5 | `calls/outbound/validators/location.validator.ts` | subscription includes VoiceAI, feature flag on |

Rejection reason stored in `callFailureReason` field on VoiceCall MongoDB document.

## Call status flow

`INITIATED → IN_PROGRESS → COMPLETED | FAILED | NO_ANSWER | BUSY | CANCELLED`

`handleCallEnd()` in `{provider}.call.service.ts` is the most common failure point for
missing transcripts, unfired actions, and undelivered PubSub events.

## Supported action types

`CALL_TRANSFER, WORKFLOW_TRIGGER, DATA_EXTRACTION, KNOWLEDGE_BASE, APPOINTMENT_BOOKING, SMS, CUSTOM_ACTION`

Not all providers support all types — check `{PROVIDER}_SUPPORTED_ACTIONS` in constants.

## Key gotchas

- Field names differ per provider: Retell uses `call_id`, VAPI uses `id` — always read the mapper
- Webhook signature must be validated BEFORE accessing any payload fields
- Unsupported actions must throw `BadRequestException` — never silently skip
