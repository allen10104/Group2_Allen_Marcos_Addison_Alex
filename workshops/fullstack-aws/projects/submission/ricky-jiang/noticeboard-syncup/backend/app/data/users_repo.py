# The list of operations the app is allow to perform on the user collection. 

from datetime import datetime, timezone

# we need the real object id to query the database, not pydantic's PyObjectId
# because this file is directly talking to the database
from bson import ObjectId

# Gets the shared connection and how this file will reach the database
from app.database import get_db
from app.models.user import Role, UserInDB, UserStatus

# defines the name of the collection in the database that this file will operate on.
COLLECTION = "users"

# looks up a user by email and returns the user document if found, otherwise returns None.
async def get_user_by_email(email: str) -> UserInDB | None:
    doc = await get_db()[COLLECTION].find_one({"email": email})
    return UserInDB(**doc) if doc else None

# used to get a user by their id, which is the unique identifier for each user in the database.
async def get_user_by_id(user_id: str | ObjectId) -> UserInDB | None:
    doc = await get_db()[COLLECTION].find_one({"_id": ObjectId(user_id)})
    return UserInDB(**doc) if doc else None

# creates a new user document in the database with the provided email, hashed password, role, created_by, and status. 
async def create_user(
    email: str,
    hashed_password: str,
    role: Role,
    created_by: ObjectId | None,
    status: UserStatus = UserStatus.APPROVED,
) -> UserInDB:
    doc = {
        "email": email,
        "hashed_password": hashed_password,
        "role": role.value,
        "status": status.value,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc),
    }
    result = await get_db()[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return UserInDB(**doc)

# Flips the status of a user between PENDING and APPROVED. It is used to approve or reject a manager account that was created through self registration.
async def set_user_status(user_id: str | ObjectId, status: UserStatus) -> UserInDB | None:
    result = await get_db()[COLLECTION].find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": status.value}},
        return_document=True,
    )
    return UserInDB(**result) if result else None

# supports the managers read status feature. It returns a list of all employee ids in the system, which is used to calculate the read status of a notice.
async def list_all_employee_ids() -> list[ObjectId]:
    cursor = get_db()[COLLECTION].find({"role": Role.EMPLOYEE.value}, {"_id": 1})
    return [doc["_id"] async for doc in cursor]

# supports the managers read status feature. It returns a list of all employee emails in the system, which is used to calculate the read status of a notice.
async def list_employee_emails_by_ids(user_ids: list[ObjectId]) -> list[str]:
    cursor = get_db()[COLLECTION].find({"_id": {"$in": user_ids}}, {"email": 1})
    return [doc["email"] async for doc in cursor]