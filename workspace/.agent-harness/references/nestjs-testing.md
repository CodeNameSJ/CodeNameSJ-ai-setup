# Skill: NestJS Testing Patterns (VoiceAI)

Reference for test-writer, code-reviewer, and qa-bug-hunter. Read this instead of
re-deriving the mock architecture from individual test files.

## Two-layer mock architecture

**Layer 1 — Module mocks (structural, always-on)**
External packages that crash Jest if loaded for real. Go in `test/__mocks__/` and wired
via `moduleNameMapper` in `jest.config.ts`. Run automatically — no `jest.mock()` in spec.

Key mocks: `dotenv-safe`, `firebase-admin`, `firebase-admin/firestore`, `langfuse`,
`langfuse-langchain`, `express-http-context`, `openai_v4`, `pubsub`, `VoiceAgents`,
`VoiceCalls`, `feature-flags`, `outbound-helper`

**Layer 2 — Behavior mocks (test-controlled)**
Return values that drive each scenario. Set in `beforeEach` via `jest.spyOn()` on
Firestore helpers, and via constructor-injected validator mocks from `service.factory.ts`.

The spec file contains **only** Layer 2 setup + `describe`/`it` blocks.

## Test folder layout (voice-ai)

```
apps/voice-ai/
├── jest.config.ts                       ← isolatedModules, moduleNameMapper
└── test/
    ├── __mocks__/                        ← Layer 1 module mocks
    ├── fixtures/builders.ts              ← buildMessage(), buildPendingCallRecord(), etc.
    ├── helpers/
    │   ├── service.factory.ts            ← createOutboundService(validatorOverrides?)
    │   └── firestore.setup.ts            ← setupVoiceAiScheduledCallSpies(callRecord)
    └── outbound/outbound-validation.spec.ts
```

## Critical rules

- **No unit tests** — write orchestration routing tests or pipeline integration tests only
- **`afterEach(() => jest.restoreAllMocks())`** at the outermost describe — always
- **`jest.mock()` factory defaults** — use `.mockResolvedValue(null)` not bare `jest.fn()`
- **Top-level imports only** — never `require()` inside a test body (bypasses mock registry)
- **Compliance combinations** — always test `selfCertifiedConsentGiven=true` AND `optedOut=true` together

## Run command

```bash
NODE_OPTIONS=--max-old-space-size=4096 npx jest <test-file> --no-coverage --runInBand
```

## Common failure modes

- `jest.spyOn` + `jest.mock` factory conflict → use `.mockResolvedValueOnce()` directly, not spyOn
- Sequential calls to same method → chain `.mockResolvedValueOnce()` for each invocation
- Spy leak across describe blocks → missing `afterEach(() => jest.restoreAllMocks())`
- Module resolution failure → missing entry in `moduleNameMapper` in `jest.config.ts`
