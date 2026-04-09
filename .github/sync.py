#!/usr/bin/env python3
"""Sync copilot-template updates to all registered projects.

Run from the copilot-template root (executed automatically by post-merge hook).
Reads projects.json, copies pure-template files to each registered project,
and rebuilds the code-graph + visualizer for projects with code_graph: true.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).parent.parent  # .github/sync.py -> root
PROJECTS_FILE = TEMPLATE_ROOT / "projects.json"

# Skip these when recursively copying directories
SKIP_DIRS = {"node_modules", "__pycache__", ".code-graph"}
SKIP_SUFFIXES = {".bak", ".pyc", ".db"}

# Never overwrite these — user has customized them during initialization
SKIP_FILES = {"CLAUDE.md", "copilot-instructions.md", "config.yaml"}


def _find_uv() -> Path | None:
    uv = shutil.which("uv")
    if uv:
        return Path(uv)
    candidate = Path.home() / ".local" / "bin" / "uv"
    return candidate if candidate.exists() else None


def _copy_dir(src: Path, dst: Path) -> int:
    """Recursively copy src to dst, skipping excluded items. Returns file count."""
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src.iterdir():
        if item.name in SKIP_DIRS:
            continue
        if item.suffix in SKIP_SUFFIXES:
            continue
        if item.name in SKIP_FILES:
            continue
        if item.is_dir():
            count += _copy_dir(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)
            count += 1
    return count


def sync_project(project: dict) -> bool:
    path = Path(project["path"])
    if not path.exists():
        print(f"  SKIP  {path}  (path not found)")
        return False

    tools = set(project.get("tools", []))
    code_graph = project.get("code_graph", False)
    total = 0

    # Claude Code commands
    if "claude" in tools:
        src = TEMPLATE_ROOT / ".claude" / "commands" / "project"
        if src.exists():
            total += _copy_dir(src, path / ".claude" / "commands" / "project")

    # VS Code Copilot files
    if "vscode" in tools:
        for subdir in ("agents", "skills", "prompts", "instructions"):
            src = TEMPLATE_ROOT / ".github" / subdir
            if src.exists():
                total += _copy_dir(src, path / ".github" / subdir)
        agents_md = TEMPLATE_ROOT / "AGENTS.md"
        if agents_md.exists():
            shutil.copy2(agents_md, path / "AGENTS.md")
            total += 1

    # Code graph server + parsers
    if code_graph:
        src = TEMPLATE_ROOT / ".github" / "code-graph"
        if src.exists():
            total += _copy_dir(src, path / ".github" / "code-graph")

    print(f"  SYNC  {path}  ({total} files updated)")

    # Rebuild graph + regenerate visualizer
    if code_graph:
        _rebuild_graph(path)

    return True


def _rebuild_graph(project_path: Path) -> None:
    uv = _find_uv()
    server = project_path / ".github" / "code-graph" / "server.py"
    reqs = project_path / ".github" / "code-graph" / "requirements.txt"

    if not server.exists():
        print(f"  SKIP  graph rebuild (server.py not found)")
        return

    if uv and reqs.exists():
        cmd_base = [str(uv), "run", "--with-requirements", str(reqs), str(server)]
    else:
        cmd_base = [sys.executable, str(server)]

    print(f"  BUILD graph...")
    subprocess.run(cmd_base + ["--build"], cwd=project_path, capture_output=True)
    subprocess.run(cmd_base + ["--visualize"], cwd=project_path, capture_output=True)
    db = project_path / ".code-graph" / "graph.db"
    size = f"{db.stat().st_size // 1024}KB" if db.exists() else "?"
    print(f"  DONE  graph.db ({size})  +  graph.html")


def main() -> None:
    if not PROJECTS_FILE.exists():
        print("projects.json not found — no projects registered.")
        return

    try:
        data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading projects.json: {e}", file=sys.stderr)
        sys.exit(1)

    projects = data.get("projects", [])
    if not projects:
        print("No projects registered in projects.json.")
        return

    print(f"Syncing {len(projects)} registered project(s)...")
    ok = 0
    for p in projects:
        print(f"\n→ {p.get('path', '(no path)')}")
        if sync_project(p):
            ok += 1

    print(f"\nSync complete: {ok}/{len(projects)} project(s) updated.")


if __name__ == "__main__":
    main()
