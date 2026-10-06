Write or review a MongoDB migration for ai-backend.

Input: $ARGUMENTS  (e.g. "contacts add-voice-opt-in-field" or "review apps/contacts/migrations/20240101-foo.ts")

---

Use the migration-writer agent.

Pass the full input so the agent can determine:
- Target app (from app name or file path)
- Whether this is a **write** or **review** task

**Write task** — agent will:
1. Read the app's migrate-mongo config and 1–2 existing migrations
2. Write the full migration with `up()` and `down()`
3. Flag any HIGH RISK operations
4. Print run and rollback commands

**Review task** — agent will:
1. Read the migration file
2. Check reversibility, batch safety, index coverage, error handling
3. Verdict: SAFE / NEEDS CHANGES / HIGH RISK

**HARD GATE** — Do not write or approve a migration if:
- No `down()` method with meaningful logic
- Unbounded query on a large collection without batching

Surface these as blockers before proceeding.
