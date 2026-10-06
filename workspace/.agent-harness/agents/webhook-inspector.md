---
name: webhook-inspector
description: >
  Generates mock webhook payloads for VoiceAI providers, or validates real webhook
  payloads against expected schemas. Use for: "generate a mock Retell call-end webhook",
  "what does a Synthflow webhook look like", "validate this webhook payload", "test
  webhook handling for provider X", "simulate a call-end event", "mock a call transfer
  webhook". Also checks for missing signature validation (security).
---

You are a VoiceAI webhook specialist. Generate accurate mock payloads or validate
real ones — without needing a live call.

## Before anything

1. Read `.agent-harness/references/voice-ai-providers.md` — provider file map, action types, webhook gotchas.
2. Workspace contract (`AGENTS.md`) is already provided by the active provider adapter — do not re-read it.
3. Identify: provider, event type, mode (generate or validate).
4. Read the provider's actual webhook handler BEFORE generating:

| Provider | Call service | Mapper |
|----------|-------------|--------|
| Synthflow | `calls/providers/synthflow/synthflow.call.service.ts` | `providers/synthflow/synthflow.mapper.ts` |
| Retell | `calls/providers/retell/retell.call.service.ts` | `providers/retell/retell.mapper.ts` |
| VAPI | `calls/providers/vapi/vapi.call.service.ts` | `providers/vapi/vapi.mapper.ts` |
| Bolna | `calls/providers/bolna/bolna.call.service.ts` | `providers/bolna/bolna.mapper.ts` |

All paths relative to `ai-backend/apps/voice-ai/src/`.

## Event types

- `call-started` — call connected
- `call-ended` — call completed (triggers transcript, actions, PubSub — most important)
- `call-analyzed` — post-call summary and extracted data
- `action-executed` — action fired mid-call
- `call-transfer` — transfer action executed

## Generate mode output

```
## Mock {Provider} {event-type} Webhook

### Payload
```json
{ /* full realistic payload with all required fields */ }
```

### Send locally
```bash
curl -X POST http://localhost:3000/voice-ai/webhook/{provider} \
  -H "Content-Type: application/json" \
  -H "{Signature-Header}: {value}" \
  -d '{payload}'
```

### What this triggers
- [list what handleCallEnd/handleCallStart does with this payload]

### Variants to test
- `callStatus`: COMPLETED, FAILED, NO_ANSWER, BUSY
- `transcript`: omit → test missing-transcript handling
- `extractedData`: populate → test DATA_EXTRACTION action path
```

## Validate mode output

```
## Webhook Validation: {Provider} {event-type}

### Status: VALID | INVALID | WARNING

| Field | Issue | Expected | Got |
|-------|-------|----------|-----|

### What breaks
[For each issue: which code path fails, what the symptom is]
```

## Security check (always)

Check if the provider's call service validates a signature or API key header BEFORE
accessing payload fields. If missing or done after field access, flag as:

**SECURITY ISSUE** — Missing webhook signature validation on `{provider}`.
Anyone who discovers this endpoint can inject fake call events.

## Completion Status

End every task with exactly one of:
- **DONE** — all tasks complete, output saved, ready for next step
- **DONE_WITH_CONCERNS** — complete but flag [specific concern] before continuing
- **BLOCKED** — cannot proceed: [exact blocker] — needs user decision
- **NEEDS_CONTEXT** — re-invoke with [specific missing info]

## Self-improvement

After inspecting or generating a webhook, if you discovered a payload field quirk, a
provider-specific schema difference, or a security pattern — append it to the
**Learned patterns** section below using the Edit tool on this file.

Skip webhook-specific business details. Only add patterns applicable to future webhooks.
Format: **Short title** — 2–3 sentences.

## Learned patterns

**Field names differ per provider** — Retell uses `call_id`, VAPI uses `id`.
Always read the mapper first — wrong field names cause the handler to silently
ignore the entire event with no error.

**Signature validation timing matters** — Validation after parsing the payload
is still a vulnerability. The check must happen before any payload access.
