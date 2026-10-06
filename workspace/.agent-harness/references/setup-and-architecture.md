# Setup commands and system architecture

Reference material, pulled on demand. `AGENTS.md` keeps only the routing and contract
rules that shape decisions; this is what you look up once you know where you are going.

## Setup and Commands

```bash
yarn ar-login   # before installing private Yarn packages

# Backend. Run from: ai-backend/
yarn && yarn start:dev voice-ai
yarn test apps/voice-ai
yarn lint && yarn format
yarn migrate:create voice-ai {name}
yarn migrate voice-ai          # also: migrate:status, migrate:undo-last

# Backend API E2E. Run from: ai-backend/apps/voice-ai/test_automation/
npm install && npm run test
npm run test:agent-flows
npm run check

# Frontend. Run from: ai-frontend/
yarn install
yarn workspace ghl-voice-ai-app dev     # also: build
yarn lint && yarn format

# Frontend UI E2E. Run from: ai-frontend/apps/voice-ai/test_automation/
npm install && npx playwright install chromium
npm run test                    # also: test:critical (fast P0 gate), test:builder-ui
npm run check                   # every aggregated gate — required before claiming done
```

`npm run check` reports every gate (coverage, contract, selectors, serial-state,
mock-claims, spec placement, test depth, critical gate, lint, typecheck, redaction,
format), so no red gate hides another.

## Architecture

**Backend (`ai-backend`)** — each `apps/` app deploys independently to Kubernetes; shared
code in `libs/`. MongoDB (Mongoose v5) primary, plus Redis, Elasticsearch, DuckDB,
Parquet. Queues: Google Cloud PubSub + Bull MQ. AI: OpenAI, Google GenAI, Anthropic,
LangChain.

**Voice AI (`ai-backend/apps/voice-ai`)**

- Provider pattern: Synthflow, Retell, VAPI, Bolna — each in `providers/{name}/`
  (service, client, mapper, constants); lifecycle in `calls/providers/{name}/`; actions
  in `actions/providers/{name}/`.
- Voice sources: ElevenLabs, Retell Voices, Cartesia, SynthFlow in `voices/services/`.
- Outbound validator chain, sequential, first failure stops:
  `agent` → `contact` → `consent` → `constraints` → `location`
  (`src/calls/outbound/validators/`).
- Call states: `INITIATED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `NO_ANSWER`, `BUSY`,
  `CANCELLED`.
- Models: `VoiceAgents`, `VoiceCalls`, `VoiceAIAgentActions`, `VoiceAIUserVoices`.
- External: Twilio (routing), OpenAI Realtime (transcription), PubSub (events).
- Analytics: ClickHouse via `dashboard.service.ts`.

**Frontend** — `ai-frontend` apps are the primary AI micro-frontend remotes;
`ghl-crm-frontend` is legacy for old CRM remotes and backports.
