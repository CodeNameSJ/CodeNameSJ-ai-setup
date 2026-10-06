#!/usr/bin/env python3
"""Read-only health check for the user-level multi-agent configuration."""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import tomllib
import urllib.error
import urllib.request
from pathlib import Path


HOME = Path.home()
CANONICAL_SKILLS = HOME / ".agents" / "skills"


def fail(message: str) -> None:
    failures.append(message)


failures: list[str] = []
warnings: list[str] = []


def package_version(path: Path) -> str | None:
    try:
        return json.loads(path.read_text()).get("version")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

for adapter in (HOME / ".claude" / "skills", HOME / ".cursor" / "skills"):
    if not adapter.is_symlink():
        fail(f"{adapter} is not a symlink")
        continue
    if adapter.resolve() != CANONICAL_SKILLS.resolve():
        fail(f"{adapter} resolves to {adapter.resolve()}, expected {CANONICAL_SKILLS}")

for link in CANONICAL_SKILLS.rglob("*"):
    if link.is_symlink() and not link.exists():
        fail(f"broken skill symlink: {link}")

if shutil.which("code-review-graph"):
    fail("code-review-graph is installed but intentionally unsupported")

graphify = shutil.which("graphify")
graphify_skill = CANONICAL_SKILLS / "graphify" / "SKILL.md"
if not graphify:
    fail("graphify executable is missing")
elif not graphify_skill.is_file():
    fail("canonical Graphify skill is missing")

updater = HOME / ".agent-harness" / "update.py"
updater_command = HOME / ".local" / "bin" / "agent-harness-update"
if not updater.is_file():
    fail("unified agent harness updater is missing")
if not updater_command.is_symlink() or updater_command.resolve() != updater.resolve():
    fail("agent-harness-update does not resolve to the unified updater")

codex_config = HOME / ".codex" / "config.toml"
cursor_mcp = HOME / ".cursor" / "mcp.json"
if codex_config.exists():
    codex = tomllib.loads(codex_config.read_text())
    print("Codex MCP:", ", ".join(sorted(codex.get("mcp_servers", {}))) or "none")
if cursor_mcp.exists():
    cursor = json.loads(cursor_mcp.read_text())
    print("Cursor MCP:", ", ".join(sorted(cursor.get("mcpServers", {}))) or "none")

memory_root = HOME / ".claude-mem"
memory_db = memory_root / "claude-mem.db"
if not memory_db.is_file():
    fail("shared claude-mem database is missing")
else:
    try:
        connection = sqlite3.connect(f"file:{memory_db}?mode=ro", uri=True)
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            fail(f"claude-mem database quick_check returned: {integrity}")
        projects = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT project, COUNT(*) FROM observations GROUP BY project"
            )
            if row[0]
        }
        connection.close()
        casefolded: dict[str, list[str]] = {}
        for project in projects:
            casefolded.setdefault(project.casefold(), []).append(project)
        for aliases in casefolded.values():
            if len(aliases) > 1:
                warnings.append(
                    "claude-mem project aliases differ only by case: " + ", ".join(sorted(aliases))
                )
        suspicious = [
            project
            for project in projects
            if project[0].isdigit() or (len(project) >= 24 and all(c in "0123456789abcdef" for c in project))
        ]
        if suspicious:
            warnings.append("claude-mem has suspicious project names: " + ", ".join(sorted(suspicious)))
    except (sqlite3.DatabaseError, OSError) as error:
        fail(f"claude-mem database could not be checked: {error}")

settings_path = memory_root / "settings.json"
worker_host, worker_port = "127.0.0.1", 37777
worker_version: str | None = None
try:
    memory_settings = json.loads(settings_path.read_text())
    if "CLAUDE_MEM_MODEL" in memory_settings:
        warnings.append(
            "claude-mem summarizer is explicitly pinned; remove CLAUDE_MEM_MODEL to follow the installed release default"
        )
    worker_host = memory_settings.get("CLAUDE_MEM_WORKER_HOST") or worker_host
    worker_port = int(memory_settings.get("CLAUDE_MEM_WORKER_PORT") or worker_port)
    if worker_host == "0.0.0.0":
        worker_host = "127.0.0.1"
except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
    warnings.append("claude-mem settings could not be read; checking the default worker address")

try:
    with urllib.request.urlopen(f"http://{worker_host}:{worker_port}/api/health", timeout=2) as response:
        health = json.loads(response.read().decode())
        worker_version = health.get("version")
        print("Claude-mem worker:", worker_version or "unknown", health.get("status", "unknown"))
except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
    warnings.append(f"claude-mem worker health unavailable: {error}")

memory_versions: dict[str, str] = {}
try:
    records = json.loads(
        (HOME / ".claude" / "plugins" / "installed_plugins.json").read_text()
    ).get("plugins", {}).get("claude-mem@thedotmack", [])
    if records:
        memory_versions["Claude"] = records[-1].get("version", "missing")
except (FileNotFoundError, json.JSONDecodeError, OSError):
    pass
try:
    server = json.loads(cursor_mcp.read_text()).get("mcpServers", {}).get("claude-mem", {})
    script = Path(server.get("args", [""])[0])
    version = package_version(script.parent.parent / "package.json")
    if version:
        memory_versions["Cursor"] = version
except (FileNotFoundError, IndexError, json.JSONDecodeError, OSError):
    pass
codex_packages = list(
    (HOME / ".codex" / "plugins" / "cache" / "claude-mem-local" / "claude-mem").glob(
        "*/package.json"
    )
)
if codex_packages:
    version = package_version(max(codex_packages, key=lambda path: path.stat().st_mtime))
    if version:
        memory_versions["Codex"] = version
if worker_version:
    memory_versions["Worker"] = worker_version
if len(set(memory_versions.values())) > 1:
    fail(
        "claude-mem provider version drift: "
        + ", ".join(f"{provider} {version}" for provider, version in memory_versions.items())
    )

try:
    claude_settings = json.loads((HOME / ".claude" / "settings.json").read_text())
    if not claude_settings.get("autoMode", {}).get("environment"):
        warnings.append("Claude Auto Mode has no workspace environment context")
except (FileNotFoundError, json.JSONDecodeError, OSError):
    warnings.append("Claude settings could not be checked for Auto Mode environment context")

installed_plugins = HOME / ".claude" / "plugins" / "installed_plugins.json"
try:
    plugin_ids = json.loads(installed_plugins.read_text()).get("plugins", {})
    duplicate_plugins = sorted(
        plugin_id
        for plugin_id in plugin_ids
        if (CANONICAL_SKILLS / plugin_id.split("@", 1)[0]).is_dir()
    )
    if duplicate_plugins:
        warnings.append(
            "Claude plugins duplicate canonical shared skills: " + ", ".join(duplicate_plugins)
        )
except (FileNotFoundError, json.JSONDecodeError, OSError):
    warnings.append("Claude plugin registry could not be checked for shared-skill duplicates")

stale_logs = list((memory_root / "logs").glob("*.log"))
if len(stale_logs) > 30:
    warnings.append(f"claude-mem has {len(stale_logs)} log files; archive old logs periodically")

for graph in (
    HOME / "Workspace" / "graphify-out" / "voice-ai-backend" / "graph.json",
    HOME / "Workspace" / "graphify-out" / "voice-ai-frontend" / "graph.json",
    HOME / "Workspace" / "graphify-out" / "graph.json",
):
    if graph.exists() and json.loads(graph.read_text()).get("directed") is not True:
        warnings.append(f"Graphify graph is undirected: {graph}")

try:
    result = subprocess.run(
        ["python3", "/Users/shubh/Workspace/.agent-harness/sync.py", "--check"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        fail("workspace harness projections are out of sync")
except (OSError, subprocess.TimeoutExpired):
    fail("workspace harness sync check could not run")

if failures:
    for message in failures:
        print(f"FAIL: {message}")
    raise SystemExit(1)

for message in warnings:
    print(f"WARN: {message}")
print(f"PASS: {len([p for p in CANONICAL_SKILLS.iterdir() if p.is_dir()])} canonical personal skills")
