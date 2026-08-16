class User:
    def __init__(self, id, name, email, password, is_admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def can_modify(self, notice):
        return notice.author_id == self.id or self.is_admin

    def my_notices(self, board):
        return board.notices_by_author(self.id)
