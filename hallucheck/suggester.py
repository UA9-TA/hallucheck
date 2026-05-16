import difflib


def get_suggestions(name, index, kind=None, limit=2):
    all_names = list(index.keys())

    # Optional filtering by kind
    if kind:
        # Simplistic filtering - we might want to be more sophisticated
        pass

    matches = difflib.get_close_matches(name, all_names, n=limit, cutoff=0.6)

    # Include modules if it's an import hallucination
    if kind == "import" and not matches:
        pass  # Could suggest modules based on path matching

    return matches
