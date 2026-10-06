Generate a mock webhook payload for a VoiceAI provider, or validate a real one.

Provider, event type, and mode: $ARGUMENTS

---

Use the webhook-inspector agent.

Examples:
- `retell call-ended`               → generate mock Retell call-end payload + curl command
- `synthflow call-started`          → generate mock Synthflow start event
- `vapi call-ended`                 → generate VAPI call-end payload
- `validate retell <paste payload>` → validate a real Retell webhook payload
- `retell call-transfer`            → generate mock transfer event

Generate mode: reads the actual handler → exact field names → realistic payload → curl command → lists what the handler does → checks signature validation.

Validate mode: compares payload against handler expectations → flags missing fields, wrong types, broken code paths.
