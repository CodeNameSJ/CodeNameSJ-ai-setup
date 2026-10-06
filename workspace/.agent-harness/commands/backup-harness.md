Commit the provider-neutral workspace harness to the config repo.

The harness is version-controlled: `.agent-harness/` is a symlink into
`CodeNameSJ-ai-setup/workspace/`, so editing it edits the repo working tree. There is
nothing to copy or rsync — back it up by committing.

```bash
cd /Users/shubh/Workspace && python3 .agent-harness/sync.py --check
cd /Users/shubh/Workspace/CodeNameSJ-ai-setup && git status --short
```

Verify the adapter check passes before committing; a `broken:` line means a symlink no
longer resolves and would be committed dead.

`mcp/servers.json` is excluded by `.gitignore` because it carries credentials inherited
from native provider configs. Back it up only through a secure secret store. Generated
adapters, `backups/`, and provider caches are excluded too — `sync.py` rebuilds them.

Staging and commits are the user's call; do not run `git commit` or `git push`.
