import pytest
from hallucheck.indexer import build_index
from pathlib import Path

def test_indexer_builds_correct_index(tmp_path):
    # Setup simple codebase
    code_dir = tmp_path / "src"
    code_dir.mkdir()

    auth_dir = code_dir / "auth"
    auth_dir.mkdir()

    (auth_dir / "models.py").write_text("""
class User:
    def __init__(self, username: str):
        self.username = username

    @property
    def permissions(self) -> list[str]:
        return ["read"]

    def fetch_roles(self) -> list[str]:
        return ["user"]
""")

    (auth_dir / "types.py").write_text("""
from dataclasses import dataclass

@dataclass
class LoginResponse:
    token: str
    user_id: int
""")

    utils_dir = code_dir / "utils"
    utils_dir.mkdir()

    (utils_dir / "signing.py").write_text("""
def sign_jwt(payload: dict) -> str:
    return "signed"

def sign_request(request_data: dict) -> str:
    return "signed"
""")

    # Build index
    index = build_index(str(code_dir))

    # Assertions
    assert "User" in index
    assert "permissions" in index
    assert index["permissions"][0]["kind"] == "property"
    assert "fetch_roles" in index
    assert index["fetch_roles"][0]["kind"] == "method"

    assert "LoginResponse" in index
    assert index["LoginResponse"][0]["kind"] == "class"

    assert "sign_jwt" in index
    assert index["sign_jwt"][0]["kind"] == "function"
    assert "sign_request" in index

    assert "auth.models" in index
    assert index["auth.models"][0]["kind"] == "module"
