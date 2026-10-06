Run all outbound call validation checks for an agent + contact before dialing.

Agent, contact, or description: $ARGUMENTS

---

Use the outbound-preflight agent.

Pass whatever you have — agentId, contactId, locationId, or a description.

The agent walks the full validator chain:
1. Agent — exists, ACTIVE, supports OUTBOUND
2. Contact — exists, has phone, not on DNC
3. Consent — TCPA configured and contact has it
4. Constraints — working hours, call frequency, concurrent limit
5. Location — subscription includes VoiceAI, feature flag on

Produces a PASS/FAIL table for every check with the exact fix for each failure.

Use before:
- Setting up outbound calling for a new location
- Diagnosing why an outbound campaign isn't connecting
- Verifying a new agent is ready for outbound
- Checking a specific contact before a manual call
