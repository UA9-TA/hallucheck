import pytest
from hallucheck.reference_extractor import extract_references_from_lines, DiffLine

def test_extract_references():
    lines = [
        DiffLine("file.py", 1, "    from utils.crypto import sign_payload"),
        DiffLine("file.py", 2, "    perms = user.get_permissions()"),
        DiffLine("file.py", 3, "    token = sign_payload(data)"),
        DiffLine("file.py", 4, "    response: AuthResponse = AuthResponse(token=token, user_id=user.id)")
    ]

    refs = extract_references_from_lines(lines)

    # We should have references for:
    # 1. utils.crypto (import)
    # 2. utils.crypto.sign_payload (import)
    # 3. get_permissions (method)
    # 4. sign_payload (function)
    # 5. AuthResponse (type)
    # 6. AuthResponse (function/class instantiation)

    ref_names = [r.name for r in refs]

    assert "utils.crypto" in ref_names
    assert "utils.crypto.sign_payload" in ref_names
    assert "get_permissions" in ref_names
    assert "sign_payload" in ref_names
    assert "AuthResponse" in ref_names

    # Verify kinds
    for r in refs:
        if r.name == "get_permissions":
            assert r.kind == "method"
        elif r.name == "utils.crypto.sign_payload":
            assert r.kind == "import"
        elif r.name == "AuthResponse" and r.kind == "type":
            assert True
