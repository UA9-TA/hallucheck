import ast
from dataclasses import dataclass
from typing import List

from .diff_parser import DiffLine


@dataclass
class ExtractedReference:
    name: str
    kind: str  # 'method', 'function', 'import', 'type'
    line_number: int
    file: str
    context: str


class ReferenceVisitor(ast.NodeVisitor):
    def __init__(self, file: str, line_offset: int, code_context: str):
        self.file = file
        self.line_offset = line_offset  # The starting line number of the snippet
        self.code_context = code_context
        self.references: List[ExtractedReference] = []

    def get_real_line_number(self, node: ast.AST) -> int:
        # node.lineno is relative to the parsed snippet
        return self.line_offset + getattr(node, "lineno", 1) - 1

    def add_reference(self, name: str, kind: str, node: ast.AST):
        self.references.append(
            ExtractedReference(
                name=name,
                kind=kind,
                line_number=self.get_real_line_number(node),
                file=self.file,
                context=self.code_context,
            )
        )

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            # It's a method call: obj.method()
            self.add_reference(node.func.attr, "method", node)
        elif isinstance(node.func, ast.Name):
            # It's a function call or class instantiation: func()
            self.add_reference(node.func.id, "function", node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.add_reference(alias.name, "import", node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            # We add the module itself
            self.add_reference(node.module, "import", node)
            # We also add the imported names as imports, though they might be functions/classes
            for alias in node.names:
                # We record the full path for imports to help with validation
                full_name = f"{node.module}.{alias.name}"
                self.add_reference(full_name, "import", node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # Type annotations in assignments: x: Type
        if isinstance(node.annotation, ast.Name):
            self.add_reference(node.annotation.id, "type", node)
        elif isinstance(node.annotation, ast.Subscript):
            # E.g., List[Type]
            if isinstance(node.annotation.value, ast.Name):
                self.add_reference(node.annotation.value.id, "type", node)
            # A full type extractor would walk the subscript slice too
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Type annotations in function signatures
        if node.returns:
            if isinstance(node.returns, ast.Name):
                self.add_reference(node.returns.id, "type", node)
        for arg in node.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    self.add_reference(arg.annotation.id, "type", arg)
        self.generic_visit(node)


def extract_references_from_lines(diff_lines: List[DiffLine]) -> List[ExtractedReference]:
    # Group lines by file and consecutive blocks to form valid AST snippets
    # A simplified approach is to try parsing line by line. If it fails, accumulate.
    # To be accurate and handle multiline statements, we should build blocks.

    references = []

    # Group by file
    files_to_lines = {}
    for dl in diff_lines:
        if dl.file not in files_to_lines:
            files_to_lines[dl.file] = []
        files_to_lines[dl.file].append(dl)

    for file, lines in files_to_lines.items():
        # Sort by line number
        lines.sort(key=lambda x: x.line_number)

        # Try to parse individual lines first (often works for imports, simple calls)
        # If it fails, we skip. A more robust way would be to parse the whole file
        # with the patch applied and find the nodes overlapping with changed lines.
        # But per requirements: "Use Python ast.parse() on the added lines to get accurate extraction"

        for i, dl in enumerate(lines):
            # Basic indentation cleanup might be needed if lines are inside a block
            # For this simple implementation, we'll strip leading whitespace to allow
            # parsing isolated statements, but that breaks multiline things.
            # A better approach: pad with spaces based on indent, or wrap in a dummy function.

            # Wrap in dummy function to handle indented lines
            code = f"def dummy_wrapper():\n    {dl.content.lstrip()}"
            try:
                tree = ast.parse(code)
                visitor = ReferenceVisitor(file, dl.line_number, dl.content)
                visitor.visit(tree)
                references.extend(visitor.references)
            except SyntaxError:
                # If a single line fails, it might be part of a multiline statement
                # A more sophisticated parser would accumulate.
                pass

    return references
