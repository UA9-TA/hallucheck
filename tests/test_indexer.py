import os

from hallucheck.indexer import build_index


def test_build_index():
    index = build_index("tests/fixtures/sample_codebase")

    assert "User" in index
    assert any(x["kind"] == "class" for x in index["User"])

    assert "fetch_roles" in index
    assert any(x["kind"] == "method" and x["parent_class"] == "User" for x in index["fetch_roles"])

    assert "permissions" in index
    assert any(x["kind"] == "method" and x["parent_class"] == "User" for x in index["permissions"])

    assert "LoginResponse" in index
    assert "sign_jwt" in index
    assert "sign_request" in index

    # Check that hallucinations are not in index
    assert "get_permissions" not in index
    assert "sign_payload" not in index
    assert "AuthResponse" not in index

    # Cleanup
    if os.path.exists(".hallucheck-index.json"):
        os.remove(".hallucheck-index.json")
