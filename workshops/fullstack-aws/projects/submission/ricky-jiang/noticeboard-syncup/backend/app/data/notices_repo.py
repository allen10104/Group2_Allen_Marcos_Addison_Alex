# This file contains the data access layer for the noticeboard application.
# It provides functions to interact with the notices collection in the database, 
# including creating, retrieving, updating, and listing notices.
# The functions use asynchronous operations to ensure non-blocking behavior when interacting with the database.
from datetime import datetime, timezone

from bson import ObjectId

from app.database import get_db
from app.models.notice import NoticeInDB, NoticeStatus

COLLECTION = "notices"

# creates a new notice document in the database with the provided title, body, category, status, and author_id.
# if notice is created with status APPROVED, the approved_by and approved_at fields are set to the author_id and current time respectively.
# meaning for managers, if they create a notice, it is automatically approved. 
async def create_notice(title: str, body: str, category: str, status: NoticeStatus, author_id: ObjectId) -> NoticeInDB:
    now = datetime.now(timezone.utc)
    doc = {
        "title": title,
        "body": body,
        "category": category,
        "status": status.value,
        "author_id": author_id,
        "created_at": now,
        "approved_by": author_id if status == NoticeStatus.APPROVED else None,
        "approved_at": now if status == NoticeStatus.APPROVED else None,
        "read_by": [],
    }
    result = await get_db()[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return NoticeInDB(**doc)

# retrieves a notice document from the database by its unique identifier (notice_id).
async def get_notice(notice_id: str | ObjectId) -> NoticeInDB | None:
    doc = await get_db()[COLLECTION].find_one({"_id": ObjectId(notice_id)})
    return NoticeInDB(**doc) if doc else None

# lists all notice documents in the database, optionally filtered by their status (PENDING, APPROVED, or REJECTED).
async def list_notices(status: NoticeStatus | None = None) -> list[NoticeInDB]:
    query: dict = {}
    if status is not None:
        query["status"] = status.value
    cursor = get_db()[COLLECTION].find(query).sort("created_at", -1)
    return [NoticeInDB(**doc) async for doc in cursor]

# updates the status of a notice document in the database, marking it as APPROVED or REJECTED.
# It is matching ID and status PENDING to ensure if two request somehow both try to approve/reject the same notice, only one will succeed.
async def set_notice_decision(notice_id: str | ObjectId, status: NoticeStatus, decided_by: ObjectId) -> NoticeInDB | None:
    result = await get_db()[COLLECTION].find_one_and_update(
        {"_id": ObjectId(notice_id), "status": NoticeStatus.PENDING.value},
        {
            "$set": {
                "status": status.value,
                "approved_by": decided_by,
                "approved_at": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )
    return NoticeInDB(**result) if result else None

# Marks a notice as read by a specific user by adding a read receipt to the notice's read_by list.
async def add_read_receipt(notice_id: str | ObjectId, user_id: ObjectId) -> bool:
    result = await get_db()[COLLECTION].update_one(
        {"_id": ObjectId(notice_id), "read_by.user_id": {"$ne": user_id}},
        {"$push": {"read_by": {"user_id": user_id, "read_at": datetime.now(timezone.utc)}}},
    )
    return result.modified_count == 1