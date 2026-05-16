import builtins
import importlib.util
import sys
from dataclasses import dataclass
from typing import List

from .reference_extractor import extract_references
from .suggester import get_suggestions


@dataclass
class Hallucination:
    file: str
    line: int
    reference: str
    kind: str
    message: str
    suggestions: List[str]


# Get all Python built-in names
BUILTINS = set(dir(builtins))

# Add common typing annotations
BUILTINS.update(
    {"Any", "Optional", "List", "Dict", "Set", "Tuple", "Union", "Callable", "Sequence", "Mapping"}
)


def is_valid_module(module_name):
    """Check if a module exists in the environment (standard library or site-packages)."""
    if module_name in sys.builtin_module_names:
        return True

    try:
        # Avoid actually importing if we can just check for existence
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except Exception:
        return False


def validate_diff(diff_lines, index):
    hallucinations = []

    for item in diff_lines:
        file = item["file"]
        line_num = item["line"]
        content = item["content"]

        refs = extract_references(content)

        for ref in refs:
            name = ref["name"]
            kind = ref["kind"]

            if name in BUILTINS:
                continue

            if kind == "method":
                # For a method obj.foo(), name is 'foo'
                # Builtin types have common methods we should allow
                COMMON_METHODS = {
                    "append",
                    "extend",
                    "insert",
                    "remove",
                    "pop",
                    "clear",
                    "index",
                    "count",
                    "sort",
                    "reverse",
                    "copy",
                    "update",
                    "keys",
                    "values",
                    "items",
                    "get",
                    "setdefault",
                    "popitem",
                    "add",
                    "discard",
                    "difference",
                    "intersection",
                    "union",
                    "issubset",
                    "issuperset",
                    "split",
                    "join",
                    "replace",
                    "strip",
                    "lstrip",
                    "rstrip",
                    "format",
                    "lower",
                    "upper",
                    "startswith",
                    "endswith",
                    "read",
                    "write",
                    "close",
                    "seek",
                    "tell",
                }

                if name not in index and name not in COMMON_METHODS and not name.startswith("__"):
                    suggestions = get_suggestions(name, index, limit=2)
                    hallucinations.append(
                        Hallucination(
                            file=file,
                            line=line_num,
                            reference=ref["full_name"],
                            kind=kind,
                            message=f"Method '{name}' not found in index",
                            suggestions=suggestions,
                        )
                    )
            elif kind == "function" or kind == "type":
                if name not in index:
                    suggestions = get_suggestions(name, index, limit=2)
                    hallucinations.append(
                        Hallucination(
                            file=file,
                            line=line_num,
                            reference=name,
                            kind=kind,
                            message=f"{kind.capitalize()} '{name}' not defined anywhere in codebase",
                            suggestions=suggestions,
                        )
                    )
            elif kind == "import":
                # ref["module"] is the module part of `from module import name`
                # if it's `import name`, module is None
                module = ref.get("module")
                full_module = f"{module}.{name}" if module else name

                # We check if the imported name exists in the index
                # Or if the module is a valid external module
                if (
                    name not in index
                    and not is_valid_module(module or name)
                    and not is_valid_module(full_module)
                ):
                    suggestions = get_suggestions(name, index, limit=2)
                    full_ref = full_module

                    hallucinations.append(
                        Hallucination(
                            file=file,
                            line=line_num,
                            reference=full_ref,
                            kind=kind,
                            message=f"Import '{name}' does not exist in codebase",
                            suggestions=suggestions,
                        )
                    )

    return hallucinations
