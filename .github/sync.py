#!/usr/bin/env python3
"""Sync copilot-template updates to all registered projects.

Run from the copilot-template root (executed automatically by post-merge hook).
Reads projects.json, copies pure-template files to each registered project,
and rebuilds the code-graph + visualizer for projects with code_graph: true.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).parent.parent  # .github/sync.py -> root
PROJECTS_FILE = TEMPLATE_ROOT / "projects.json"
LOG_FILE = Path(__file__).parent / "sync.log"

# Skip these when recursively copying directories
SKIP_DIRS = {"node_modules", "__pycache__", ".code-graph"}
SKIP_SUFFIXES = {".bak", ".pyc", ".db"}

# Never overwrite these - user has customized them during initialization
SKIP_FILES = {"CLAUDE.md", "copilot-instructions.md", "config.yaml"}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s code-graph.sync %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("code-graph.sync")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_project(project: dict) -> bool:
    path = Path(project["path"])
    if not path.exists():
        log.warning("SKIP %s (path not found)", path)
        return False

    tools = set(project.get("tools", []))
    code_graph = project.get("code_graph", False)
    total = 0

    # Claude Code commands
    if "claude" in tools:
        src = TEMPLATE_ROOT / ".claude" / "commands" / "project"
        if src.exists():
            n = _copy_dir(src, path / ".claude" / "commands" / "project")
            log.info("  .claude/commands/project  %d files", n)
            total += n

    # VS Code Copilot files
    if "vscode" in tools:
        for subdir in ("agents", "skills", "prompts", "instructions"):
            src = TEMPLATE_ROOT / ".github" / subdir
            if src.exists():
                n = _copy_dir(src, path / ".github" / subdir)
                log.info("  .github/%s  %d files", subdir, n)
                total += n
        agents_md = TEMPLATE_ROOT / "AGENTS.md"
        if agents_md.exists():
            shutil.copy2(agents_md, path / "AGENTS.md")
            log.info("  AGENTS.md  1 file")
            total += 1

    # Code graph server + parsers + MCP config
    if code_graph:
        src = TEMPLATE_ROOT / ".github" / "code-graph"
        if src.exists():
            n = _copy_dir(src, path / ".github" / "code-graph")
            log.info("  .github/code-graph  %d files", n)
            total += n

        mcp_src = TEMPLATE_ROOT / ".mcp.json"
        if mcp_src.exists():
            shutil.copy2(mcp_src, path / ".mcp.json")
            log.info("  .mcp.json  1 file")
            total += 1
    elif (path / ".github" / "code-graph").exists():
        log.warning("  code_graph is false but %s has .github/code-graph/ "
                     "- set code_graph: true in projects.json to sync updates", path)

    log.info("SYNC %s - %d files updated", path, total)

    # Rebuild graph + regenerate visualizer
    if code_graph:
        _rebuild_graph(path)

    return True


def _rebuild_graph(project_path: Path) -> None:
    uv = _find_uv()
    server = project_path / ".github" / "code-graph" / "server.py"
    reqs = project_path / ".github" / "code-graph" / "requirements.txt"

    if not server.exists():
        log.warning("SKIP graph rebuild - server.py not found in %s", project_path)
        return

    if uv and reqs.exists():
        cmd_base = [str(uv), "run", "--with-requirements", str(reqs), str(server)]
        log.info("BUILD graph (uv + tree-sitter)...")
    else:
        cmd_base = [sys.executable, str(server)]
        log.info("BUILD graph (python fallback)...")

    t0 = time.perf_counter()
    result = subprocess.run(cmd_base + ["--build"], cwd=project_path, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0

    if result.returncode != 0:
        log.error("Graph build failed (%.2fs):\n%s", elapsed, result.stderr.strip())
        return

    db = project_path / ".code-graph" / "graph.db"
    size = f"{db.stat().st_size // 1024}KB" if db.exists() else "?"
    log.info("graph.db built: %s in %.2fs", size, elapsed)

    t0 = time.perf_counter()
    result = subprocess.run(cmd_base + ["--visualize"], cwd=project_path, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0

    if result.returncode != 0:
        log.error("Visualizer failed (%.2fs):\n%s", elapsed, result.stderr.strip())
    else:
        log.info("graph.html generated in %.2fs", elapsed)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _ensure_hooks() -> None:
    """Point git to .github/hooks/ so post-merge runs automatically."""
    hooks_dir = TEMPLATE_ROOT / ".github" / "hooks"
    if not hooks_dir.exists():
        return
    result = subprocess.run(
        ["git", "config", "--local", "core.hooksPath", ".github/hooks"],
        cwd=TEMPLATE_ROOT, capture_output=True, text=True,
    )
    if result.returncode == 0:
        log.info("Git hooks configured (core.hooksPath = .github/hooks)")
    else:
        log.warning("Failed to set core.hooksPath: %s", result.stderr.strip())


def main() -> None:
    _ensure_hooks()

    if not PROJECTS_FILE.exists():
        log.info("projects.json not found - no projects registered.")
        return

    try:
        data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to read projects.json: %s", e)
        sys.exit(1)

    projects = data.get("projects", [])
    if not projects:
        log.info("No projects registered in projects.json.")
        return

    log.info("Starting sync for %d registered project(s)...", len(projects))
    t_start = time.perf_counter()
    ok = 0
    for p in projects:
        log.info("=> %s", p.get("path", "(no path)"))
        if sync_project(p):
            ok += 1

    log.info("Sync complete: %d/%d project(s) updated in %.2fs",
             ok, len(projects), time.perf_counter() - t_start)


if __name__ == "__main__":
    main()
