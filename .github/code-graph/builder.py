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
    ".xml", ".yaml", ".yml", ".sql", ".properties", ".json",
})

_IGNORE_DIRS = frozenset({
    "node_modules", ".git", ".venv", "venv", "env",
    "__pycache__", "target", "dist", "build", ".gradle",
    ".idea", ".vscode", "coverage", ".code-graph",
    ".next", ".nuxt", "out", ".turbo", ".pytest_cache",
})

_TEST_MARKERS = ("test", "spec", "__tests__", "_test", "_spec")

_JAVA_KEYWORDS = frozenset({
    'if', 'for', 'while', 'switch', 'catch', 'return', 'new', 'throw',
    'class', 'interface', 'enum', 'import', 'package', 'assert', 'super',
    'this', 'void', 'null', 'true', 'false', 'try', 'finally', 'default',
    'do', 'break', 'continue', 'case', 'else', 'instanceof', 'synchronized',
})


def _strip_generics(s: str) -> str:
    """Remove generic type parameters: 'List<String>' -> 'List'."""
    depth, result = 0, []
    for ch in s:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(0, depth - 1)
        elif depth == 0:
            result.append(ch)
    return "".join(result).strip()


def _split_java_types(raw: str) -> list[str]:
    """Split 'Foo, Bar<Baz>, Qux' into ['Foo', 'Bar', 'Qux']."""
    stripped = _strip_generics(raw)
    return [t.strip().rsplit(".", 1)[-1] for t in stripped.split(",") if t.strip()]

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
# Java parsing (dedicated parser with inheritance + annotations)
# ---------------------------------------------------------------------------

# Regex to match class/interface/enum declarations with extends/implements
_JAVA_CLASS_RE = re.compile(
    r'(?:(?:public|private|protected|abstract|final|static|strictfp)\s+)*'
    r'(class|interface|enum|@interface)\s+'
    r'(\w+)'
    r'(?:\s*<[^{]*?>)?'
    r'((?:\s+extends\s+[\w.<>,\s]+?)?)'
    r'((?:\s+implements\s+[\w.<>,\s]+?)?)'
    r'\s*\{',
    re.MULTILINE | re.DOTALL,
)

_JAVA_METHOD_RE = re.compile(
    r'(?:(?:public|private|protected|static|final|abstract|synchronized|native|default|override)\s+)+'
    r'(?:@?\w+(?:\([^)]*\))?\s+)*'
    r'(?:<[^>]+>\s+)?'
    r'[\w<>\[\]?.]+\s+'
    r'(\w+)\s*\(',
    re.MULTILINE,
)

_JAVA_ANNOTATION_RE = re.compile(r'^\s*@(\w+)', re.MULTILINE)


def _parse_java(path: Path, rel: str, nodes: list, edges: list) -> None:
    """Enhanced Java parser with inheritance, interfaces, enums, annotations."""
    text = path.read_text(encoding="utf-8", errors="ignore")

    fid = _nid("file", rel, rel)
    nodes.append((fid, "file", rel, rel, None, None))

    # --- imports (skip stdlib) ---
    for m in re.finditer(r'^import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;', text, re.MULTILINE):
        imp = m.group(1).strip()
        edges.append((fid, imp, "imports"))

    # --- class / interface / enum declarations ---
    for m in _JAVA_CLASS_RE.finditer(text):
        decl_type = m.group(1)   # class, interface, enum, @interface
        name = m.group(2)
        extends_raw = m.group(3)
        implements_raw = m.group(4)

        line = text[:m.start()].count('\n') + 1
        # Map declaration type to node kind
        kind = "class"
        if decl_type == "interface" or decl_type == "@interface":
            kind = "interface"
        elif decl_type == "enum":
            kind = "enum"

        nid = _nid(kind, rel, name)
        nodes.append((nid, kind, name, rel, line, None))
        edges.append((fid, nid, "contains"))

        # Inheritance edges
        if extends_raw and extends_raw.strip():
            raw = extends_raw.strip()
            if raw.startswith("extends"):
                raw = raw[7:].strip()
            for base in _split_java_types(raw):
                if base:
                    edges.append((nid, base, "inherits"))

        if implements_raw and implements_raw.strip():
            raw = implements_raw.strip()
            if raw.startswith("implements"):
                raw = raw[10:].strip()
            for iface in _split_java_types(raw):
                if iface:
                    edges.append((nid, iface, "implements"))

    # --- methods (avoid false positives via keyword filter) ---
    for lineno, line_text in enumerate(text.splitlines(), 1):
        for m in _JAVA_METHOD_RE.finditer(line_text):
            mname = m.group(1)
            if mname and len(mname) > 1 and mname not in _JAVA_KEYWORDS:
                mid = _nid("function", rel, f"{mname}_{lineno}")
                nodes.append((mid, "function", mname, rel, lineno, None))
                edges.append((fid, mid, "contains"))

    # --- file-level annotations (Spring stereotypes etc.) ---
    annotations = set()
    for m in _JAVA_ANNOTATION_RE.finditer(text):
        annotations.add(m.group(1))
    # Store notable annotations as a special node (for searchability)
    notable = annotations & {
        'Service', 'Repository', 'Controller', 'RestController',
        'Component', 'Configuration', 'Entity', 'Mapper',
        'SpringBootApplication', 'Audited',
    }
    if notable:
        aid = _nid("annotation", rel, ",".join(sorted(notable)))
        nodes.append((aid, "annotation", ",".join(sorted(notable)), rel, None, None))


# ---------------------------------------------------------------------------
# Structured file parsing (XML, YAML, SQL, etc.)
# ---------------------------------------------------------------------------


def _parse_structured(path: Path, rel: str, nodes: list, edges: list) -> None:
    """Parse non-source files (XML, YAML, SQL, properties, JSON) as file nodes."""
    fid = _nid("file", rel, rel)
    nodes.append((fid, "file", rel, rel, None, None))

    ext = path.suffix.lower()

    if ext == ".xml":
        _parse_xml_refs(path, rel, fid, nodes, edges)
    elif ext in (".yaml", ".yml"):
        _parse_yaml_refs(path, rel, fid, nodes, edges)
    elif ext == ".sql":
        _parse_sql_refs(path, rel, fid, nodes, edges)


def _parse_xml_refs(path: Path, rel: str, fid: str, nodes: list, edges: list) -> None:
    """Extract references from XML files (pom.xml, Spring configs, Liquibase)."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    # Liquibase: extract table names from changeSets
    for m in re.finditer(r'tableName="(\w+)"', text):
        table = m.group(1)
        tid = _nid("table", rel, table)
        nodes.append((tid, "table", table, rel, None, None))
        edges.append((fid, tid, "contains"))

    # Spring beans: class references
    for m in re.finditer(r'class="([\w.]+)"', text):
        edges.append((fid, m.group(1), "imports"))


def _parse_yaml_refs(path: Path, rel: str, fid: str, nodes: list, edges: list) -> None:
    """Extract references from YAML files (OpenAPI specs, Spring configs)."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    # OpenAPI: extract path definitions
    for m in re.finditer(r"^  (/[\w/{}\-]+):", text, re.MULTILINE):
        epath = m.group(1)
        eid = _nid("endpoint", rel, epath)
        nodes.append((eid, "endpoint", epath, rel, None, None))
        edges.append((fid, eid, "contains"))

    # $ref references to other files
    for m in re.finditer(r"\$ref:\s*['\"]?([^'\"#\s]+)", text):
        ref = m.group(1).strip()
        if ref and not ref.startswith("#"):
            edges.append((fid, ref, "imports"))


def _parse_sql_refs(path: Path, rel: str, fid: str, nodes: list, edges: list) -> None:
    """Extract table references from SQL files."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    for m in re.finditer(
        r'(?:CREATE\s+TABLE|ALTER\s+TABLE|INSERT\s+INTO|FROM|JOIN)\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
        text, re.IGNORECASE,
    ):
        table = m.group(1).lower()
        if table not in ('select', 'where', 'set', 'values', 'into', 'table'):
            tid = _nid("table", rel, table)
            nodes.append((tid, "table", table, rel, None, None))
            edges.append((fid, tid, "contains"))


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


_STRUCTURED_EXTS = frozenset({".xml", ".yaml", ".yml", ".sql", ".properties", ".json"})


def _parse_file(path: Path, rel: str, nodes: list, edges: list) -> None:
    """Route a source file to the appropriate parser."""
    if path.suffix == ".py":
        _parse_py(path, rel, nodes, edges)
    elif path.suffix == ".java":
        _parse_java(path, rel, nodes, edges)
    elif path.suffix.lower() in _STRUCTURED_EXTS:
        _parse_structured(path, rel, nodes, edges)
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
    # Build stem → [(rel, id)] index for O(1) lookup instead of O(n) scan
    by_stem: dict[str, list[tuple[str, str]]] = {}
    for rel, fid in file_map.items():
        by_stem.setdefault(Path(rel).stem, []).append((rel, fid))

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
            for known_rel, known_id in by_stem.get(imp_stem, []):
                if known_id != fid:
                    inserts.append((fid, known_id, "tests_for"))
                    break

    conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", inserts)


# ---------------------------------------------------------------------------
# File dependency resolution
# ---------------------------------------------------------------------------


def _resolve_file_deps(conn: sqlite3.Connection) -> None:
    """Resolve import strings to file→file depends_on edges.

    For Java files: uses package-path matching derived from the standard
    Maven layout (src/main/java/com/foo/Bar.java → com.foo.Bar).
    For other languages: falls back to stem-based matching.
    """
    file_nodes: dict[str, str] = {
        row[0]: row[1]
        for row in conn.execute("SELECT file, id FROM nodes WHERE kind='file'")
    }
    by_stem: dict[str, list[tuple[str, str]]] = {}
    for rel, fid in file_nodes.items():
        by_stem.setdefault(Path(rel).stem, []).append((rel, fid))

    # ---- Java package-path index ----
    # Build qualified_name → fid mapping from file paths
    java_qualified: dict[str, str] = {}   # "com.cybergrid.foo.Bar" → fid
    for rel, fid in file_nodes.items():
        if not rel.endswith(".java"):
            continue
        parts = Path(rel).parts
        # Find the "java" directory marker (after "main" or "test")
        java_marker = None
        for i, p in enumerate(parts):
            if p == "java" and i > 0 and parts[i - 1] in ("main", "test"):
                java_marker = i + 1
                break
        if java_marker and java_marker < len(parts):
            pkg_parts = list(parts[java_marker:-1])
            class_name = Path(rel).stem
            qualified = ".".join(pkg_parts + [class_name])
            java_qualified[qualified] = fid

    # ---- Resolve imports ----
    inserts: list[tuple[str, str, str]] = []
    for src_id, imp_str in conn.execute(
        "SELECT src, dst FROM edges WHERE kind='imports'"
    ):
        target_fid = None

        # 1) Java exact qualified match: "com.cybergrid.foo.Bar"
        target_fid = java_qualified.get(imp_str)

        # 2) Java static import: "com.cybergrid.foo.Bar.METHOD" → try parent
        if not target_fid and "." in imp_str:
            parent = imp_str.rsplit(".", 1)[0]
            target_fid = java_qualified.get(parent)

        # 3) Java wildcard: "com.cybergrid.foo.*" → match all in package
        if not target_fid and imp_str.endswith(".*"):
            pkg_prefix = imp_str[:-2] + "."
            for qn, fid in java_qualified.items():
                if qn.startswith(pkg_prefix) and fid != src_id:
                    inserts.append((src_id, fid, "depends_on"))
            continue

        # 4) Stem-based fallback with package-path disambiguation
        if not target_fid:
            parts = re.split(r"[./\\]", imp_str)
            stem = parts[-1] if parts else imp_str
            if stem and len(stem) >= 2:
                candidates = by_stem.get(stem, [])
                if candidates and len(candidates) <= 20:
                    # Try to match by package directory structure
                    imp_path = "/".join(parts)
                    best = None
                    for known_rel, known_id in candidates:
                        if known_id == src_id:
                            continue
                        if imp_path in known_rel:
                            best = known_id
                            break
                    if not best:
                        # Take first non-self candidate
                        for known_rel, known_id in candidates:
                            if known_id != src_id:
                                best = known_id
                                break
                    target_fid = best

        if target_fid and target_fid != src_id:
            inserts.append((src_id, target_fid, "depends_on"))

    conn.executemany("INSERT OR IGNORE INTO edges VALUES (?,?,?)", inserts)


# ---------------------------------------------------------------------------
# Inheritance resolution
# ---------------------------------------------------------------------------


def _link_inheritance(conn: sqlite3.Connection) -> None:
    """Resolve inherits/implements edges: class names → file-level edges.

    After parsing, inherits/implements edges point from a class node ID to a
    plain class name string.  This function resolves those names to actual
    class/interface nodes and creates file-level inheritance edges.
    """
    # Build class/interface/enum name → [(node_id, file)] index
    class_index: dict[str, list[tuple[str, str]]] = {}
    for nid, name, file in conn.execute(
        "SELECT id, name, file FROM nodes WHERE kind IN ('class','interface','enum')"
    ):
        class_index.setdefault(name, []).append((nid, file))

    # Build file → file_node_id mapping
    file_to_fid: dict[str, str] = {}
    for fid, file in conn.execute("SELECT id, file FROM nodes WHERE kind='file'"):
        file_to_fid[file] = fid

    inserts: list[tuple[str, str, str]] = []

    for src_id, target_name, kind in conn.execute(
        "SELECT src, dst, kind FROM edges WHERE kind IN ('inherits', 'implements')"
    ):
        candidates = class_index.get(target_name, [])
        if not candidates:
            continue

        # Find source node's file
        src_row = conn.execute("SELECT file FROM nodes WHERE id=?", (src_id,)).fetchone()
        if not src_row:
            continue
        src_file = src_row[0]
        src_fid = file_to_fid.get(src_file)

        # Pick best target: prefer same service, then any
        src_service = src_file.split("/")[0] if "/" in src_file else ""
        best_fid = None
        for target_nid, target_file in candidates:
            if target_file == src_file:
                continue  # skip self
            target_fid = file_to_fid.get(target_file)
            if not target_fid:
                continue
            target_service = target_file.split("/")[0] if "/" in target_file else ""
            best_fid = target_fid
            if target_service == src_service:
                break  # prefer same service

        if best_fid and src_fid and src_fid != best_fid:
            inserts.append((src_fid, best_fid, kind))

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

    with _timed("link inheritance"):
        _link_inheritance(conn)

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
    _link_inheritance(conn)

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
