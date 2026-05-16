from dataclasses import dataclass


@dataclass
class LoginResponse:
    token: str
    user_id: int
