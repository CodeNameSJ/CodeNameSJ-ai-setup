#!/usr/bin/env zsh
# Activate or deactivate a harness agent/command without deleting it.
#
# Inactive files live in .agent-harness/inactive/{agents,commands}/. Provider adapters
# expose only the active canonical directories.
#
#   zsh .claude/scripts/toggle.sh                 # list what is active and inactive
#   zsh .claude/scripts/toggle.sh off test-writer # deactivate (agent or command)
#   zsh .claude/scripts/toggle.sh on  test-writer # reactivate
#
# A command and its agent are separate files — toggle both if they pair up.

set -uo pipefail
# :A resolves symlinks on purpose — this script moves the harness's own files, so it
# wants the real canonical tree no matter which adapter path invoked it.
WS="${0:A:h:h}"
ACT_A="$WS/agents";           ACT_C="$WS/commands"
INA_A="$WS/inactive/agents";  INA_C="$WS/inactive/commands"
mkdir -p "$INA_A" "$INA_C"

list() {
  print -r -- "ACTIVE agents:";    for f in "$ACT_A"/*.md(N);  print -r -- "  ${f:t:r}"
  print -r -- "ACTIVE commands:";  for f in "$ACT_C"/*.md(N);  print -r -- "  /${f:t:r}"
  print -r -- "INACTIVE agents:";  for f in "$INA_A"/*.md(N);  print -r -- "  ${f:t:r}"
  print -r -- "INACTIVE commands:";for f in "$INA_C"/*.md(N);  print -r -- "  /${f:t:r}"
}

[[ $# -lt 2 ]] && { list; exit 0 }

dir=$1; name=${2:t:r}
moved=0
case $dir in
  off) for pair in "$ACT_A:$INA_A" "$ACT_C:$INA_C"; do
         src=${pair%%:*}; dst=${pair##*:}
         [[ -f "$src/$name.md" ]] && { mv "$src/$name.md" "$dst/"; print -r -- "deactivated ${src:t}/$name.md"; moved=1 }
       done ;;
  on)  for pair in "$INA_A:$ACT_A" "$INA_C:$ACT_C"; do
         src=${pair%%:*}; dst=${pair##*:}
         [[ -f "$src/$name.md" ]] && { mv "$src/$name.md" "$dst/"; print -r -- "activated ${dst:t}/$name.md"; moved=1 }
       done ;;
  *)   print -r -- "usage: toggle.sh [on|off] <name>"; exit 2 ;;
esac

(( moved )) || { print -r -- "no file named '$name.md' found to turn $dir"; exit 1 }
print -r -- "Start a new session for the change to register."
print -r -- "From your workspace root, run: python3 .agent-harness/sync.py"
