"""
Tree-sitter code parser.
Extracts functions, classes, imports from Python, JS/TS source files.
Each function → one chunk (the right granularity for embeddings).
"""
from __future__ import annotations
from typing import List, Dict, Optional, Any
import structlog

log = structlog.get_logger()


def _safe_text(node, source: bytes) -> str:
    try:
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _get_docstring(node, source: bytes) -> Optional[str]:
    """Extract first string literal as docstring (Python)."""
    for child in node.children:
        if child.type == "block":
            for stmt in child.children:
                if stmt.type == "expression_statement":
                    for s in stmt.children:
                        if s.type == "string":
                            raw = _safe_text(s, source)
                            return raw.strip('"""\'').strip()
    return None


class ParsedFile:
    def __init__(self, path: str, language: str):
        self.path = path
        self.language = language
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[str] = []
        self.imports: List[Dict[str, Any]] = []


def parse_python(source: bytes, path: str) -> ParsedFile:
    """Parse Python source using tree-sitter-python."""
    result = ParsedFile(path, "python")
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser

        PY_LANGUAGE = Language(tspython.language())
        parser = Parser(PY_LANGUAGE)
        tree = parser.parse(source)
        root = tree.root_node

        def walk(node, current_class=None):
            if node.type == "class_definition":
                class_name = None
                for child in node.children:
                    if child.type == "identifier":
                        class_name = _safe_text(child, source)
                        result.classes.append(class_name)
                        break
                for child in node.children:
                    walk(child, class_name)

            elif node.type == "function_definition":
                fn_name = None
                params = []
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                is_async = False
                for child in node.children:
                    if child.type == "identifier" and fn_name is None:
                        fn_name = _safe_text(child, source)
                    elif child.type == "parameters":
                        for p in child.children:
                            if p.type == "identifier":
                                params.append(_safe_text(p, source))

                if fn_name:
                    body = _safe_text(node, source)
                    docstring = _get_docstring(node, source)
                    result.functions.append({
                        "name": fn_name,
                        "class_name": current_class,
                        "start_line": start_line,
                        "end_line": end_line,
                        "body": body[:4000],  # cap at 4000 chars
                        "docstring": docstring,
                        "parameters": params,
                        "is_async": is_async,
                    })

            elif node.type == "import_statement":
                module = None
                for child in node.children:
                    if child.type == "dotted_name" or child.type == "identifier":
                        module = _safe_text(child, source)
                        break
                if module:
                    result.imports.append({
                        "module": module,
                        "names": [],
                        "is_relative": False,
                    })

            elif node.type == "import_from_statement":
                module = None
                names = []
                is_relative = False
                for child in node.children:
                    if child.type == "dotted_name":
                        module = _safe_text(child, source)
                    elif child.type == "relative_import":
                        is_relative = True
                        for sub in child.children:
                            if sub.type == "dotted_name":
                                module = _safe_text(sub, source)
                    elif child.type == "import_from_names":
                        for sub in child.children:
                            if sub.type == "identifier":
                                names.append(_safe_text(sub, source))
                if module:
                    result.imports.append({
                        "module": module,
                        "names": names,
                        "is_relative": is_relative,
                    })

            else:
                for child in node.children:
                    walk(child, current_class)

        walk(root)
    except Exception as e:
        log.warning("Python parse error", path=path, error=str(e))

    return result


def parse_javascript(source: bytes, path: str, language: str = "javascript") -> ParsedFile:
    """Parse JS/TS using tree-sitter-javascript."""
    result = ParsedFile(path, language)
    try:
        import tree_sitter_javascript as tsjs
        from tree_sitter import Language, Parser

        JS_LANGUAGE = Language(tsjs.language())
        parser = Parser(JS_LANGUAGE)
        tree = parser.parse(source)
        root = tree.root_node

        def walk(node, current_class=None):
            if node.type in ("class_declaration", "class"):
                for child in node.children:
                    if child.type == "identifier":
                        class_name = _safe_text(child, source)
                        result.classes.append(class_name)
                        break
                for child in node.children:
                    walk(child, current_class)

            elif node.type in (
                "function_declaration", "function",
                "arrow_function", "method_definition",
            ):
                fn_name = None
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                for child in node.children:
                    if child.type in ("identifier", "property_identifier") and fn_name is None:
                        fn_name = _safe_text(child, source)

                fn_name = fn_name or "<anonymous>"
                body = _safe_text(node, source)
                result.functions.append({
                    "name": fn_name,
                    "class_name": current_class,
                    "start_line": start_line,
                    "end_line": end_line,
                    "body": body[:4000],
                    "docstring": None,
                    "parameters": [],
                    "is_async": "async" in _safe_text(node, source)[:20],
                })

            elif node.type == "import_statement":
                module = None
                names = []
                for child in node.children:
                    if child.type == "string":
                        module = _safe_text(child, source).strip("'\"")
                    elif child.type == "import_clause":
                        for sub in child.children:
                            if sub.type == "identifier":
                                names.append(_safe_text(sub, source))
                if module:
                    result.imports.append({"module": module, "names": names, "is_relative": module.startswith(".")})

            else:
                for child in node.children:
                    walk(child, current_class)

        walk(root)
    except Exception as e:
        log.warning("JS/TS parse error", path=path, error=str(e))

    return result


def parse_file(full_path: str, rel_path: str, language: str) -> ParsedFile:
    """Dispatch to the right parser."""
    try:
        with open(full_path, "rb") as f:
            source = f.read()
    except Exception as e:
        log.warning("Cannot read file", path=full_path, error=str(e))
        return ParsedFile(rel_path, language)

    if language == "python":
        return parse_python(source, rel_path)
    elif language in ("javascript", "typescript"):
        return parse_javascript(source, rel_path, language)
    else:
        return ParsedFile(rel_path, language)
