from backend.models.user import User
from fastapi import HTTPException, Header

USERS: dict[int, User] = {
    1: User(id=1, name="John Doe", email="john.doe@example.com", password="password", is_admin=True),
    2: User(id=2, name="Jane Doe", email="jane.doe@example.com", password="password", is_admin=False),
    3: User(id=3, name="Jim Doe", email="jim.doe@example.com", password="password", is_admin=False),
    99: User(id=99, name="Admin", email="admin@example.com", password="password", is_admin=True),
}


def get_current_user(x_user_id: int=Header(..., alias="X-User-ID")) -> User:
    try:
        return USERS[x_user_id]
    except KeyError:
        raise HTTPException(status_code=401, detail="Unauthorized")