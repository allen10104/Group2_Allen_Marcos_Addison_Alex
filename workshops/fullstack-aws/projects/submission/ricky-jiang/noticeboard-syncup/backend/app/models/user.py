# This files defines the user model and the user creation model for the application.
# Nothing here talks directly to the database, it just defines the data structure and validation rules for users.

# The FLOW OF THE USER MODEL is as follows:
#Employee self-registers  →  RegisterRequest(role=EMPLOYEE)  →  UserInDB created with status=ACTIVE (default)  →  can log in immediately
#Manager self-registers, has valid code   →  RegisterRequest(role=MANAGER, invite_code="...")  →  code validated against invite_codes  →  UserInDB created with status=ACTIVE  →  can log in immediately
#Manager self-registers, no/bad code      →  RegisterRequest(role=MANAGER)  →  UserInDB created with status=PENDING  →  auth_service.login() rejects them until...
#...they later call POST /auth/verify-manager {email, code}  →  invite code validated and marked used  →  that user's status flipped PENDING → ACTIVE  →  can now log in

# datetime for timestamping
from datetime import datetime, timezone
#enum for defining the user roles
from enum import Enum
#Basemdoel is base class for defining the user model
#EmailStr is a type for validating email addresses
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.py_object_id import PyObjectId


# This is the only allowed roles for users in the system. 
# It is used to validate the role field in the user model.
# This prevents users from having arbitrary roles that are not recognized by the system like admin or misspelled roles.
class Role(str, Enum):
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"

# This is for the exisiting user (A MANAGER) to create new users.
# Thew new user created is an EMPLOYEE by default, as MANAGER can only create EMPLOYEEs.
# An new employee is given an email and password, which is hashed before storing in the database. 
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = Role.EMPLOYEE

# Similar to class Role, it defies the status of a user in the system.
# Whether a newly created manager account is usable yet.
# This is because a newly created manager account needs to be approved by the seed manager before it can be used to create new employee accounts.
# Whereas a newly created employee account can be used immediately to log in and use the system.
class UserStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"

# Defines the shape of the user data stored in the database.
class UserInDB(BaseModel):
    #   allows this model to be populated by field names or aliases, 
    # and allows arbitrary types like PyObjectId to be used in the model
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    #the bycrypt hashed password is stored in the database, not the plain text password
    hashed_password: str
    # All users in database will have a role, either MANAGER or EMPLOYEE. 
    # This is used to control access to certain features in the system.
    role: Role
    # Every new user created is active by default
    # However if a new manager is created through self registration it will be overridden to PENDING
    status: UserStatus = UserStatus.APPROVED
    # Defines the user who created the new user.
    # None if the user was created by the seed manager, otherwise it is the id of the manager who created the user.
    created_by: PyObjectId | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# The shape of the user response returned to the client when a user is created or queried.
# note that the password is never returned to the client, only the hashed password is stored in the database.
class UserOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    role: Role
    status: UserStatus
    created_by: PyObjectId | None = None
    created_at: datetime 