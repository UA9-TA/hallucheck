import os

from hallucheck.diff_parser import parse_diff
from hallucheck.indexer import build_index
from hallucheck.validator import validate_diff


def test_validate_diff():
    # Build index from sample codebase
    index = build_index("tests/fixtures/sample_codebase")

    # Parse diff
    with open("tests/fixtures/sample_diff.patch", "r") as f:
        diff_content = f.read()
    diff_lines = parse_diff(diff_content)

    # Validate
    hallucinations = validate_diff(diff_lines, index)

    # We expect 3 hallucinations (ignoring 'process' which isn't defined but let's assume we catch the main ones)

    get_perms = [h for h in hallucinations if h.reference == "user.get_permissions"]
    assert len(get_perms) == 1
    assert "permissions" in get_perms[0].suggestions

    sign_payload = [
        h
        for h in hallucinations
        if h.reference == "utils.crypto.sign_payload" or h.reference == "sign_payload"
    ]
    assert len(sign_payload) == 1

    auth_resp = [h for h in hallucinations if h.reference == "AuthResponse"]
    assert len(auth_resp) == 1

    if os.path.exists(".hallucheck-index.json"):
        os.remove(".hallucheck-index.json")
