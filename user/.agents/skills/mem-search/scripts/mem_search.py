#!/usr/bin/env python3
"""Provider-neutral CLI for the local claude-mem worker API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SETTINGS = Path.home() / ".claude-mem" / "settings.json"


def worker_base_url() -> str:
    host = "127.0.0.1"
    port = 37777
    try:
        settings = json.loads(SETTINGS.read_text())
        host = settings.get("CLAUDE_MEM_WORKER_HOST") or host
        port = int(settings.get("CLAUDE_MEM_WORKER_PORT") or port)
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        pass
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"http://{host}:{port}"


def request(path: str, *, params: dict[str, Any] | None = None, body: Any = None) -> Any:
    url = worker_base_url() + path
    if params:
        values = {key: value for key, value in params.items() if value is not None}
        url += "?" + urllib.parse.urlencode(values)
    data = None if body is None else json.dumps(body).encode()
    headers = {} if data is None else {"Content-Type": "application/json"}
    method = "GET" if data is None else "POST"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers=headers, method=method), timeout=15
        ) as response:
            payload = response.read().decode()
            return json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"claude-mem returned HTTP {error.code}: {detail}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(
            f"claude-mem worker is unavailable at {worker_base_url()}; "
            "leave worker lifecycle management to its provider adapter"
        ) from error


def print_result(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("health", help="Check worker health without changing it")

    search = commands.add_parser("search", help="Search memory and return a compact index")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--project")
    search.add_argument("--platform-source")
    search.add_argument("--type", choices=("observations", "sessions", "prompts"))
    search.add_argument("--obs-type")
    search.add_argument("--date-start")
    search.add_argument("--date-end")
    search.add_argument("--offset", type=int)
    search.add_argument("--order-by", choices=("date_desc", "date_asc", "relevance"))

    timeline = commands.add_parser("timeline", help="Show context around an observation")
    anchor = timeline.add_mutually_exclusive_group(required=True)
    anchor.add_argument("--anchor", type=int)
    anchor.add_argument("--query")
    timeline.add_argument("--before", type=int, default=5)
    timeline.add_argument("--after", type=int, default=5)
    timeline.add_argument("--project")

    get = commands.add_parser("get", help="Fetch full details for selected observations")
    get.add_argument("ids", nargs="+", type=int)
    get.add_argument("--project")
    get.add_argument("--order-by", choices=("date_desc", "date_asc"), default="date_desc")
    get.add_argument("--limit", type=int)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "health":
        result = request("/api/health")
    elif args.command == "search":
        result = request(
            "/api/search",
            params={
                "query": args.query,
                "limit": args.limit,
                "project": args.project,
                "platformSource": args.platform_source,
                "type": args.type,
                "obs_type": args.obs_type,
                "dateStart": args.date_start,
                "dateEnd": args.date_end,
                "offset": args.offset,
                "orderBy": args.order_by,
            },
        )
    elif args.command == "timeline":
        result = request(
            "/api/timeline",
            params={
                "anchor": args.anchor,
                "query": args.query,
                "depth_before": args.before,
                "depth_after": args.after,
                "project": args.project,
            },
        )
    else:
        result = request(
            "/api/observations/batch",
            body={
                "ids": args.ids,
                "project": args.project,
                "orderBy": args.order_by,
                "limit": args.limit,
            },
        )
    print_result(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error

