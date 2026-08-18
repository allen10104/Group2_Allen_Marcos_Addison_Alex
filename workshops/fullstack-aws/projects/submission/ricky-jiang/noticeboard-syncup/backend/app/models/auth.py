# None of these are stored in the database, they are only used for request/response 
# validation and serialization

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role

# Body of POST auth/login 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# This is what is returned to the client when a user logs in successfully. It contains the access and refresh tokens, which are used to authenticate subsequent requests.
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Body of POST auth/refresh 
class RefreshRequest(BaseModel):
    refresh_token: str

# Shape of the data stored in the decoded JWT token. It contains the users id and role. 
class TokenData(BaseModel):
    sub: str
    role: Role

# The body of the request to register a new user. It is used to validate the request body and ensure that the required fields are present and valid.
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role = Role.EMPLOYEE
    invite_code: str | None = None
# The body of the request to verify a manager's invite code. It is used to validate the request body and ensure that the required fields are present and valid.
class VerifyManagerRequest(BaseModel):
    email: EmailStr
    code: str