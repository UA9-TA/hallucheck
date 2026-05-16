class User:
    def __init__(self, username: str):
        self.username = username

    @property
    def permissions(self):
        return ["read", "write"]

    def fetch_roles(self):
        return ["admin"]
