import ast
import json
from pathlib import Path
from typing import Any, Dict, List

INDEX_FILE = ".hallucheck-index.json"


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.symbols: Dict[str, List[Dict[str, Any]]] = {}
        self.current_class = None

    def add_symbol(self, name: str, line: int, kind: str, parent_class: str = None):
        if name not in self.symbols:
            self.symbols[name] = []
        self.symbols[name].append(
            {"file": self.filepath, "line": line, "kind": kind, "parent_class": parent_class}
        )

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_symbol(node.name, node.lineno, "class")
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        kind = "method" if self.current_class else "function"

        # Check if it's a property
        is_property = any(
            isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
        )
        if is_property:
            kind = "property"

        self.add_symbol(node.name, node.lineno, kind, self.current_class)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_symbol(target.id, node.lineno, "variable", self.current_class)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.add_symbol(node.target.id, node.lineno, "variable", self.current_class)
        self.generic_visit(node)


def build_index(root_path: str = ".") -> Dict[str, List[Dict[str, Any]]]:
    root = Path(root_path)
    index = {}

    for py_file in root.rglob("*.py"):
        # skip virtual environments and hidden dirs
        if any(part.startswith(".") for part in py_file.parts) and not str(py_file).startswith(
            "./.hallucheck"
        ):
            if not str(py_file).startswith("./"):
                continue
            # Need a more robust check for hidden files, but we'll ignore '.git', '.venv', etc.
            if any(part.startswith(".") and part not in [".", ".."] for part in py_file.parts):
                continue

        # Don't index site-packages or venv
        if "site-packages" in py_file.parts or "venv" in py_file.parts or "env" in py_file.parts:
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(py_file))

            # Extract module paths as symbols too
            # e.g., if file is auth/models.py, module is auth.models
            rel_path = py_file.relative_to(root)
            if rel_path.stem != "__init__":
                module_parts = list(rel_path.parent.parts) + [rel_path.stem]
            else:
                module_parts = list(rel_path.parent.parts)

            module_name = ".".join(module_parts)
            if module_name:
                if module_name not in index:
                    index[module_name] = []
                index[module_name].append(
                    {"file": str(rel_path), "line": 1, "kind": "module", "parent_class": None}
                )

            visitor = SymbolVisitor(str(rel_path))
            visitor.visit(tree)

            for name, entries in visitor.symbols.items():
                if name not in index:
                    index[name] = []
                index[name].extend(entries)

        except Exception:
            # Skip files that can't be parsed
            continue

    return index


def save_index(index: Dict[str, List[Dict[str, Any]]], path: str = "."):
    index_path = Path(path) / INDEX_FILE
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def load_index(path: str = ".") -> Dict[str, List[Dict[str, Any]]]:
    index_path = Path(path) / INDEX_FILE
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def should_rebuild_index(path: str = ".") -> bool:
    root = Path(path)
    index_path = root / INDEX_FILE

    if not index_path.exists():
        return True

    index_mtime = index_path.stat().st_mtime

    for py_file in root.rglob("*.py"):
        if any(part.startswith(".") and part not in [".", ".."] for part in py_file.parts):
            continue
        if py_file.stat().st_mtime > index_mtime:
            return True

    return False


def get_or_build_index(path: str = ".") -> Dict[str, List[Dict[str, Any]]]:
    if should_rebuild_index(path):
        index = build_index(path)
        save_index(index, path)
        return index
    return load_index(path)
