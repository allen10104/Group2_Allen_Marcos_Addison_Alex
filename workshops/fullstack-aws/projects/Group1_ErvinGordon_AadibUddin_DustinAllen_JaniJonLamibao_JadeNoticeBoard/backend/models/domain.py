
import uuid


class User:
    def __init__(self, user_id :uuid, password: str, email: str):
        self.user_id = user_id
        self.password = password
        self.email = email

class Notice:
    def __init__(self, user_id: uuid, message: str):
        self.user_id = user_id
        self.message = message