from hallucheck.diff_parser import parse_diff


def test_parse_diff():
    with open("tests/fixtures/sample_diff.patch", "r") as f:
        diff_content = f.read()

    added_lines = parse_diff(diff_content)

    assert len(added_lines) == 3

    # Check first hallucination
    assert added_lines[0]["file"] == "auth/validators.py"
    assert "user.get_permissions()" in added_lines[0]["content"]

    # Check second hallucination
    assert added_lines[1]["file"] == "auth/validators.py"
    assert "from utils.crypto import sign_payload" in added_lines[1]["content"]

    # Check third hallucination
    assert added_lines[2]["file"] == "payment/processor.py"
    assert "response: AuthResponse = process(data)" in added_lines[2]["content"]
