class User:
    def __init__(self, id: int, name: str, email: str, password: str, is_admin: bool = False):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def can_modify(self, notice):
        return notice.author_id == self.id or self.is_admin