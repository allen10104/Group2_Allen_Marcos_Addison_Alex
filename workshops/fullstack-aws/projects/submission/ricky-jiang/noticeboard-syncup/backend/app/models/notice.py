from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.py_object_id import PyObjectId


# Defines the status of a notice in the system. 
# A notice can only be in one of three states: PENDING, APPROVED, or REJECTED.
class NoticeStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# THe body of POST /notices. It is used to validate the request body and ensure that the required fields are present and valid.
# The min lenght is 1 so no empty notice is being submitted. 
# THe default category will be general
class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    category: str = "general"

#Each document will carry its own list of who has read the notice
class ReadReceipt(BaseModel):
    user_id: PyObjectId
    read_at: datetime

# Defines the shape of the notice data stored in the database.
# Every notice will have a status 
# author_id to identify the user who created the notice
# read_by list to keep track of which users have read the notice and when they read it.
class NoticeInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id")
    title: str
    body: str
    category: str
    status: NoticeStatus
    author_id: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: PyObjectId | None = None
    approved_at: datetime | None = None
    read_by: list[ReadReceipt] = Field(default_factory=list)

# What is returned from GET /notices. It is the same as NoticeInDB but with read_count and read_by_me fields added.   
class NoticeOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(alias="_id")
    title: str
    body: str
    category: str
    status: NoticeStatus
    author_id: PyObjectId
    created_at: datetime
    approved_by: PyObjectId | None = None
    approved_at: datetime | None = None
    read_count: int = 0
    read_by_me: bool = False

# A seperate response for GET /notices/{notice_id}/read-status. 
# It is used to return the read status of a notice, including the total number of employees, the number of employees who have read the notice, and the list of emails of employees who have read and not read the notice.
class ReadStatusOut(BaseModel):
    notice_id: PyObjectId
    total_employees: int
    read_count: int
    read_emails: list[str]
    unread_emails: list[str]