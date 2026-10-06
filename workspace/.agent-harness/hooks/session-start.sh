#!/usr/bin/env zsh
# Injects previous session context into the conversation at session start.
# Claude sees this output before the first user message.

WS="/Users/shubh/Workspace"
CONTEXT_FILE="$WS/.claude/session-context.md"
if [ -f "$CONTEXT_FILE" ]; then
  echo "=== Previous Session Context ==="
  cat "$CONTEXT_FILE"
  echo "================================"
fi

# Graph staleness. AGENTS.md tells agents to check manifest freshness before
# trusting a graph, but nothing surfaced it — so the check never happened.
python3 - "$WS" <<'PYEOF' 2>/dev/null
import json, os, subprocess, sys
from datetime import datetime, timezone

ws = sys.argv[1]
stale = []
for scope, repo in (("", None), ("voice-ai-backend", "ai-backend"), ("voice-ai-frontend", "ai-frontend")):
    path = os.path.join(ws, "graphify-out", scope, "manifest.json")
    if not os.path.exists(path):
        continue
    try:
        built = datetime.fromisoformat(json.load(open(path))["generated_at"])
    except Exception:
        continue
    days = (datetime.now(timezone.utc) - built).days
    behind = 0
    if repo:
        try:
            out = subprocess.run(
                ["git", "-C", os.path.join(ws, repo), "log", "--oneline", f"--since={built.isoformat()}"],
                capture_output=True, text=True, timeout=5)
            behind = len([l for l in out.stdout.splitlines() if l.strip()])
        except Exception:
            pass
    if days >= 7 or behind:
        label = scope or "agent-builder"
        stale.append(f"{label} ({days}d old" + (f", {behind} commits since" if behind else "") + ")")

if stale:
    print("⚠ graphify indexes may be stale: " + "; ".join(stale))
    print("  refresh: ~/.local/pipx/venvs/graphifyy/bin/python .agent-harness/refresh_graphs.py")
PYEOF
