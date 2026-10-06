#!/usr/bin/env python3
"""Check and deliberately update the user-level multi-agent toolchain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


HOME = Path.home()
SKILLS = HOME / ".agents" / "skills"
SKILL_LOCK = HOME / ".agents" / ".skill-lock.json"
NPM_GLOBALS = (
    "@nestjs/cli",
    "npm",
    "postman-cli",
    "typescript-language-server",
    "typescript",
)
CLAUDE_MEM_IDES = ("claude-code", "cursor", "codex-cli")
PROVIDER_ONLY_SKILL_FIELDS = ("user-invocable", "disable-model-invocation", "argument-hint")


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "agent-harness-updater/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def run(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, capture_output=True, text=True, timeout=300)


def digest(files: dict[str, bytes]) -> str:
    value = hashlib.sha256()
    for name, content in sorted(files.items()):
        value.update(name.encode())
        value.update(b"\0")
        value.update(content)
        value.update(b"\0")
    return value.hexdigest()


def local_tree(path: Path) -> dict[str, bytes]:
    return {
        str(file.relative_to(path)): file.read_bytes()
        for file in path.rglob("*")
        if file.is_file() and file.name != ".DS_Store" and "__pycache__" not in file.parts
    }


def normalize_upstream_skill(files: dict[str, bytes]) -> dict[str, bytes]:
    """Remove provider-only frontmatter unsupported by the shared Codex schema."""
    normalized = dict(files)
    skill = normalized.get("SKILL.md")
    if skill is None:
        return normalized
    lines = skill.decode().splitlines(keepends=True)
    normalized["SKILL.md"] = "".join(
        line
        for line in lines
        if not any(line.startswith(f"{field}:") for field in PROVIDER_ONLY_SKILL_FIELDS)
    ).encode()
    return normalized


def normalize_installed_skills() -> None:
    for skill_file in SKILLS.glob("*/SKILL.md"):
        original = skill_file.read_text()
        normalized = "".join(
            line
            for line in original.splitlines(keepends=True)
            if not any(line.startswith(f"{field}:") for field in PROVIDER_ONLY_SKILL_FIELDS)
        )
        if normalized != original:
            skill_file.write_text(normalized)


def check_skills() -> list[tuple[str, str, str, str]]:
    if not SKILL_LOCK.is_file():
        return [("shared skills", "missing", "unknown", "error")]
    locked = json.loads(SKILL_LOCK.read_text()).get("skills", {})
    rows: list[tuple[str, str, str, str]] = []
    repositories: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for name, metadata in sorted(locked.items()):
        repositories.setdefault(metadata.get("source", ""), []).append((name, metadata))

    with tempfile.TemporaryDirectory(prefix="agent-skill-check-") as temp:
        for repository, entries in repositories.items():
            if not repository:
                for name, _ in entries:
                    rows.append((name, "missing", "unknown", "error"))
                continue
            checkout = Path(temp) / repository.replace("/", "__")
            clone = run(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--depth=1",
                    "--filter=blob:none",
                    "--sparse",
                    f"https://github.com/{repository}.git",
                    str(checkout),
                ]
            )
            if clone.returncode:
                for name, _ in entries:
                    local = SKILLS / name
                    installed = digest(local_tree(local))[:12] if local.is_dir() else "missing"
                    rows.append((name, installed, "unavailable", "manual"))
                continue
            tree = run(["git", "-C", str(checkout), "ls-tree", "-r", "--name-only", "HEAD"])
            tree_paths = set(tree.stdout.splitlines())
            resolved: dict[str, tuple[str, bool]] = {}
            sparse_roots: set[str] = set()
            for name, metadata in entries:
                skill_path = metadata.get("skillPath", "")
                upstream_root = str(Path(skill_path).parent)
                relocated = skill_path not in tree_paths
                if relocated:
                    previous_folder = Path(skill_path).parent.name
                    candidates = [
                        path
                        for path in tree_paths
                        if path.endswith(f"/{previous_folder}/SKILL.md")
                    ]
                    if not candidates:
                        resolved[name] = ("", True)
                        continue
                    skill_path = min(candidates, key=lambda value: (len(Path(value).parts), value))
                    upstream_root = str(Path(skill_path).parent)
                resolved[name] = (upstream_root, relocated)
                sparse_roots.add(upstream_root)
            if sparse_roots:
                sparse = run(
                    ["git", "-C", str(checkout), "sparse-checkout", "set", *sorted(sparse_roots)]
                )
                if sparse.returncode:
                    for name, _ in entries:
                        local = SKILLS / name
                        installed = digest(local_tree(local))[:12] if local.is_dir() else "missing"
                        rows.append((name, installed, "checkout-error", "manual"))
                    continue
            for name, _ in entries:
                local = SKILLS / name
                upstream_root, relocated = resolved.get(name, ("", True))
                if not local.is_dir() or not upstream_root:
                    installed = digest(local_tree(local))[:12] if local.is_dir() else "missing"
                    rows.append((name, installed, "removed", "manual"))
                    continue
                local_digest = digest(local_tree(local))[:12]
                upstream_digest = digest(normalize_upstream_skill(local_tree(checkout / upstream_root)))[:12]
                policy = f"manual move:{upstream_root}" if relocated else "shared safe-update"
                rows.append((name, local_digest, upstream_digest, policy))
    for local_only in sorted(path.name for path in SKILLS.iterdir() if path.is_dir() and path.name not in locked):
        local_digest = digest(local_tree(SKILLS / local_only))[:12]
        rows.append((local_only, local_digest, local_digest, "local"))
    return rows


def npm_latest(package: str) -> str | None:
    try:
        encoded = urllib.parse.quote(package, safe="")
        return fetch_json(f"https://registry.npmjs.org/{encoded}/latest").get("version")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return None


def installed_npm_globals() -> dict[str, str]:
    result = run(["npm", "list", "-g", "--depth=0", "--json"])
    try:
        dependencies = json.loads(result.stdout).get("dependencies", {})
        return {name: item.get("version", "unknown") for name, item in dependencies.items()}
    except json.JSONDecodeError:
        return {}


def installed_graphify() -> str | None:
    try:
        data = json.loads(run(["pipx", "list", "--json"]).stdout)
        return data["venvs"]["graphifyy"]["metadata"]["main_package"]["package_version"]
    except (KeyError, json.JSONDecodeError, OSError):
        return None


def latest_graphify() -> str | None:
    try:
        return fetch_json("https://pypi.org/pypi/graphifyy/json")["info"]["version"]
    except (KeyError, urllib.error.URLError, TimeoutError, OSError):
        return None


def plugin_versions() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    latest_memory = npm_latest("claude-mem") or "unknown"
    memory_installs: dict[str, str] = {}
    claude_registry = HOME / ".claude" / "plugins" / "installed_plugins.json"
    try:
        records = json.loads(claude_registry.read_text()).get("plugins", {}).get(
            "claude-mem@thedotmack", []
        )
        if records:
            memory_installs["Claude"] = records[-1].get("version", "missing")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    cursor_mcp = HOME / ".cursor" / "mcp.json"
    try:
        server = json.loads(cursor_mcp.read_text()).get("mcpServers", {}).get("claude-mem", {})
        script = Path(server.get("args", [""])[0])
        package = script.parent.parent / "package.json"
        memory_installs["Cursor"] = json.loads(package.read_text()).get("version", "missing")
    except (FileNotFoundError, IndexError, json.JSONDecodeError, OSError):
        pass
    codex_root = HOME / ".codex" / "plugins" / "cache" / "claude-mem-local" / "claude-mem"
    codex_packages = list(codex_root.glob("*/package.json"))
    if codex_packages:
        newest = max(codex_packages, key=lambda path: path.stat().st_mtime)
        try:
            memory_installs["Codex"] = json.loads(newest.read_text()).get("version", "missing")
        except (json.JSONDecodeError, OSError):
            pass
    for provider in ("Claude", "Cursor", "Codex"):
        rows.append((f"claude-mem / {provider}", memory_installs.get(provider, "missing"), latest_memory))
    superdesign = HOME / ".cursor" / "plugins" / "cache" / "cursor-public" / "superdesign"
    installs = [path for path in superdesign.iterdir() if path.is_dir()] if superdesign.is_dir() else []
    installed_sha = sorted(installs, key=lambda path: path.stat().st_mtime)[-1].name if installs else "missing"
    try:
        remote_sha = run(
            ["git", "ls-remote", "https://github.com/superdesigndev/superdesign-skill.git", "HEAD"]
        ).stdout.split()[0]
    except (IndexError, OSError):
        remote_sha = "unknown"
    rows.append(("Superdesign / Cursor", installed_sha[:12], remote_sha[:12]))
    registry = HOME / ".claude" / "plugins" / "installed_plugins.json"
    catalog_path = HOME / ".claude" / "plugins" / "plugin-catalog-cache.json"
    try:
        installed_plugins = json.loads(registry.read_text()).get("plugins", {})
        catalog = json.loads(catalog_path.read_text()).get("catalog", {}).get("plugins", {})
        for plugin_id, records in sorted(installed_plugins.items()):
            if plugin_id == "claude-mem@thedotmack" or not records:
                continue
            installed = records[-1].get("version", "unknown")
            latest = catalog.get(plugin_id, {}).get("version") or installed
            rows.append((f"Claude / {plugin_id.split('@')[0]}", installed, latest))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return rows


def app_version(path: Path) -> str | None:
    info = path / "Contents" / "Info.plist"
    try:
        with info.open("rb") as handle:
            return plistlib.load(handle).get("CFBundleShortVersionString")
    except (FileNotFoundError, OSError, plistlib.InvalidFileException):
        return None


def brew_outdated_casks() -> set[str]:
    try:
        value = json.loads(run(["brew", "outdated", "--json=v2"]).stdout)
        return {item.get("token", "") for item in value.get("casks", [])}
    except (json.JSONDecodeError, OSError):
        return set()


def print_row(category: str, name: str, installed: str, latest: str, policy: str) -> None:
    marker = "=" if installed == latest else "->"
    print(f"{category:12} {name:30} {installed:16} {marker} {latest:16} {policy}")


def check() -> int:
    print("CATEGORY     ITEM                           INSTALLED        LATEST           POLICY")
    print("-" * 112)
    for name, installed, latest, policy in check_skills():
        print_row("skill", name, installed, latest, policy)

    graphify_installed = installed_graphify() or "missing"
    graphify_latest = latest_graphify() or "unknown"
    print_row("pipx", "graphifyy", graphify_installed, graphify_latest, "shared safe-update")

    globals_installed = installed_npm_globals()
    for package in NPM_GLOBALS:
        print_row(
            "npm-global",
            package,
            globals_installed.get(package, "missing"),
            npm_latest(package) or "unknown",
            "workspace latest",
        )

    for name, installed, latest in plugin_versions():
        print_row("plugin", name, installed, latest, "restart window")

    outdated_casks = brew_outdated_casks()
    for name, token, path in (
        ("Cursor", "cursor", Path("/Applications/Cursor.app")),
        ("Claude", "claude", Path("/Applications/Claude.app")),
    ):
        installed = app_version(path) or "missing"
        latest = "update available" if token in outdated_casks else installed
        print_row("app", name, installed, latest, "provider-owned")
    claude_cli = run(["claude", "--version"]).stdout.split()[0] if shutil.which("claude") else "missing"
    print_row("CLI", "Claude Code", claude_cli, npm_latest("@anthropic-ai/claude-code") or "unknown", "provider-owned")
    print_row("app", "Codex", "bundled", "native updater", "provider-owned")
    print_row("MCP", "Playwright/Jenkins", "@latest", "@latest", "rolling per launch")
    print("\n--apply: shared skills + Graphify.")
    print("--apply-all: also global workspace npm tools + one Claude-mem version for every IDE.")
    print("Desktop apps remain provider-owned and may require their native updater/restart.")
    return 0


def apply_safe_updates(*, audit: bool = True) -> int:
    if not sys.stdin.isatty():
        print("ERROR: --apply requires an interactive terminal", file=sys.stderr)
        return 2
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = HOME / ".local" / "share" / "agent-harness" / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(backup_dir / "personal-skills.tgz", "w:gz") as archive:
        archive.add(SKILLS, arcname="skills")
        archive.add(SKILL_LOCK, arcname=".skill-lock.json")
    commands = (
        ["npx", "--yes", "skills@latest", "update", "-g", "-y"],
        ["pipx", "upgrade", "graphifyy"],
        ["graphify", "install", "--platform", "agents"],
    )
    for command in commands:
        print("+", " ".join(command))
        subprocess.run(command, check=True)
    normalize_installed_skills()
    graphify_backup = SKILLS / "graphify" / "SKILL.md.bak"
    if graphify_backup.exists():
        graphify_backup.replace(backup_dir / "graphify-SKILL.md.bak")
    if audit:
        subprocess.run(["python3", str(HOME / ".agent-harness" / "audit.py")], check=True)
    print(f"Backup: {backup_dir}")
    return 0


def claude_mem_port() -> str:
    settings = HOME / ".claude-mem" / "settings.json"
    try:
        return str(json.loads(settings.read_text()).get("CLAUDE_MEM_WORKER_PORT", "37777"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "37777"


def archive_stale_claude_mem_caches(current_version: str) -> Path | None:
    """Move superseded provider caches to Trash after all adapters are upgraded."""
    roots = {
        "claude": HOME / ".claude" / "plugins" / "cache" / "thedotmack" / "claude-mem",
        "cursor": HOME / ".cursor" / "plugins" / "cache" / "thedotmack" / "claude-mem",
        "codex": HOME / ".codex" / "plugins" / "cache" / "claude-mem-local" / "claude-mem",
    }
    archive_root: Path | None = None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for provider, root in roots.items():
        if not root.is_dir():
            continue
        for cache in root.iterdir():
            if not cache.is_dir():
                continue
            try:
                version = json.loads((cache / "package.json").read_text()).get("version")
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                print(f"Preserving unrecognized claude-mem cache: {cache}")
                continue
            if version == current_version:
                continue
            archive_root = archive_root or HOME / ".Trash" / f"claude-mem-stale-caches-{timestamp}"
            destination = archive_root / provider / cache.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                destination = destination.with_name(f"{destination.name}-{timestamp}")
            shutil.move(str(cache), str(destination))
            print(f"Archived stale claude-mem cache: {cache} -> {destination}")
    return archive_root


def apply_all_updates() -> int:
    """Update the shared harness and user-level tools without touching repository lockfiles."""
    if not sys.stdin.isatty():
        print("ERROR: --apply-all requires an interactive terminal", file=sys.stderr)
        return 2
    result = apply_safe_updates(audit=False)
    if result:
        return result

    npm_packages = [f"{package}@latest" for package in NPM_GLOBALS]
    print("+ npm install -g", " ".join(npm_packages))
    subprocess.run(["npm", "install", "-g", *npm_packages], check=True)

    memory_version = npm_latest("claude-mem")
    if not memory_version:
        raise RuntimeError("Unable to resolve the latest claude-mem version")
    memory_backup = HOME / ".local" / "share" / "agent-harness" / "backups" / datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ-claude-mem")
    memory_backup.mkdir(parents=True, exist_ok=True)
    memory_dir = HOME / ".claude-mem"
    database = memory_dir / "claude-mem.db"
    if database.exists():
        with sqlite3.connect(database) as source, sqlite3.connect(
            memory_backup / "claude-mem.db"
        ) as destination:
            source.backup(destination)
    for name in ("settings.json", "vector-sync-state.json"):
        source = memory_dir / name
        if source.exists():
            shutil.copy2(source, memory_backup / name)

    for ide in CLAUDE_MEM_IDES:
        command = [
            "npx",
            "--yes",
            f"claude-mem@{memory_version}",
            "install",
            "--ide",
            ide,
            "--provider",
            "claude",
            "--runtime",
            "worker",
            "--no-auto-start",
        ]
        print("+", " ".join(command))
        subprocess.run(command, check=True)

    stale_cache_archive = archive_stale_claude_mem_caches(memory_version)
    port = claude_mem_port()
    print(f"+ CLAUDE_MEM_WORKER_PORT={port} npx claude-mem@{memory_version} start")
    subprocess.run(
        ["npx", "--yes", f"claude-mem@{memory_version}", "start"],
        check=True,
        env={**os.environ, "CLAUDE_MEM_WORKER_PORT": port},
    )
    print(f"Claude-mem backup: {memory_backup}")
    if stale_cache_archive:
        print(f"Stale claude-mem caches: {stale_cache_archive}")
    print("Restart open Claude/Cursor sessions once so they reload the upgraded adapters.")
    return check()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Update shared skills and Graphify, then run the harness audit",
    )
    parser.add_argument(
        "--apply-all",
        action="store_true",
        help="Also update workspace-global npm tools and Claude-mem for Claude, Cursor, and Codex",
    )
    args = parser.parse_args()
    if args.apply and args.apply_all:
        parser.error("choose either --apply or --apply-all")
    if args.apply_all:
        return apply_all_updates()
    return apply_safe_updates() if args.apply else check()


if __name__ == "__main__":
    raise SystemExit(main())
