import ast
import json
import os
from pathlib import Path

INDEX_FILE = ".hallucheck-index.json"


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.symbols = {}
        self.current_class = None

    def add_symbol(self, name, line, kind, parent_class=None):
        if name not in self.symbols:
            self.symbols[name] = []
        self.symbols[name].append(
            {"file": self.filepath, "line": line, "kind": kind, "parent_class": parent_class}
        )

    def visit_ClassDef(self, node):
        self.add_symbol(node.name, node.lineno, "class")
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        kind = "method" if self.current_class else "function"
        self.add_symbol(node.name, node.lineno, kind, self.current_class)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        kind = "method" if self.current_class else "function"
        self.add_symbol(node.name, node.lineno, kind, self.current_class)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                kind = "attribute" if self.current_class else "variable"
                self.add_symbol(target.id, node.lineno, kind, self.current_class)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            kind = "attribute" if self.current_class else "variable"
            self.add_symbol(node.target.id, node.lineno, kind, self.current_class)
        self.generic_visit(node)


def build_index(directory="."):
    index = {}
    path = Path(directory)

    for filepath in path.rglob("*.py"):
        if ".venv" in filepath.parts or "venv" in filepath.parts or ".git" in filepath.parts:
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(filepath))

            visitor = SymbolVisitor(str(filepath.relative_to(path)))
            visitor.visit(tree)

            for name, occurrences in visitor.symbols.items():
                if name not in index:
                    index[name] = []
                index[name].extend(occurrences)

        except Exception:
            # Skip unparseable files
            continue

    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

    return index


def load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    try:
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}
