"""Tree-sitter parser — accurate AST parsing for all supported languages.

Registers under stack "tree_sitter" and overrides regex parsers for any
extension whose language package is installed.  Uninstalled languages fall
back to the existing regex parsers automatically.

Install language packages:
    uv add tree-sitter>=0.22 \\
           tree-sitter-python tree-sitter-javascript tree-sitter-typescript \\
           tree-sitter-java tree-sitter-go tree-sitter-rust tree-sitter-ruby \\
           tree-sitter-c-sharp tree-sitter-php tree-sitter-kotlin
"""
from __future__ import annotations

import importlib
from pathlib import Path

from . import register, nid

# ---------------------------------------------------------------------------
# Core availability check
# ---------------------------------------------------------------------------

try:
    from tree_sitter import Language, Parser
    _CORE_OK = True
except ImportError:
    _CORE_OK = False

if not _CORE_OK:
    pass  # nothing to register — regex parsers handle everything
else:
    # -----------------------------------------------------------------------
    # Language loader (lazy, one Language object per extension)
    # -----------------------------------------------------------------------

    # ext -> (package_name, function_name_on_package)
    _PKG_MAP: dict[str, tuple[str, str]] = {
        '.py':  ('tree_sitter_python',     'language'),
        '.js':  ('tree_sitter_javascript', 'language'),
        '.jsx': ('tree_sitter_javascript', 'language'),
        '.ts':  ('tree_sitter_typescript', 'language_typescript'),
        '.tsx': ('tree_sitter_typescript', 'language_tsx'),
        '.java':('tree_sitter_java',       'language'),
        '.kt':  ('tree_sitter_kotlin',     'language'),
        '.go':  ('tree_sitter_go',         'language'),
        '.rs':  ('tree_sitter_rust',       'language'),
        '.rb':  ('tree_sitter_ruby',       'language'),
        '.cs':  ('tree_sitter_c_sharp',    'language'),
        '.php': ('tree_sitter_php',        'language_php'),
    }

    _lang_cache: dict[str, Language | None] = {}

    def _get_lang(ext: str) -> Language | None:
        if ext not in _lang_cache:
            entry = _PKG_MAP.get(ext)
            if not entry:
                _lang_cache[ext] = None
            else:
                pkg, fn = entry
                try:
                    mod = importlib.import_module(pkg)
                    _lang_cache[ext] = Language(getattr(mod, fn)())
                except Exception:
                    _lang_cache[ext] = None
        return _lang_cache[ext]

    # Probe which language packages are actually installed
    _supported: set[str] = {ext for ext in _PKG_MAP if _get_lang(ext) is not None}

    if not _supported:
        pass  # no language packages found — nothing to register
    else:
        # -------------------------------------------------------------------
        # AST helpers
        # -------------------------------------------------------------------

        def _txt(node, src: bytes) -> str:
            return src[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')

        def _field(node, field: str, src: bytes) -> str | None:
            child = node.child_by_field_name(field)
            return _txt(child, src) if child else None

        def _ancestor(node, types: frozenset[str]):
            """Walk the parent chain and return the nearest node whose type is in types."""
            p = node.parent
            while p:
                if p.type in types:
                    return p
                p = p.parent
            return None

        def _walk(root):
            """Iterative depth-first traversal."""
            stack = [root]
            while stack:
                node = stack.pop()
                yield node
                stack.extend(reversed(node.children))

        # Python builtins — skip these in call extraction to reduce noise
        _BUILTINS_PY = frozenset({
            'print', 'len', 'range', 'str', 'int', 'float', 'bool', 'list',
            'dict', 'set', 'tuple', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'super', 'enumerate', 'zip', 'map', 'filter', 'sorted',
            'reversed', 'open', 'repr', 'format', 'any', 'all', 'min', 'max',
            'sum', 'abs', 'vars', 'dir', 'id', 'hash', 'iter', 'next',
            'callable', 'staticmethod', 'classmethod', 'property', 'object',
        })

        def _calls_python(fn_node, src: bytes, fn_types: frozenset) -> set[str]:
            """Extract callee names from a Python function node.

            Does not descend into nested function/class definitions.
            Only resolves simple names and self.method() calls.
            """
            calls: set[str] = set()

            def _visit(node):
                for child in node.children:
                    if child.type in fn_types or child.type == 'class_definition':
                        continue  # stop at nested scopes
                    if child.type == 'call':
                        fn_child = child.child_by_field_name('function')
                        if fn_child:
                            if fn_child.type == 'identifier':
                                name = _txt(fn_child, src)
                                if (name
                                        and not (name.startswith('__') and name.endswith('__'))
                                        and name not in _BUILTINS_PY):
                                    calls.add(name)
                            elif fn_child.type == 'attribute':
                                obj = fn_child.child_by_field_name('object')
                                attr = fn_child.child_by_field_name('attribute')
                                if obj and attr and _txt(obj, src) == 'self':
                                    name = _txt(attr, src)
                                    if name and not (name.startswith('__') and name.endswith('__')):
                                        calls.add(name)
                    _visit(child)

            _visit(fn_node)
            return calls

        # -------------------------------------------------------------------
        # Import extractors (per language)
        # -------------------------------------------------------------------

        def _imports_python(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'import_statement':
                    for ch in node.children:
                        if ch.type == 'dotted_name':
                            edges.append((fid, _txt(ch, src), 'imports'))
                        elif ch.type == 'aliased_import':
                            n = ch.child_by_field_name('name')
                            if n:
                                edges.append((fid, _txt(n, src), 'imports'))
                elif node.type == 'import_from_statement':
                    m = node.child_by_field_name('module_name')
                    if m:
                        edges.append((fid, _txt(m, src), 'imports'))

        def _imports_js(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'import_statement':
                    src_node = node.child_by_field_name('source')
                    if src_node:
                        for ch in src_node.children:
                            if ch.type == 'string_fragment':
                                edges.append((fid, _txt(ch, src), 'imports'))
                elif node.type == 'call_expression':
                    fn = node.child_by_field_name('function')
                    if fn and _txt(fn, src) == 'require':
                        args = node.child_by_field_name('arguments')
                        if args:
                            for ch in _walk(args):
                                if ch.type == 'string_fragment':
                                    edges.append((fid, _txt(ch, src), 'imports'))
                                    break

        def _imports_java(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'import_declaration':
                    for ch in node.children:
                        if ch.type in ('scoped_identifier', 'identifier', 'asterisk'):
                            if ch.type != 'asterisk':
                                edges.append((fid, _txt(ch, src), 'imports'))

        def _imports_go(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'import_spec':
                    path_node = node.child_by_field_name('path')
                    if path_node:
                        val = _txt(path_node, src).strip('"\'`')
                        edges.append((fid, val, 'imports'))

        def _imports_rust(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'use_declaration':
                    arg = node.child_by_field_name('argument')
                    if arg:
                        edges.append((fid, _txt(arg, src), 'imports'))

        def _imports_ruby(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'call' and _field(node, 'method', src) in ('require', 'require_relative'):
                    args = node.child_by_field_name('arguments')
                    if args:
                        for ch in _walk(args):
                            if ch.type == 'string_content':
                                edges.append((fid, _txt(ch, src), 'imports'))
                                break

        def _imports_cs(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'using_directive':
                    name = node.child_by_field_name('name')
                    if name:
                        edges.append((fid, _txt(name, src), 'imports'))

        def _imports_php(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'namespace_use_declaration':
                    for ch in _walk(node):
                        if ch.type == 'namespace_use_clause':
                            n = ch.child_by_field_name('name')
                            if n:
                                edges.append((fid, _txt(n, src).replace('\\', '.'), 'imports'))

        def _imports_kotlin(root, src, fid, edges):
            for node in _walk(root):
                if node.type == 'import_header':
                    idn = node.child_by_field_name('identifier')
                    if idn:
                        edges.append((fid, _txt(idn, src), 'imports'))

        # -------------------------------------------------------------------
        # Language config table
        # -------------------------------------------------------------------
        # class_types: AST node types that represent class/struct/interface/enum
        # fn_types:    AST node types that represent functions/methods
        # import_fn:   callable(root, src, fid, edges)

        _CFG: dict[str, dict] = {
            '.py': dict(
                class_types=frozenset({'class_definition'}),
                fn_types=frozenset({'function_definition'}),
                import_fn=_imports_python,
            ),
            '.js': dict(
                class_types=frozenset({'class_declaration', 'class'}),
                fn_types=frozenset({'function_declaration', 'method_definition'}),
                import_fn=_imports_js,
            ),
            '.ts': dict(
                class_types=frozenset({'class_declaration', 'class', 'abstract_class_declaration'}),
                fn_types=frozenset({'function_declaration', 'method_definition'}),
                import_fn=_imports_js,
            ),
            '.java': dict(
                class_types=frozenset({'class_declaration', 'interface_declaration',
                                       'enum_declaration', 'record_declaration',
                                       'annotation_type_declaration'}),
                fn_types=frozenset({'method_declaration', 'constructor_declaration'}),
                import_fn=_imports_java,
            ),
            '.kt': dict(
                class_types=frozenset({'class_declaration', 'object_declaration',
                                       'interface_declaration'}),
                fn_types=frozenset({'function_declaration'}),
                import_fn=_imports_kotlin,
            ),
            '.go': dict(
                class_types=frozenset({'type_declaration'}),   # handled specially
                fn_types=frozenset({'function_declaration', 'method_declaration'}),
                import_fn=_imports_go,
            ),
            '.rs': dict(
                class_types=frozenset({'struct_item', 'enum_item', 'trait_item'}),
                fn_types=frozenset({'function_item'}),
                import_fn=_imports_rust,
            ),
            '.rb': dict(
                class_types=frozenset({'class', 'module'}),
                fn_types=frozenset({'method', 'singleton_method'}),
                import_fn=_imports_ruby,
            ),
            '.cs': dict(
                class_types=frozenset({'class_declaration', 'interface_declaration',
                                       'enum_declaration', 'struct_declaration',
                                       'record_declaration'}),
                fn_types=frozenset({'method_declaration', 'constructor_declaration',
                                    'operator_declaration'}),
                import_fn=_imports_cs,
            ),
            '.php': dict(
                class_types=frozenset({'class_declaration', 'interface_declaration',
                                       'trait_declaration', 'enum_declaration'}),
                fn_types=frozenset({'method_declaration', 'function_definition'}),
                import_fn=_imports_php,
            ),
        }
        _CFG['.jsx'] = _CFG['.js']
        _CFG['.tsx'] = _CFG['.ts']

        # kind overrides for specific AST types
        _KIND_OVERRIDE: dict[str, str] = {
            'interface_declaration': 'interface',
            'interface': 'interface',
            'trait_item': 'interface',
            'trait_declaration': 'interface',
            'annotation_type_declaration': 'interface',
            'enum_declaration': 'enum',
            'enum_item': 'enum',
        }

        # -------------------------------------------------------------------
        # Core parse function
        # -------------------------------------------------------------------

        def _parse_file(path: Path, rel: str, nodes: list, edges: list) -> None:
            ext = path.suffix.lower()
            lang = _get_lang(ext)
            cfg = _CFG.get(ext)
            if lang is None or cfg is None:
                nodes.append((nid("file", rel, rel), "file", rel, rel, None, None))
                return

            try:
                src = path.read_bytes()
            except OSError:
                return

            tree = Parser(lang).parse(src)
            root = tree.root_node

            fid = nid("file", rel, rel)
            nodes.append((fid, "file", rel, rel, None, None))

            class_types = cfg['class_types']
            fn_types = cfg['fn_types']

            # ---- Pass 1: classes / structs / interfaces / enums ----
            for node in _walk(root):
                if node.type not in class_types:
                    continue

                # Go: type_declaration wraps type_spec which wraps struct/interface
                if ext == '.go' and node.type == 'type_declaration':
                    for spec in node.children:
                        if spec.type != 'type_spec':
                            continue
                        name_node = spec.child_by_field_name('name')
                        type_node = spec.child_by_field_name('type')
                        if not name_node or not type_node:
                            continue
                        name = _txt(name_node, src)
                        kind = 'interface' if type_node.type == 'interface_type' else 'class'
                        cls_id = nid(kind, rel, name)
                        nodes.append((cls_id, kind, name, rel,
                                      node.start_point[0] + 1, node.end_point[0] + 1))
                        edges.append((fid, cls_id, 'contains'))
                    continue

                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                name = _txt(name_node, src)
                if not name or len(name) < 2:
                    continue

                kind = _KIND_OVERRIDE.get(node.type, 'class')
                cls_id = nid(kind, rel, name)
                nodes.append((cls_id, kind, name, rel,
                              node.start_point[0] + 1, node.end_point[0] + 1))
                edges.append((fid, cls_id, 'contains'))

                # Inheritance edges
                if ext == '.py':
                    superclasses = node.child_by_field_name('superclasses')
                    if superclasses:
                        for ch in superclasses.children:
                            if ch.type == 'identifier':
                                edges.append((cls_id, _txt(ch, src), 'inherits'))
                elif ext in ('.java', '.kt', '.cs', '.php'):
                    for ch in _walk(node):
                        if ch.type == 'super_interfaces' or ch.type == 'extends_interfaces':
                            for tn in _walk(ch):
                                if tn.type == 'type_identifier':
                                    edges.append((cls_id, _txt(tn, src), 'inherits'))
                        elif ch.type == 'superclass':
                            for tn in _walk(ch):
                                if tn.type == 'type_identifier':
                                    edges.append((cls_id, _txt(tn, src), 'inherits'))

            # ---- Pass 2: functions / methods ----
            for node in _walk(root):
                if node.type not in fn_types:
                    continue

                # Go method_declaration: receiver determines the struct owner
                if ext == '.go' and node.type == 'method_declaration':
                    name_node = node.child_by_field_name('name')
                    recv = node.child_by_field_name('receiver')
                    if not name_node or not recv:
                        continue
                    name = _txt(name_node, src)
                    receiver_type = None
                    for ch in _walk(recv):
                        if ch.type == 'type_identifier':
                            receiver_type = _txt(ch, src)
                            break
                    if receiver_type:
                        fn_nid = nid("method", rel, f"{receiver_type}.{name}")
                        nodes.append((fn_nid, "method", name, rel,
                                      node.start_point[0] + 1, node.end_point[0] + 1))
                        edges.append((nid("class", rel, receiver_type), fn_nid, 'contains'))
                    else:
                        fn_nid = nid("function", rel, name)
                        nodes.append((fn_nid, "function", name, rel,
                                      node.start_point[0] + 1, node.end_point[0] + 1))
                        edges.append((fid, fn_nid, 'contains'))
                    continue

                # Rust: functions inside impl blocks are methods
                if ext == '.rs':
                    impl_anc = _ancestor(node, frozenset({'impl_item'}))
                    name_node = node.child_by_field_name('name')
                    if not name_node:
                        continue
                    name = _txt(name_node, src)
                    if not name or len(name) < 2:
                        continue
                    if impl_anc:
                        type_node = impl_anc.child_by_field_name('type')
                        struct_name = _txt(type_node, src) if type_node else None
                        if struct_name:
                            # impl Trait for Struct — use the struct, not the trait
                            fn_nid = nid("method", rel, f"{struct_name}.{name}")
                            nodes.append((fn_nid, "method", name, rel,
                                          node.start_point[0] + 1, node.end_point[0] + 1))
                            edges.append((nid("class", rel, struct_name), fn_nid, 'contains'))
                            continue
                    fn_nid = nid("function", rel, f"{name}_{node.start_point[0]+1}")
                    nodes.append((fn_nid, "function", name, rel,
                                  node.start_point[0] + 1, node.end_point[0] + 1))
                    edges.append((fid, fn_nid, 'contains'))
                    continue

                # General case: check for enclosing class ancestor
                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                name = _txt(name_node, src)
                if not name or len(name) < 2:
                    continue

                cls_anc = _ancestor(node, class_types)
                if cls_anc is not None:
                    cls_name_node = cls_anc.child_by_field_name('name')
                    cls_name = _txt(cls_name_node, src) if cls_name_node else None
                    if cls_name:
                        fn_nid = nid("method", rel, f"{cls_name}.{name}")
                        nodes.append((fn_nid, "method", name, rel,
                                      node.start_point[0] + 1, node.end_point[0] + 1))
                        edges.append((nid("class", rel, cls_name), fn_nid, 'contains'))
                        continue

                # Top-level function
                fn_nid = nid("function", rel, f"{name}_{node.start_point[0]+1}")
                nodes.append((fn_nid, "function", name, rel,
                              node.start_point[0] + 1, node.end_point[0] + 1))
                edges.append((fid, fn_nid, 'contains'))

            # ---- Pass 3: calls (Python only) ----
            if ext == '.py':
                for fn_node in _walk(root):
                    if fn_node.type not in fn_types:
                        continue
                    name_node = fn_node.child_by_field_name('name')
                    if not name_node:
                        continue
                    fn_name = _txt(name_node, src)
                    if not fn_name or len(fn_name) < 2:
                        continue
                    cls_anc = _ancestor(fn_node, class_types)
                    if cls_anc:
                        cls_name_node = cls_anc.child_by_field_name('name')
                        cls_name = _txt(cls_name_node, src) if cls_name_node else None
                        if not cls_name:
                            continue
                        fn_nid = nid("method", rel, f"{cls_name}.{fn_name}")
                    else:
                        fn_nid = nid("function", rel, f"{fn_name}_{fn_node.start_point[0]+1}")
                    for callee in _calls_python(fn_node, src, fn_types):
                        edges.append((fn_nid, callee, 'calls'))

            # ---- Imports ----
            cfg['import_fn'](root, src, fid, edges)

        # -------------------------------------------------------------------
        # Register under "tree_sitter" stack
        # -------------------------------------------------------------------

        STACK = "tree_sitter"
        EXTENSIONS = frozenset(_supported)
        register(STACK, EXTENSIONS)(_parse_file)
