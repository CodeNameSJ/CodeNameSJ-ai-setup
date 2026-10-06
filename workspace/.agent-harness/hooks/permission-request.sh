#!/usr/bin/env zsh
# Approve file tools inside the workspace or Claude's scratch directories.
# Shell commands follow native permission rules; this hook does not parse shell text.
python3 -c '
import json
import os
import sys
from pathlib import Path

try:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    allowed = tool in {"Read", "Glob", "Grep", "WebFetch", "WebSearch"}
    if tool in {"Write", "Edit"}:
        filename = event.get("tool_input", {}).get("file_path", "")
        if filename:
            target = Path(filename).expanduser()
            if not target.is_absolute():
                target = Path(event.get("cwd") or os.getcwd()) / target
            target = target.resolve()
            workspace = Path(os.environ.get("WORKSPACE_DIR", str(Path.home() / "Workspace"))).resolve()
            allowed = target.is_relative_to(workspace)
            if target.is_relative_to(Path("/private/tmp")):
                parts = target.relative_to("/private/tmp").parts
                allowed = allowed or bool(parts and parts[0].startswith("claude-"))
    if allowed:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}))
except (ValueError, OSError, TypeError, KeyError):
    pass
'
