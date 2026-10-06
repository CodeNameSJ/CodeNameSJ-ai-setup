# User-level agent harness

This directory documents configuration shared across repositories. Its scope stays
separate from `/Users/shubh/Workspace/.agent-harness`, which contains team/project
behavior — though both are now tracked in one config repo, as `user/` and `workspace/`
in `CodeNameSJ-ai-setup`. This path is a symlink into that repo's `user/` subtree.

## Ownership

- `~/.agents/skills/` is the canonical store for personal, cross-provider skills.
- `~/.claude/skills` and `~/.cursor/skills` point to that canonical directory.
- Codex discovers `~/.agents/skills` directly; do not copy personal skills into
  `~/.codex/skills`, which also contains Codex-managed system/runtime skills.
- Cursor-managed built-ins remain in `~/.cursor/skills-cursor`; they are application
  state, not authored personal skills.
- Provider settings, credentials, caches, databases, histories, plugins, and MCP
  runtime state remain provider-owned. They must not be symlinked or mechanically
  normalized because their schemas and lifecycles differ.
- Repository skills, commands, agents, hooks, and MCP definitions remain in the
  repository/workspace harness so teammates receive them without inheriting personal
  configuration.

## Graphify

Graphify is installed once through pipx. Its current cross-provider skill is installed
in `~/.agents/skills/graphify`. Use its graph as an orientation aid, then confirm caller
and blast-radius conclusions with `rg`.

`code-review-graph` is intentionally absent: its measured impact traversal followed
dependencies instead of dependents and produced unsafe low-risk results.

## Shared memory

- `~/.claude-mem/` is the one persistent data store for Claude, Cursor, and Codex
  memories. Do not copy or symlink its database into provider directories.
- Capture remains provider-specific because each host emits different lifecycle events.
  Provider plugin caches and hooks must remain provider-owned.
- Retrieval is shared through `~/.agents/skills/mem-search`, which talks to the local
  worker API without depending on a provider-specific MCP tool name.
- Do not restart a healthy worker merely for cleanup. For upgrades, use the unified
  updater during a planned maintenance window; it installs one version for every provider.
- Leave `CLAUDE_MEM_MODEL` unset unless a deliberate temporary override is required; the
  installed release then selects its supported summarizer default instead of retaining a
  stale model pin across upgrades.
- The audit checks database integrity, worker health, provider-version drift, project-name
  fragmentation, and stale logs without printing settings or credentials.

## Audit

Run:

```bash
python3 ~/.agent-harness/audit.py
```

The audit is read-only and never prints MCP environment values or credentials.

## Updates

Run the unified read-only inventory:

```bash
agent-harness-update
```

Apply only the safe shared layer—canonical skills and Graphify—from an interactive
terminal:

```bash
agent-harness-update --apply
```

Update the complete user-level workspace toolchain from an interactive terminal:

```bash
agent-harness-update --apply-all
```

This updates canonical skills, Graphify, the workspace-global npm tools, and installs one
current claude-mem release for Claude, Cursor, and Codex. It backs up the memory database
and settings first, then moves superseded provider caches to a dated folder in Trash.
Backups are stored at `~/.local/share/agent-harness/backups/`, outside this config repo.
Restart open Claude/Cursor sessions afterward so their adapters reload. The audit treats
provider/worker version drift as a failure rather than allowing one provider to remain stale.

The updater deliberately does not replace provider applications:

- repositories still resolve Node tooling through Volta and their own lockfiles; updating
  global tools does not alter repository dependency versions;
- Cursor, Claude, and Codex applications retain their native signed updaters;
- claude-mem adapter reloads still require one application restart after `--apply-all`.

Do not use `npx skills check -g` as a read-only check. Despite its name, the current CLI
immediately applies updates. The unified inventory compares upstream content without
mutating installed skills.
