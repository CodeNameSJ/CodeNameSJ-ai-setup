---
name: mem-search
description: Search the shared claude-mem cross-session memory store. Use when asked whether prior work already solved something, how a past task was handled, or what happened in earlier Claude, Cursor, or Codex sessions.
---

# Shared Memory Search

Search the single local claude-mem store through its worker API. This skill is
provider-neutral: Claude, Cursor, and Codex use the same helper and data.

## Workflow

Always use the smallest useful retrieval sequence:

1. Search for a compact result index.
2. Use timeline around promising results when surrounding context matters.
3. Fetch full observations only for the IDs selected from the first two steps.

Do not fetch large batches before filtering. Do not start, stop, restart, upgrade, or
repair the worker as part of a search.

## Commands

The helper reads host and port from `~/.claude-mem/settings.json` and falls back to
`127.0.0.1:37777`.

```bash
python3 ~/.agents/skills/mem-search/scripts/mem_search.py health
python3 ~/.agents/skills/mem-search/scripts/mem_search.py search "selector contract" --limit 20
python3 ~/.agents/skills/mem-search/scripts/mem_search.py search "auth" --project Workspace --type observations --obs-type bugfix
python3 ~/.agents/skills/mem-search/scripts/mem_search.py timeline --anchor 6509 --before 3 --after 3
python3 ~/.agents/skills/mem-search/scripts/mem_search.py timeline --query "selector contract" --before 3 --after 3
python3 ~/.agents/skills/mem-search/scripts/mem_search.py get 6509 6453
```

Useful filters for `search` are `--project`, `--platform-source`, `--type`,
`--obs-type`, `--date-start`, `--date-end`, `--offset`, and `--order-by`.

If the helper reports that the worker is unavailable, report that plainly. Do not
restart a healthy or busy worker because its pending queue is in memory.

