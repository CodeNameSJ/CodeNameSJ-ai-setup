#!/usr/bin/env python3
"""Rebuild the workspace Graphify indexes deterministically and without LLM tokens."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from graphify.analyze import god_nodes, suggest_questions, surprising_connections
from graphify.build import build_from_json
from graphify.cluster import cluster, label_communities_by_hub, score_all
from graphify.export import to_html, to_json
from graphify.extract import collect_files, extract
from graphify.report import generate


# abspath, not resolve: `.agent-harness` is itself a symlink into the config repo, and
# dereferencing it would point WORKSPACE at the repo checkout instead of the workspace.
WORKSPACE = Path(os.path.abspath(__file__)).parents[1]
OUTPUT_ROOT = WORKSPACE / "graphify-out"

SCOPES: dict[str, tuple[Path, ...]] = {
    "agent-builder": (
        WORKSPACE / "ai-frontend/apps/agent-builder/src",
        WORKSPACE / "ghl-crm-frontend/apps/voice-ai/src/components/builder",
    ),
    "voice-ai-backend": (WORKSPACE / "ai-backend/apps/voice-ai",),
    "voice-ai-frontend": (
        WORKSPACE / "ai-frontend/apps/voice-ai",
        WORKSPACE / "ghl-crm-frontend/apps/voice-ai",
    ),
}


def output_dir(scope: str) -> Path:
    return OUTPUT_ROOT if scope == "agent-builder" else OUTPUT_ROOT / scope


def source_words(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        try:
            total += len(path.read_text(encoding="utf-8", errors="ignore").split())
        except OSError:
            continue
    return total


def backup_outputs(target: Path, stamp: str) -> None:
    backup = target / "backups" / stamp
    copied = False
    for name in ("graph.json", "GRAPH_REPORT.md", "graph.html", "manifest.json"):
        source = target / name
        if source.exists():
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup / name)
            copied = True
    if not copied and backup.exists():
        backup.rmdir()


def rebuild(scope: str, roots: tuple[Path, ...], stamp: str) -> None:
    missing = [str(path) for path in roots if not path.exists()]
    if missing:
        raise FileNotFoundError(f"{scope}: missing source roots: {', '.join(missing)}")

    files: list[Path] = []
    for root in roots:
        files.extend(collect_files(root, root=WORKSPACE))
    files = sorted(set(path.resolve() for path in files))
    if not files:
        raise RuntimeError(f"{scope}: no supported code files found")

    extraction = extract(files, cache_root=WORKSPACE, root=WORKSPACE)
    graph = build_from_json(extraction, root=WORKSPACE, directed=True)
    if graph.number_of_nodes() == 0:
        raise RuntimeError(f"{scope}: extraction produced an empty graph")

    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = label_communities_by_hub(graph, communities)
    gods = god_nodes(graph)
    surprises = surprising_connections(graph, communities)
    questions = suggest_questions(graph, communities, labels)
    detection = {
        "total_files": len(files),
        "total_words": source_words(files),
        "files": {"code": [str(path) for path in files]},
        "scan_root": str(WORKSPACE),
    }
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        detection,
        {"input": 0, "output": 0},
        "+".join(path.name for path in roots),
        suggested_questions=questions,
    )

    target = output_dir(scope)
    target.mkdir(parents=True, exist_ok=True)
    backup_outputs(target, stamp)

    graph_tmp = target / ".graph.next.json"
    html_tmp = target / ".graph.next.html"
    report_tmp = target / ".GRAPH_REPORT.next.md"
    manifest_tmp = target / ".manifest.next.json"

    to_json(graph, communities, str(graph_tmp), force=True, community_labels=labels)
    to_html(
        graph,
        communities,
        str(html_tmp),
        community_labels=labels,
        node_limit=5000,
    )
    report_tmp.write_text(report, encoding="utf-8")
    manifest_tmp.write_text(
        json.dumps(
            {
                "scope": scope,
                "roots": [str(path.relative_to(WORKSPACE)) for path in roots],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "graphify_version": version("graphifyy"),
                "directed": True,
                "code_only": True,
                "files": len(files),
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    os.replace(graph_tmp, target / "graph.json")
    os.replace(html_tmp, target / "graph.html")
    os.replace(report_tmp, target / "GRAPH_REPORT.md")
    os.replace(manifest_tmp, target / "manifest.json")
    (target / ".graphify_root").write_text(
        "\n".join(str(path) for path in roots) + "\n", encoding="utf-8"
    )
    print(
        f"{scope}: {len(files)} files, {graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} directed edges"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scopes",
        nargs="*",
        choices=tuple(SCOPES),
        help="Scopes to rebuild (default: all)",
    )
    args = parser.parse_args()
    selected = args.scopes or list(SCOPES)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for scope in selected:
        rebuild(scope, SCOPES[scope], stamp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
