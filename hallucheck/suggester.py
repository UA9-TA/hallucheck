import difflib
from typing import Any, Dict, List


def get_suggestions(
    reference_name: str, kind: str, index: Dict[str, List[Dict[str, Any]]], limit: int = 2
) -> List[str]:
    """Finds the closest matching symbols in the index."""

    # Filter the index keys based on the expected kind, but also allow
    # close matches across kinds (e.g., asked for property, got method)
    all_symbols = list(index.keys())

    # Basic fuzzy matching
    matches = difflib.get_close_matches(reference_name, all_symbols, n=limit, cutoff=0.6)

    suggestions = []
    for match in matches:
        # Get details about the matched symbol to format the suggestion
        entries = index[match]
        if not entries:
            continue

        entry = entries[0]  # Just take the first one for the suggestion description
        match_kind = entry["kind"]

        if match_kind == "method":
            suggestions.append(f"{match}()")
        elif match_kind == "property":
            suggestions.append(f"{match} (property)")
        elif match_kind == "class":
            suggestions.append(f"{match} (class in {entry['file']})")
        else:
            suggestions.append(f"{match} (in {entry['file']})")

    return suggestions
