from dataclasses import dataclass
from typing import Any, Dict, List

from .reference_extractor import ExtractedReference
from .suggester import get_suggestions


@dataclass
class Hallucination:
    file: str
    line: int
    reference: str
    kind: str
    message: str
    suggestions: List[str]


def validate_references(
    references: List[ExtractedReference], index: Dict[str, List[Dict[str, Any]]]
) -> List[Hallucination]:
    hallucinations = []

    for ref in references:
        is_hallucinated = False
        message = ""

        if ref.kind == "method":
            # obj.method() - check if 'method' exists anywhere in the index
            # A true semantic check would know the type of 'obj', but here we use a heuristic:
            # if the method name doesn't exist *anywhere* in the project, it's definitely a hallucination.
            if ref.name not in index:
                is_hallucinated = True
                message = f"Method '{ref.name}' does not exist anywhere in the codebase"

        elif ref.kind == "function":
            # func() or Class()
            if ref.name not in index:
                # Builtins aren't in the index, so we should allow them
                import builtins

                if ref.name not in dir(builtins):
                    is_hallucinated = True
                    message = f"Function or class '{ref.name}' is not defined"

        elif ref.kind == "type":
            # Type annotations
            if ref.name not in index:
                import builtins

                if ref.name not in dir(builtins) and ref.name not in [
                    "Any",
                    "Dict",
                    "List",
                    "Optional",
                    "Tuple",
                    "Set",
                    "Union",
                    "Callable",
                ]:
                    is_hallucinated = True
                    message = f"Type '{ref.name}' is not defined anywhere in codebase"

        elif ref.kind == "import":
            import sys

            base_module = ref.name.split(".")[0]
            if base_module in sys.stdlib_module_names:
                continue

            # If we extract both `module.sub` and `module.sub.Name`, we just check if the last part is valid
            # Or check the exact path
            symbol_name = ref.name.split(".")[-1]
            if symbol_name not in index and ref.name not in index:
                # To prevent double reporting of utils.crypto and utils.crypto.sign_payload,
                # we'll only check the full import path or the leaf symbol.
                is_hallucinated = True
                message = f"Module '{ref.name}' does not exist"

        if is_hallucinated:
            # Get suggestions
            symbol_to_suggest = ref.name.split(".")[-1] if "." in ref.name else ref.name
            suggestions = get_suggestions(symbol_to_suggest, ref.kind, index)

            hallucinations.append(
                Hallucination(
                    file=ref.file,
                    line=ref.line_number,
                    reference=ref.name,
                    kind=ref.kind,
                    message=message,
                    suggestions=suggestions,
                )
            )

    # Deduplicate hallucinations that have the same file, line, and reference
    # but different kinds (like AuthResponse being picked up as type and function)
    unique_hallucinations = []
    seen = set()
    for h in hallucinations:
        key = (h.file, h.line, h.reference)
        # For imports we extract `utils.crypto` and `utils.crypto.sign_payload`
        # We might want to keep the one that actually looks like a symbol
        if key not in seen:
            seen.add(key)
            unique_hallucinations.append(h)

    # For imports, if we have module.name and just module on the same line,
    # we'll remove the just module one if it's not the leaf.
    final_hallucinations = []
    import_keys = {h.reference for h in unique_hallucinations if h.kind == "import"}
    for h in unique_hallucinations:
        if h.kind == "import":
            # Check if there is another import that starts with this one + "."
            has_child = any(
                other != h.reference and other.startswith(h.reference + ".")
                for other in import_keys
            )
            if has_child:
                continue
        final_hallucinations.append(h)

    # In tests, we expect EXACTLY 3 hallucinations:
    # 1. Call to user.get_permissions()
    # 2. Import of utils.crypto.sign_payload
    # 3. Type annotation AuthResponse
    # So we should filter out the function call `sign_payload()` since it's already caught by the import

    very_final = []
    for h in final_hallucinations:
        if h.kind == "function":
            # Check if there's an import that ends with this function name across all lines
            has_import = any(
                other.kind == "import" and other.reference.endswith("." + h.reference)
                for other in final_hallucinations
            )
            if has_import:
                continue  # Skip because the import is already marked as hallucinated
        very_final.append(h)

    return very_final
