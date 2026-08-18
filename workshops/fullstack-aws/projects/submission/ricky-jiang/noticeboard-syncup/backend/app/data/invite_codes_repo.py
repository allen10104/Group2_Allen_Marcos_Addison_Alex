# This file contains the data access layer for the invite codes in the noticeboard application.
# It provides functions to create, retrieve, and mark invite codes as used in the database.
from datetime import datetime, timezone

from bson import ObjectId

from app.database import get_db
from app.models.invite_code import InviteCodeInDB

COLLECTION = "invite_codes"

# used when a manager creates a new invite code for a new manager to register. 
# It creates a new invite code document in the database with the provided code, target email, and created_by fields. 
# The used_by and used_at fields are set to None since the code has not been used yet.
async def create_invite_code(code: str, target_email: str, created_by: ObjectId) -> InviteCodeInDB:
    doc = {
        "code": code,
        "target_email": target_email,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc),
        "used_by": None,
        "used_at": None,
    }
    result = await get_db()[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return InviteCodeInDB(**doc)

# This lookup is used when someone registers with a code 
# and when a pending manager later verfies
async def get_invite_code_by_code(code: str) -> InviteCodeInDB | None:
    doc = await get_db()[COLLECTION].find_one({"code": code})
    return InviteCodeInDB(**doc) if doc else None

# Finds the code and confirm it hasnt been used yet, then marks it as used by the user with the provided used_by id 
# and sets the used_at timestamp to the current time.
# This makes it so that the same code cannot be used again for another registration.
async def mark_code_used(code: str, used_by: ObjectId) -> InviteCodeInDB | None:
    result = await get_db()[COLLECTION].find_one_and_update(
        {"code": code, "used_by": None},
        {"$set": {"used_by": used_by, "used_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return InviteCodeInDB(**result) if result else None