class User:
    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        password_hash: str,
        is_admin: bool = False,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin

    def can_modify(self, notice):
        return notice.author_id == self.id or self.is_admin
