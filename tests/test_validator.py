import pytest
from hallucheck.validator import validate_references
from hallucheck.reference_extractor import ExtractedReference

def test_validate_references():
    index = {
        "fetch_roles": [{"file": "models.py", "kind": "method"}],
        "sign_jwt": [{"file": "utils.py", "kind": "function"}],
        "LoginResponse": [{"file": "types.py", "kind": "class"}]
    }

    refs = [
        ExtractedReference("get_permissions", "method", 2, "file.py", ""),
        ExtractedReference("utils.crypto.sign_payload", "import", 1, "file.py", ""),
        ExtractedReference("sign_payload", "function", 3, "file.py", ""),
        ExtractedReference("AuthResponse", "type", 4, "file.py", "")
    ]

    hallucinations = validate_references(refs, index)

    # We should have exactly 3 hallucinations after deduplication/filtering:
    # 1. get_permissions (method)
    # 2. utils.crypto.sign_payload (import)
    # 3. AuthResponse (type)

    assert len(hallucinations) == 3

    names = [h.reference for h in hallucinations]
    assert "get_permissions" in names
    assert "utils.crypto.sign_payload" in names
    assert "AuthResponse" in names

    # sign_payload function should be filtered out because it overlaps with the import
    assert "sign_payload" not in names
