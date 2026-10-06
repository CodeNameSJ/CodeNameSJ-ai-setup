#!/usr/bin/env zsh
# Drift check for agents that exist twice: committed in the repo (repo-relative paths,
# used when working inside ai-frontend) and mirrored into the provider-neutral workspace
# harness (used when working from the workspace root).
#
# They are meant to differ ONLY by:
#   - the `ai-frontend/apps/voice-ai/` path prefix
#   - the `tools:` frontmatter line (workspace copy grants MCP tools)
#   - workspace-only sections marked with the sync footer
#
# Anything else is real drift. Edit the committed copy first, then mirror.
#
# Usage: zsh .claude/scripts/check-agent-sync.sh

set -uo pipefail
WS="/Users/shubh/Workspace"
SRC="$WS/ai-frontend/apps/voice-ai/.claude/agents"
DST="$WS/.agent-harness/agents"
AGENTS=(run-test review-coverage)

normalize() {
  # strip the path prefix, the tools line, and blank/comment noise
  sed -e 's|ai-frontend/apps/voice-ai/||g' \
      -e '/^tools:/d' \
      -e '/^model:/d' \
      -e '/^<!-- Synced from/d' \
      -e '/^[[:space:]]*$/d' "$1"
}

rc=0
for a in $AGENTS; do
  if [[ ! -f "$SRC/$a.md" || ! -f "$DST/$a.md" ]]; then
    print -r -- "SKIP    $a (missing one side)"
    continue
  fi
  # lines present in the committed copy but absent from the workspace copy = real drift
  missing=$(comm -23 <(normalize "$SRC/$a.md" | sort -u) <(normalize "$DST/$a.md" | sort -u))
  if [[ -n "$missing" ]]; then
    print -r -- "DRIFT   $a — committed lines missing from the workspace copy:"
    print -r -- "$missing" | sed 's/^/          /'
    rc=1
  else
    print -r -- "OK      $a"
  fi
done

exit $rc
