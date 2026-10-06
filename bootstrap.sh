#!/usr/bin/env bash
# Link this config repo into a workspace. Idempotent: existing correct symlinks are left
# alone, real files are never overwritten — they are reported so you can move them aside.
#
#   ./bootstrap.sh            # link, then report what still needs doing
#   ./bootstrap.sh --dry-run  # show what would change
#
# Run it from inside the clone. The workspace is the clone's parent directory.

set -uo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

REPO=$(cd "$(dirname "$0")" && pwd)
WORKSPACE=$(dirname "$REPO")
REPO_NAME=$(basename "$REPO")
rc=0

link() {
  local target=$1 path=$2
  if [[ -L "$path" ]]; then
    if [[ "$(readlink "$path")" == "$target" ]]; then
      echo "ok       $path"
      return
    fi
    echo "RELINK   $path (was -> $(readlink "$path"))"
  elif [[ -e "$path" ]]; then
    echo "SKIP     $path exists and is not a symlink — move it aside first"
    rc=1
    return
  else
    echo "LINK     $path -> $target"
  fi
  (( DRY_RUN )) && return
  [[ -L "$path" ]] && unlink "$path"
  ln -s "$target" "$path" || rc=1
}

link "$REPO_NAME/workspace/AGENTS.md"      "$WORKSPACE/AGENTS.md"
link "$REPO_NAME/workspace/CLAUDE.md"      "$WORKSPACE/CLAUDE.md"
link "$REPO_NAME/workspace/.agent-harness" "$WORKSPACE/.agent-harness"
link "$REPO/user/.agent-harness" "$HOME/.agent-harness"
link "$REPO/user/.agents"        "$HOME/.agents"

for provider_skills in "$HOME/.claude/skills" "$HOME/.cursor/skills"; do
  (( DRY_RUN )) || mkdir -p "$(dirname "$provider_skills")"
  link "../.agents/skills" "$provider_skills"
done

echo
if [[ ! -d "$WORKSPACE/ai-frontend" ]]; then
  echo "TODO     clone ai-frontend as a sibling — .agent-harness/skills/ links into"
  echo "         ai-frontend/apps/voice-ai/agent-skills/ and is dead until it exists"
  rc=1
fi

if [[ ! -f "$REPO/workspace/.agent-harness/mcp/servers.json" ]]; then
  echo "TODO     recreate workspace/.agent-harness/mcp/servers.json from your secret"
  echo "         store (excluded from git — it carries credentials). Servers expected:"
  echo "         claude-mem, computer-use, jenkins, node_repl, playwright"
  rc=1
fi

echo "NEXT     cd $WORKSPACE && python3 .agent-harness/sync.py"
echo "         then python3 .agent-harness/sync.py --check  (reports any dead symlink)"
echo "         then python3 ~/.agent-harness/audit.py"
echo "         then restart Claude Code, Cursor, and Codex"

exit $rc
