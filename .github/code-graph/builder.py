"""Standalone code graph builder.

Parses a repository into a SQLite graph using Python's ast module for
Python files and language-specific regex patterns for everything else.

No external dependencies required beyond Python 3.10+ stdlib.
Output: .code-graph/graph.db

Languages: Python, TypeScript/TSX, JavaScript/JSX, Java, Go, Rust,
           Kotlin, Scala, Swift, PHP, C#, Ruby, Dart.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

log = logging.getLogger("code-graph.builder")


@contextmanager
def _timed(label: str):
    """Context manager that logs elapsed time for a phase."""
    t0 = time.perf_counter()
    yield
    log.info("%s completed in %.2fs", label, time.perf_counter() - t0)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id         TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,   -- file | function | method | class
    name       TEXT NOT NULL,
    file       TEXT NOT NULL,
    start_line INTEGER,
    end_line   INTEGER
);
CREATE TABLE IF NOT EXISTS edges (
    src  TEXT NOT NULL,
    dst  TEXT NOT NULL,
    kind TEXT NOT NULL          -- imports | contains | calls | tests_for
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_edges    ON edges(src, dst, kind);
CREATE INDEX       IF NOT EXISTS idx_edge_dst ON edges(dst);
CREATE INDEX       IF NOT EXISTS idx_node_file ON nodes(file);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS file_hashes (
    file TEXT PRIMARY KEY,
    sha1 TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SOURCE_EXTS = frozenset({
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".java", ".go", ".rs", ".kt", ".scala",
    ".swift", ".php", ".cs", ".rb", ".dart",
})

_IGNORE_DIRS = frozenset({
    "node_modules", ".git", ".venv", "venv", "env",
    "__pycache__", "target", "dist", "build", ".gradle",
    ".idea", ".vscode", "coverage", ".code-graph",
    ".next", ".nuxt", "out", ".turbo", ".pytest_cache",
})

_TEST_MARKERS = ("test", "spec", "__tests__", "_test", "_spec")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _nid(kind: str, file: str, name: str) -> str:
    return hashlib.sha1(f"{kind}\x00{file}\x00{name}".encode()).hexdigest()[:16]


def _walk(root: Path) -> Generator[Path, None, None]:
    for dp, dirs, files in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if d not in _IGNORE_DIRS and not d.startswith(".")
        ]
        for f in files:
            p = Path(dp) / f
            if p.suffix in _SOURCE_EXTS:
                yield p


def _is_test(rel: str) -> bool:
    lower = rel.lower()
    return any(m in lower for m in _TEST_MARKERS)


def _sha1_file(path: Path) -> str:
    """SHA-1 content hash for change detection."""
    h = hashlib.sha1(usedforsecurity=False)
    h.update(path.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Python parsing (stdlib ast — no regex needed)
# ---------------------------------------------------------------------------


def _parse_py(path: Path, rel: str, nodes: list, edges: list) -> None:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except SyntaxError:
        return

    fid = _nid("file", rel, rel)
    nodes.append((fid, "file", rel, rel, None, None))

    # Use a stack to track class nesting so we can label methods correctly
    class_stack: list[str] = []

    class _V(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                edges.append((fid, alias.name, "imports"))
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                edges.append((fid, node.module, "imports"))
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            cid = _nid("class", rel, node.name)
            nodes.append((cid, "class", node.name, rel, node.lineno, node.end_lineno))
            edges.append((fid, cid, "contains"))
            class_stack.append(node.name)
            self.generic_visit(node)
            class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            kind = "method" if class_stack else "function"
            nid = _nid(kind, rel, node.name)
            nodes.append((nid, kind, node.name, rel, node.lineno, node.end_lineno))
            edges.append((fid, nid, "contains"))
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

    _V().visit(tree)


# ---------------------------------------------------------------------------
# Regex-based parsing for other languages
# ---------------------------------------------------------------------------

_LANG: dict[str, dict[str, str]] = {
    ".ts": {
        "import":   r"""(?:import|from)\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        "function": r"""(?:^|[^.\w])(?:export\s+)?(?:async\s+)?function\s+(\w+)""",
        "class":    r"""(?:^|[^.\w])(?:export\s+)?(?:abstract\s+)?class\s+(\w+)""",
    },
    ".java": {
        "import":   r"""^import\s+([\w.]+);""",
        "function": r"""(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+(\w+)\s*\(""",
        "class":    r"""(?:public\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)""",
    },
    ".go": {
        "import":   r'''"([\w./\-]+)"''',
        "function": r"""^func\s+(?:\([^)]*\)\s+)?(\w+)\s*[(<]""",
        "class":    r"""^type\s+(\w+)\s+struct\b""",
    },
    ".rs": {
        "import":   r"""^use\s+([\w:]+)""",
        "function": r"""(?:pub(?:\([^)]*\))?\s+)?fn\s+(\w+)\s*[\(<]""",
        "class":    r"""(?:pub\s+)?struct\s+(\w+)\b""",
    },
    ".kt": {
        "import":   r"""^import\s+([\w.]+)""",
        "function": r"""(?:fun\s+)(\w+)\s*[(<]""",
        "class":    r"""(?:data\s+|sealed\s+|abstract\s+|open\s+)?class\s+(\w+)""",
    },
    ".cs": {
        "import":   r"""^using\s+([\w.]+);""",
        "function": r"""(?:public|private|protected|internal|static|async|\s)+[\w<>\[\]]+\s+(\w+)\s*\(""",
        "class":    r"""(?:public\s+)?(?:abstract\s+|sealed\s+|partial\s+)?class\s+(\w+)""",
    },
    ".rb": {
        "import":   r"""require(?:_relative)?\s+['"]([^'"]+)['"]""",
        "function": r"""^\s*def\s+(\w+)""",
        "class":    r"""^\s*class\s+(\w+)""",
    },
    ".php": {
        "import":   r"""(?:use|require|include)(?:_once)?\s+['"]?([^\s;'"(]+)""",
        "function": r"""function\s+(\w+)\s*\(""",
        "class":    r"""(?:abstract\s+)?class\s+(\w+)""",
    },
    ".swift": {
        "import":   r"""^import\s+(\w+)""",
        "function": r"""(?:func\s+)(\w+)\s*[(<]""",
        "class":    r"""(?:class|struct|actor)\s+(\w+)""",
    },
    ".dart": {
        "import":   r"""import\s+['"]([^'"]+)['"]""",
        "function": r"""(?:Future|Stream|void|int|String|bool|double|var|dynamic|[\w<>?]+)\s+(\w+)\s*\(""",
        "class":    r"""(?:abstract\s+)?class\s+(\w+)""",
    },
    ".scala": {
        "import":   r"""^import\s+([\w.{}*]+)""",
        "function": r"""def\s+(\w+)\s*[(<]""",
        "class":    r"""(?:case\s+|abstract\s+|sealed\s+)?class\s+(\w+)""",
    },
}

# Aliases for extensions that share the same patterns
for _ext in (".tsx", ".jsx", ".js"):
    _LANG.setdefault(_ext, _LANG[".ts"])


def _parse_generic(path: Path, rel: str, nodes: list, edges: list) -> None:
    pat = _LANG.get(path.suffix)
    if not pat:
        return

    fid = _nid("file", rel, rel)
    nodes.append((fid, "file", rel, rel, None, None))

    text = path.read_text(encoding="utf-8", errors="ignore")

    # Imports (scan whole file, multiline)
    for m in re.finditer(pat["import"], text, re.MULTILINE):
        val = next((g for g in m.groups() if g), None)
        if val:
            edges.append((fid, val.strip(), "imports"))

    # Functions and classes (line-by-line for line number tracking)
    for lineno, line in enumerate(text.splitlines(), 1):
        for key, kind in (("class", "class"), ("function", "function")):
            for m in re.finditer(pat[key], line):
                val = next((g for g in m.groups() if g), None)
                if val and len(val) > 1:  # skip single-char matches
                    nid = _nid(kind, rel, val)
                    nodes.append((nid, kind, val, rel, lineno, None))
                    edges.append((fid, nid, "contains"))


# ---------------------------------------------------------------------------
# File dispatch
# ---------------------------------------------------------------------------


def _parse_file(path: Path, rel: str, nodes: list, edges: list) -> None:
    """Route a source file to the appropriate parser."""
    if path.suffix == ".py":
        _parse_py(path, rel, nodes, edges)
    else:
        _parse_generic(path, rel, nodes, edges)


# ---------------------------------------------------------------------------
# Test association
# ---------------------------------------------------------------------------


def _link_tests(conn: sqlite3.Connection) -> None:
    """Add tests_for edges: test_file → source_file it imports/references."""
    file_map: dict[str, str] = {
        row[0]: row[1]
        for row in conn.execute("SELECT file, id FROM nodes WHERE kind='file'")
    }
    inserts: list[tuple[str, str, str]] = []

    for rel, fid in file_map.items():
        if not _is_test(rel):
            continue
        for (imp,) in conn.execute(
            "SELECT dst FROM edges WHERE src=? AND kind='imports'", (fid,)
        ):
            # Match import string to a known source file by stem/module path
            imp_parts = re.split(r"[./\\]", imp)
            imp_stem = imp_parts[-1] if imp_parts else imp
            for known_rel, known_id in file_map.items():
                if known_id == fid:
                    continue
                stem = Path(known_rel).stem
                if imp_stem == stem or imp.endswith(f"/{stem}") or imp.endswith(f".{stem}"):
                    inserts.append((fid, known_id, "tests_for"))
                    break

    conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", inserts)


# ---------------------------------------------------------------------------
# File dependency resolution
# ---------------------------------------------------------------------------


def _resolve_file_deps(conn: sqlite3.Connection) -> None:
    """Resolve import strings to file→file depends_on edges.

    Matches import-path stems to known file stems.  Skips ambiguous stems
    with more than five candidates to reduce false positives.
    """
    file_nodes: dict[str, str] = {
        row[0]: row[1]
        for row in conn.execute("SELECT file, id FROM nodes WHERE kind='file'")
    }
    by_stem: dict[str, list[tuple[str, str]]] = {}
    for rel, fid in file_nodes.items():
        by_stem.setdefault(Path(rel).stem, []).append((rel, fid))

    inserts: list[tuple[str, str, str]] = []
    for src_id, imp_str in conn.execute(
        "SELECT src, dst FROM edges WHERE kind='imports'"
    ):
        parts = re.split(r"[./\\]", imp_str)
        stem = parts[-1] if parts else imp_str
        if not stem or len(stem) < 2:
            continue
        candidates = by_stem.get(stem, [])
        if not candidates or len(candidates) > 5:
            continue
        for known_rel, known_id in candidates:
            if known_id != src_id:
                inserts.append((src_id, known_id, "depends_on"))
                break

    conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", inserts)


# ---------------------------------------------------------------------------
# Graph traversal
# ---------------------------------------------------------------------------


def _find_dependents(conn: sqlite3.Connection, rels: list[str]) -> list[str]:
    """Find files that depend on any of the given files (1-hop reverse)."""
    seed_ids: set[str] = set()
    for rel in rels:
        row = conn.execute(
            "SELECT id FROM nodes WHERE file=? AND kind='file'", (rel,)
        ).fetchone()
        if row:
            seed_ids.add(row[0])

    if not seed_ids:
        return []

    dependent_rels: set[str] = set()
    for sid in seed_ids:
        for (src_id,) in conn.execute(
            "SELECT src FROM edges WHERE dst=? AND kind='depends_on'", (sid,)
        ):
            row = conn.execute(
                "SELECT file FROM nodes WHERE id=?", (src_id,)
            ).fetchone()
            if row and row[0] not in rels:
                dependent_rels.add(row[0])

    return list(dependent_rels)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build(root: Path) -> Path:
    """Full rebuild: parse every source file in root into .code-graph/graph.db."""
    build_start = time.perf_counter()
    log.info("Starting full graph build for %s", root)

    db_dir = root / ".code-graph"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "graph.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)

    # Full rebuild: clear existing data
    conn.execute("DELETE FROM nodes")
    conn.execute("DELETE FROM edges")
    conn.execute("DELETE FROM file_hashes")
    conn.commit()

    all_nodes: list[tuple] = []
    all_edges: list[tuple] = []
    all_hashes: list[tuple] = []
    file_count = 0

    with _timed("parse files"):
        for path in _walk(root):
            rel = str(path.relative_to(root))
            _parse_file(path, rel, all_nodes, all_edges)
            all_hashes.append((rel, _sha1_file(path)))
            file_count += 1
    log.info("Parsed %d files (%d nodes, %d edges)", file_count, len(all_nodes), len(all_edges))

    with _timed("write nodes/edges"):
        # Batch insert — dedup edges via UNIQUE index
        conn.executemany("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?)", all_nodes)
        conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", all_edges)
        conn.executemany("INSERT OR REPLACE INTO file_hashes VALUES (?,?)", all_hashes)

    with _timed("link tests"):
        _link_tests(conn)

    with _timed("resolve file deps"):
        _resolve_file_deps(conn)

    conn.execute("INSERT OR REPLACE INTO meta VALUES ('root',?)", (str(root),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('files_parsed',?)", (str(file_count),))
    conn.commit()
    conn.close()

    elapsed = time.perf_counter() - build_start
    log.info("Graph built: %d files → %s (%.2fs total)", file_count, db_path, elapsed)
    print(f"Graph built: {file_count} files → {db_path} ({elapsed:.2f}s)")
    return db_path


def update(root: Path) -> tuple[Path, list[str]]:
    """Incremental update: re-parse changed files + their 1-hop dependents.

    Uses SHA-1 content hashes to detect changes (not timestamps).
    Removes nodes/edges for deleted files automatically.
    Also re-parses files that import from any changed file so that
    cross-file edges (calls, tests_for) stay accurate.

    Returns (db_path, list_of_updated_relative_paths).
    """
    update_start = time.perf_counter()
    db_path = root / ".code-graph" / "graph.db"
    if not db_path.exists():
        return build(root), []

    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)  # idempotent — adds file_hashes if missing

    stored: dict[str, str] = {
        row[0]: row[1] for row in conn.execute("SELECT file, sha1 FROM file_hashes")
    }

    current_rels: set[str] = set()
    changed: list[str] = []

    for path in _walk(root):
        rel = str(path.relative_to(root))
        current_rels.add(rel)
        if stored.get(rel) != _sha1_file(path):
            changed.append(rel)

    deleted = set(stored) - current_rels

    if not changed and not deleted:
        conn.close()
        print("Graph up to date — no changes detected.")
        return db_path, []

    # Expand: also re-parse files that import from changed/deleted files
    dependents = _find_dependents(conn, changed + list(deleted))
    # Only include dependents that still exist on disk
    dependents = [d for d in dependents if d in current_rels and d not in changed]

    to_reparse = changed + dependents

    # Remove old data for changed + deleted + dependent files
    for rel in (*to_reparse, *deleted):
        fid_rows = conn.execute(
            "SELECT id FROM nodes WHERE file=? AND kind='file'", (rel,)
        ).fetchall()
        for (fid,) in fid_rows:
            conn.execute("DELETE FROM edges WHERE src=? OR dst=?", (fid, fid))
        conn.execute("DELETE FROM nodes WHERE file=?", (rel,))
        conn.execute("DELETE FROM file_hashes WHERE file=?", (rel,))

    all_nodes: list[tuple] = []
    all_edges: list[tuple] = []

    for rel in to_reparse:
        path = root / rel
        if not path.exists():
            continue
        _parse_file(path, rel, all_nodes, all_edges)
        conn.execute(
            "INSERT OR REPLACE INTO file_hashes VALUES (?,?)", (rel, _sha1_file(path))
        )

    conn.executemany("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?)", all_nodes)
    conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", all_edges)

    _link_tests(conn)
    _resolve_file_deps(conn)

    conn.execute(
        "INSERT OR REPLACE INTO meta VALUES ('files_parsed',?)",
        (str(len(current_rels)),),
    )
    conn.commit()
    conn.close()

    elapsed = time.perf_counter() - update_start
    summary = f"updated {len(changed)}, dependents {len(dependents)}, deleted {len(deleted)}"
    log.info("Graph updated: %s (%.2fs)", summary, elapsed)
    print(f"Graph updated: {summary} → {db_path} ({elapsed:.2f}s)")
    return db_path, changed
