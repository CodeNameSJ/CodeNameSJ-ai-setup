# Workspace Agent Harness Setup

This workspace uses one provider-neutral harness with native Claude Code, Cursor, and
Codex adapters. `AGENTS.md` is the always-on workspace contract.

## Layout

```text
Workspace/
├── AGENTS.md
├── CLAUDE.md
├── .agent-harness/
│   ├── agents/                     # canonical shared agent instructions
│   ├── commands/                   # canonical shared workflows
│   ├── skills/                     # shared skills; app skills may be symlinks
│   ├── references/                 # shared on-demand knowledge
│   ├── hooks/                      # hook implementations, not event manifests
│   ├── scripts/                    # maintenance scripts
│   ├── mcp/servers.json            # canonical MCP inventory/projections
│   ├── provider-agent-metadata.json# Claude-only model/tool assignments
│   ├── generated/                  # generated native adapters
│   └── sync.py
├── .claude/                        # Claude adapters + Claude-owned settings
├── .cursor/                        # Cursor adapters + Cursor application state
├── .codex/                         # generated Codex agents/config
└── .agents/skills                  # Codex workspace skill discovery adapter
```

## Restore on a new machine

1. Clone the config repo to `<workspace>/CodeNameSJ-ai-setup` and run its
   `./bootstrap.sh`, which does steps 1–2 for you and is safe to re-run. The rest of this
   section is what it automates, for reference or manual recovery.

   The canonical paths are not real files at the workspace root — they live in the repo:

   ```bash
   cd /Users/shubh/Workspace

   ln -s CodeNameSJ-ai-setup/workspace/AGENTS.md AGENTS.md
   ln -s CodeNameSJ-ai-setup/workspace/CLAUDE.md CLAUDE.md
   ln -s CodeNameSJ-ai-setup/workspace/.agent-harness .agent-harness
   ln -s Workspace/CodeNameSJ-ai-setup/user/.agent-harness ~/.agent-harness
   ln -s Workspace/CodeNameSJ-ai-setup/user/.agents ~/.agents
   ```

   Clone `ai-frontend` as a sibling before running the sync: `.agent-harness/skills/`
   symlinks into `ai-frontend/apps/voice-ai/agent-skills/`, and those links are dead
   until that repo exists.

2. Recreate the provider adapter symlinks:

   ```bash
   cd /Users/shubh/Workspace

   ln -s ../.agent-harness/generated/claude-agents .claude/agents
   ln -s ../.agent-harness/commands .claude/commands
   ln -s ../.agent-harness/references .claude/references
   ln -s ../.agent-harness/hooks .claude/hooks
   ln -s ../.agent-harness/scripts .claude/scripts
   ln -s ../.agent-harness/inactive .claude/inactive
   ln -s ../.agent-harness/skills .claude/skills

   ln -s ../.agent-harness/generated/cursor-agents .cursor/agents
   ln -s ../.agent-harness/commands .cursor/commands
   ln -s ../.agent-harness/skills .cursor/skills

   ln -s ../.agent-harness/generated/codex-agents .codex/agents
   ln -s ../.agent-harness/generated/codex-skills .agents/skills
   ```

3. Restore provider-owned settings separately:
   - `.claude/settings.json` and optional `.claude/settings.local.json`
   - Cursor application/user configuration (do not copy cache databases blindly)
   - user-level `~/.codex/config.toml` and installed Codex plugins
4. Recreate `.agent-harness/mcp/servers.json` from your secret store — it is excluded
   from the config repo because it carries credentials.
5. Run `python3 .agent-harness/sync.py`, then `python3 .agent-harness/sync.py --check`.
   The check reports `broken:` for any symlink that no longer resolves.
6. Restart each provider so it rediscovers agents, commands, skills, and MCP servers.

## Editing workflow

- Shared agent behavior: edit `.agent-harness/agents/<name>.md`.
- Claude model/tool assignment: edit `.agent-harness/provider-agent-metadata.json`.
- Shared command workflow: edit `.agent-harness/commands/<name>.md`.
- Shared skill: edit `.agent-harness/skills/<name>/SKILL.md` or its app-owned symlink target.
- MCP: edit `.agent-harness/mcp/servers.json`.
- Then run the sync and drift-check commands.

Never edit `.agent-harness/generated/`, `.codex/agents/`, generated command skills, root
`.mcp.json`, or `.cursor/mcp.json` directly.

## Provider boundaries

Centralizing content does not make provider schemas identical:

- Claude and Cursor use Markdown custom agents; Codex uses TOML custom agents.
- Claude and Cursor expose `/name` commands; Codex receives equivalent command skills
  and invokes them with `$name` or matching natural language.
- MCP JSON/TOML schemas differ, so `sync.py` projects the canonical inventory.
- Hook event names and payloads differ. Hook scripts are shared, but no Cursor/Codex
  hook manifest is enabled until its behavior is deliberately mapped and tested.
- Permissions, installed plugins/extensions, caches, conversation history, and secrets
  remain provider-owned.

## Validation

```bash
python3 .agent-harness/sync.py --check
python3 -m py_compile .agent-harness/sync.py
zsh .agent-harness/scripts/check-agent-sync.sh
```

The final command checks the two Voice AI agents that also have app-committed copies.
Application-level skills and rules remain independent from this workspace harness.
