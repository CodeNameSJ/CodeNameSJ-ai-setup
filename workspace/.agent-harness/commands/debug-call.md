Debug a specific VoiceAI call — trace it through the full system to find the failure point.

Call ID, agent ID, or symptom: $ARGUMENTS

---

Use the call-debugger agent.

Accepts:
- A callId or telephonyProviderCallId
- An agentId + timeframe ("agent abc123 around 2pm yesterday")
- A symptom description ("call completed but transcript is missing")
- Any combination

The agent maps your symptom to the right failure layer, traces the code path,
and gives a concrete fix with verification step.

This is for **a specific call's wrong behavior** — for general code errors, use `/debug`.
