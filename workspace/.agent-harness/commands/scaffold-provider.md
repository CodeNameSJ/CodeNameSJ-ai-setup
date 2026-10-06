Scaffold a complete new voice call provider integration for the VoiceAI app.

Provider name: $ARGUMENTS

---

Use the voice-provider-scaffolder agent.

The agent will:
1. Ask which capabilities the provider supports (call directions, voice library, action types, webhook signature method)
2. Read the Retell reference implementation to match patterns exactly
3. Create all required files (service, client, mapper, constants, call service, actions service)
4. Register in Provider enum and registry
5. Print a go-live checklist

**HARD GATE** — Do not proceed if:
- Provider name conflicts with an existing Provider enum value
- User hasn't confirmed which action types the provider supports

Action types affect generated constants and actions service — wrong values cause silent production failures.
