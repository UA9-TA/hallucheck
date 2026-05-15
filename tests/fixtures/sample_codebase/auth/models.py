class User:
    def __init__(self, username: str):
        self.username = username

    @property
    def permissions(self) -> list[str]:
        return ["read"]

    def fetch_roles(self) -> list[str]:
        return ["user"]
