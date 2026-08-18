# This file contains the business logic for user management, specifically for when a manager creates employee users.
# THE FLOW:
# POST /users → users_controller (checks Depends(require_roles(Role.MANAGER))) → user_service.create_employee()

from bson import ObjectId
from fastapi import HTTPException, status

from app.data.users_repo import create_user, get_user_by_email
from app.models.user import Role, UserInDB
from app.security.passwords import hash_password

# This function creates a new employee user in the database. It checks for existing users with the same email and raises an error if found. 
# If the email is unique, it creates the user with the provided email, hashed password, and associates it with the manager who created it.
async def create_employee(email: str, password: str, manager: UserInDB) -> UserInDB:
    existing = await get_user_by_email(email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    return await create_user(
        email=email,
        hashed_password=hash_password(password),
        role=Role.EMPLOYEE,
        created_by=ObjectId(manager.id),
    )