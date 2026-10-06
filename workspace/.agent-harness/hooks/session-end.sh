#!/usr/bin/env zsh
# Runs on Stop event. Auto-writes session context when feature work is active.
# Cooldown: 15 minutes (short enough to catch back-to-back sessions).

SPECS_DIR="/Users/shubh/Workspace/ai-specs"
CONTEXT_FILE="/Users/shubh/Workspace/.claude/session-context.md"
AGENTS_DIR="/Users/shubh/Workspace/.claude/agents"

# Only act if ai-specs has feature folders with content
if [[ ! -d "$SPECS_DIR" ]] || ! find "$SPECS_DIR" -name "*.md" -maxdepth 2 | grep -q .; then
  exit 0
fi

# Cooldown — 15 min to catch back-to-back short sessions
if [[ -f "$CONTEXT_FILE" ]] && [[ -z "$(find "$CONTEXT_FILE" -mmin +15 2>/dev/null)" ]]; then
  exit 0
fi

DATE=$(date '+%Y-%m-%d %H:%M')

# Active feature folders (most recently modified first)
ACTIVE_FEATURES=$(find "$SPECS_DIR" -maxdepth 1 -mindepth 1 -type d | xargs ls -dt 2>/dev/null | head -3 | xargs -I{} basename {} | tr '\n' ', ' | sed 's/, $//')

# Pipeline position — infer from newest file type per feature.
# (N) is the null-glob qualifier: without it zsh raises "no matches found" before ls
# runs, so a 2>/dev/null on ls cannot suppress it.
has() { local matches=("$@"); (( ${#matches} )) }

PIPELINE_POS=""
for feature_dir in $(find "$SPECS_DIR" -maxdepth 1 -mindepth 1 -type d | xargs ls -dt 2>/dev/null | head -3); do
  feature=$(basename "$feature_dir")
  if has "$feature_dir"/qa-*.md(N); then
    PIPELINE_POS+="$feature: QA written → ready to ship or fix blockers\n"
  elif has "$feature_dir"/review-*.md(N); then
    PIPELINE_POS+="$feature: Review done → next: /qa $feature\n"
  elif has "$feature_dir"/plan-*.md(N); then
    PIPELINE_POS+="$feature: Plan written → next: /code $feature\n"
  elif has "$feature_dir"/prd-*.md(N); then
    PIPELINE_POS+="$feature: PRD written → next: /plan $feature\n"
  elif [[ -f "$feature_dir/requirements.md" ]]; then
    PIPELINE_POS+="$feature: Requirements written → next: /prd $feature\n"
  fi
done

# Open decisions — grep for blockers in recently modified ai-specs files
OPEN_DECISIONS=$(grep -r "→ needs decision\|BLOCKED\|open question" "$SPECS_DIR" \
  --include="*.md" -l 2>/dev/null | head -3 | sed "s|$SPECS_DIR/||" | tr '\n' ', ' | sed 's/, $//')

# Agents that learned something this session (modified in last 8 hours)
AGENTS_UPDATED=$(find "$AGENTS_DIR" -name "*.md" -mmin -480 2>/dev/null | xargs -I{} basename {} .md | tr '\n' ', ' | sed 's/, $//')

# Recent commits and uncommitted work across sub-repos. The workspace root is not a
# repo, so both have to be collected per repo.
RECENT_COMMITS=""
CHANGED_FILES=""
for repo in /Users/shubh/Workspace/ai-backend /Users/shubh/Workspace/ai-frontend \
            /Users/shubh/Workspace/ghl-crm-frontend /Users/shubh/Workspace/CodeNameSJ-ai-setup; do
  if [[ -d "$repo/.git" ]]; then
    commits=$(git -C "$repo" log --oneline -2 2>/dev/null)
    [[ -n "$commits" ]] && RECENT_COMMITS+="$(basename $repo): $commits\n"
    changed=$(git -C "$repo" status --porcelain 2>/dev/null | head -5 | sed 's|^|  |')
    [[ -n "$changed" ]] && CHANGED_FILES+="$(basename $repo):\n$changed\n"
  fi
done

cat > "$CONTEXT_FILE" <<EOF
# Session Context — auto-saved $DATE

## Active features
${ACTIVE_FEATURES:-none}

## Pipeline position
$(echo "$PIPELINE_POS" | sed '/^$/d')

## Open decisions / blockers
${OPEN_DECISIONS:-none found}

## Agents that updated learned patterns
${AGENTS_UPDATED:-none}

## Recent commits
$(echo "$RECENT_COMMITS" | sed '/^$/d')
## Changed files
$(echo "${CHANGED_FILES:-none}" | sed '/^$/d')

---
*Auto-saved. Run \`/save-context\` to add manual notes, next steps, and decisions.*
EOF

# Warn if patterns were updated — they should be backed up
if [[ -n "$AGENTS_UPDATED" ]]; then
  echo "⚠ Learned patterns updated: $AGENTS_UPDATED"
  echo "  Run /backup-harness to persist."
fi

echo "Session context saved → .claude/session-context.md"
