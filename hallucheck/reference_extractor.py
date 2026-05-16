import ast


class ReferenceVisitor(ast.NodeVisitor):
    def __init__(self):
        self.references = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.references.append(
                {
                    "kind": "method",
                    "name": node.func.attr,
                    "full_name": f"{self._get_name(node.func.value)}.{node.func.attr}",
                }
            )
        elif isinstance(node.func, ast.Name):
            self.references.append({"kind": "function", "name": node.func.id})
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.references.append({"kind": "import", "module": node.module, "name": alias.name})
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.references.append({"kind": "import", "module": None, "name": alias.name})
        self.generic_visit(node)

    def visit_Name(self, node):
        # We catch Names used in annotations via visit_AnnAssign, but might need others
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.annotation, ast.Name):
            self.references.append({"kind": "type", "name": node.annotation.id})
        elif isinstance(node.annotation, ast.Subscript):
            if isinstance(node.annotation.value, ast.Name):
                self.references.append({"kind": "type", "name": node.annotation.value.id})
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.returns:
            if isinstance(node.returns, ast.Name):
                self.references.append({"kind": "type", "name": node.returns.id})
        for arg in node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Name):
                self.references.append({"kind": "type", "name": arg.annotation.id})
        self.generic_visit(node)

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return f"{self._get_name(node.func)}()"
        return "unknown"


def extract_references(code_string):
    # To parse a single line or fragment, we might need to wrap it if it has indentation errors
    # Let's try parsing directly first
    try:
        tree = ast.parse(code_string)
    except SyntaxError:
        try:
            # Try parsing it as part of a dummy function if it's indented
            tree = ast.parse(f"def dummy():\n    {code_string.strip()}")
        except SyntaxError:
            return []

    visitor = ReferenceVisitor()
    visitor.visit(tree)
    return visitor.references
