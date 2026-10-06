Use the `run-test` agent to run and debug Voice AI UI Playwright tests at the browser level.

Input: $ARGUMENTS — one of:
- A test description or scenario to automate (e.g. "navigate to agent list and verify VoiceAI agent appears")
- A test file path to run or debug (e.g. "src/AI Employee/VoiceAI/agent-create.spec.ts")
- A URL to inspect with the browser (e.g. "https://app.gohighlevel.com/v2/location/.../voice-ai")
- "run all" — run the full VoiceAI E2E suite

The agent will:
1. Workspace contract (`AGENTS.md`) is already provided by the active provider adapter — do not re-read it. Test structure lives in the suite contract.
2. Use MCP browser tools (browser_navigate, browser_screenshot, etc.) if available
3. Fall back to CLI (npx playwright test) if MCP is not available
4. For debugging: identify the exact failure point and suggest a fix
5. For new Voice AI tests: write them in ai-frontend/apps/voice-ai/test_automation following its AGENTS.md
