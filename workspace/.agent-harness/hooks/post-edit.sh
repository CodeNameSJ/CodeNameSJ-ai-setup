#!/usr/bin/env zsh
# Lints a single TypeScript/Vue file after an Edit or Write, so failures surface
# before Claude claims done.
#
# History: this hook read $CLAUDE_TOOL_INPUT_FILE_PATH, which Claude Code does not
# set — PostToolUse delivers JSON on stdin — so it silently never ran. Two traps it
# also has to avoid, now that it does:
#   - Never invoke the package `lint` script: ai-frontend's ROOT script is
#     `eslint . --fix`, so passing a file appends to it and lints the whole repo.
#     Call the eslint binary on the one file instead.
#   - No project-wide `tsc --noEmit` here. On an app this size that is tens of
#     seconds on every edit; `npm run check` owns typechecking.

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -n "$FILE_PATH" ] || exit 0
[ -f "$FILE_PATH" ] || exit 0
[[ "$FILE_PATH" =~ \.(ts|tsx|vue)$ ]] || exit 0

# Nearest node_modules/.bin/eslint above the edited file decides both the binary
# and the working directory, so app-local config and plugins resolve correctly.
DIR="$(dirname "$FILE_PATH")"
while [ "$DIR" != "/" ]; do
  if [ -x "$DIR/node_modules/.bin/eslint" ]; then
    cd "$DIR" || exit 0
    # --quiet: errors only. Without it every .vue edit reprints the repo's chronic
    # localeDir config warning, which trains you to ignore this hook's output.
    OUT=$("$DIR/node_modules/.bin/eslint" --fix --quiet "$FILE_PATH" 2>&1)
    [ -n "$OUT" ] && printf '%s\n' "$OUT" | tail -15
    exit 0
  fi
  DIR="$(dirname "$DIR")"
done
exit 0
