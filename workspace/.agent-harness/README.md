# Workspace Agent Harness

This directory is the provider-neutral source of truth for reusable workspace agent
configuration. Provider directories contain only native adapters or provider-owned
runtime settings.

It is version-controlled: `/Users/shubh/Workspace/.agent-harness` is a symlink into
`CodeNameSJ-ai-setup/workspace/`, so edits here are edits to that repo's working tree.
`skills/automate-ui` and `skills/triage-ui` symlink back out into
`ai-frontend/apps/voice-ai/agent-skills/`, which means the app repo must be cloned as a
sibling for them to resolve. `sync.py --check` reports any link that does not.

## Ownership

| Capability | Canonical source | Claude | Cursor | Codex |
| --- | --- | --- | --- | --- |
| Workspace rules | `../AGENTS.md` | `../CLAUDE.md` imports it | `.cursor/rules/workspace.mdc` points to it | discovers it directly |
| Agents | `agents/*.md` + `provider-agent-metadata.json` | generated Markdown with Claude model/tool metadata | generated provider-neutral Markdown | generated `.codex/agents/*.toml` |
| Commands/workflows | `commands/*.md` | `.claude/commands` symlink (`/name`) | `.cursor/commands` symlink (`/name`) | generated command skills (`$name` or natural language) |
| Skills | `skills/*/SKILL.md` | two shared skills; workflows stay native commands | two shared skills; workflows stay native commands | generated projection combines shared skills and command-equivalent skills |
| References | `references/*` | `.claude/references` symlink | available by canonical path | available by canonical path |
| Hook implementations | `hooks/*` | `.claude/hooks` symlink | available for an explicit Cursor hook adapter | no adapter enabled |
| Harness scripts | `scripts/*` | `.claude/scripts` symlink | canonical path | canonical path |
| MCP definitions | `mcp/servers.json` | generated `.mcp.json` | generated `.cursor/mcp.json` | project-safe servers generated in `.codex/config.toml` |

Run `python3 .agent-harness/sync.py` after changing agents, commands, or MCP sources.
Run `python3 .agent-harness/sync.py --check` to fail on adapter drift without writing.

Rebuild the three workspace code graphs with zero-token AST extraction using Graphify's
installed Python runtime:

```bash
~/.local/pipx/venvs/graphifyy/bin/python .agent-harness/refresh_graphs.py
```

The script preserves prior graph/report/HTML outputs under each scope's `backups/`
directory and always emits directed graphs.

## Deliberately provider-owned

These are not centralized because their semantics are not portable:

- `.claude/settings.json` and `.claude/settings.local.json` (Claude permissions, model,
  plugins, personal MCP enablement)
- `.cursor/argv.json`, `.cursor/extensions`, `.cursor/projects`, `.cursor/snapshots`,
  `.cursor/skills-cursor`, and other Cursor application state
- user-level `~/.codex/config.toml`, installed Codex plugins, and personal permissions
- hook event manifests: Claude, Cursor, and Codex use different event schemas
- secrets. Existing secret-bearing MCP fields remain in the local canonical MCP file.
  `mcp/servers.json` is excluded by the config repo's `.gitignore`; keep it that way and
  back it up only through a secret store.

## Rules

- Edit canonical content here, never an adapter output.
- Keep app-owned skills in their application. Workspace skill entries may symlink to
  them; this does not make the workspace copy authoritative.
- An agent body must be provider-neutral. Claude-specific model/tool restrictions belong
  in `provider-agent-metadata.json`, not in shared instructions.
- Do not add the same MCP server independently to multiple provider files. Add it once
  to `mcp/servers.json` and declare its provider projections there.
- Never centralize provider caches, conversation history, extension state, or credentials.
