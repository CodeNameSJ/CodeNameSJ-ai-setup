# CLAUDE.md

The workspace contract is `AGENTS.md` — shared with Codex and Cursor. It is imported
below, so it is already in context: **do not re-read `AGENTS.md` or restate it.**

@AGENTS.md

---

Everything below is Claude Code specific.

## Harness Map

| Kind | Location | Notes |
|------|----------|-------|
| Canonical harness | `.agent-harness/` | Shared with Claude, Cursor, and Codex |
| Agents | `.claude/agents/` | Adapter symlink to `.agent-harness/agents/` |
| Commands | `.claude/commands/` | Adapter symlink; exposed as `/name` |
| References | `.claude/references/` | Adapter symlink; canonical paths are under `.agent-harness/` |
| Skills | `.claude/skills/` | Adapter symlink to shared workspace skills |
| Docs | `.claude/GUIDE.md`, `.claude/SETUP.md` | Adapter symlinks to harness docs |

Edit `.agent-harness/`, then run `python3 .agent-harness/sync.py`. Do not edit generated
Codex agents or generated command skills.

Pipeline: `/requirements → /prd → [/feature-brainstorm] → /plan → /code → tests → /review-changes → /qa`.
All outputs land in `ai-specs/<feature-name>/`. `/feature` runs the whole chain.
Natural language works too — commands are shortcuts with built-in hard gates.

## Working Rules

- Grep is the source of truth for "who calls this" / "what breaks". `graphify-out/*/graph.json`
  is a correct-direction but partial-recall starting set — confirm with Grep, and never
  read an empty result as "nothing depends on this". See AGENTS.md § Context Tooling.
- Never run `git commit` or `git push`. Staging and history are the user's call.
- Scope linting to the app you touched; never run a repo-wide linter for a
  `voice-ai`-scoped change.
- State the concrete failure mode before applying a fix. A reviewer or bot flag is not
  by itself a reason to change code.
- Push back with reasoning before implementing a questionable approach.

## Communication style

Caveman mode by default: drop articles, filler, pleasantries, hedging. Fragments fine.
Pattern: `[thing] [action] [reason]. [next step].` Not "Sure! I'd be happy to help with
that." — instead "Bug in auth middleware. Fix:".

Write normally inside code, commit messages, and security content.
User says "normal" or "stop caveman" to disable.
