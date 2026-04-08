"""Python parser — uses stdlib ast for accurate parsing."""

from __future__ import annotations

import ast
from pathlib import Path

from . import register, nid

STACK = "python"
EXTENSIONS = frozenset({".py"})


@register(STACK, EXTENSIONS)
def parse(path: Path, rel: str, nodes: list, edges: list) -> None:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except SyntaxError:
        return

    fid = nid("file", rel, rel)
    nodes.append((fid, "file", rel, rel, None, None))

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
            cid = nid("class", rel, node.name)
            nodes.append((cid, "class", node.name, rel, node.lineno, node.end_lineno))
            edges.append((fid, cid, "contains"))
            # Inheritance
            for base in node.bases:
                base_name = _resolve_name(base)
                if base_name:
                    edges.append((cid, base_name, "inherits"))
            class_stack.append(node.name)
            self.generic_visit(node)
            class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            kind = "method" if class_stack else "function"
            func_nid = nid(kind, rel, node.name)
            nodes.append((func_nid, kind, node.name, rel, node.lineno, node.end_lineno))
            edges.append((fid, func_nid, "contains"))
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

    _V().visit(tree)


def _resolve_name(node: ast.expr) -> str | None:
    """Extract a dotted name from an AST node (e.g. base class)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _resolve_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None
