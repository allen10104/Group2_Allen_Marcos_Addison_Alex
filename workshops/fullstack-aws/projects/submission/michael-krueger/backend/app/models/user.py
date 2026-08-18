# BaseModel defines the shape of a request or response body. Field attaches
# the length rules below to individual fields.
from pydantic import BaseModel, Field


# The shape of the body POST /auth/signup and POST /auth/login expect.
#
# The plain password arrives here and goes no further: the service hashes it
# immediately and only the hash is ever stored. This model is deliberately
# never used as a response_model, because doing so would echo the password
# back to the caller.
#
# The 72 byte maximum is bcrypt's own limit, not an arbitrary choice. bcrypt
# silently ignored anything past 72 bytes for years and current versions
# raise instead, so the limit is stated here where the caller gets a clear
# 422 rather than a 500 from deep inside the hashing call.
#
# It is worth knowing this counts characters and bcrypt counts bytes, so a
# password of 72 accented or emoji characters is longer than 72 bytes and is
# caught by the byte check in auth_service instead. This bound is the cheap
# first pass, not the whole story.
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


# The shape of the body POST /auth/login expects.
#
# Almost identical to UserCreate, and separate from it on purpose.
#
# Reusing UserCreate here was the first version and it was wrong. Its rules
# describe what a new password must look like, and applying them at login
# means someone whose password is shorter than the current rule, or who
# simply mistypes a short one, gets a 422 listing the password policy
# instead of a 401. That is the wrong status, and it hands an anonymous
# caller the rules to aim at.
#
# The only constraint kept is min_length=1, which rejects an empty body
# without saying anything about what a valid password looks like. Checking
# the credentials is the service's job, and its answer is always the same
# vague 401.
class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# The shape of a user as the API returns it.
#
# password_hash is deliberately absent. Declaring this as the response_model
# on the signup route is what guarantees the hash cannot leak, because
# FastAPI filters the outgoing row down to exactly these two fields even
# though the service returns the whole database row.
class UserOut(BaseModel):
    id: int
    username: str


# The shape of a successful login response.
#
# token_type defaults to "bearer" because that is the only type this API
# issues, and it is the word the client has to put in front of the token in
# the Authorization header. Returning it rather than assuming it is what the
# OAuth2 conventions expect, and it is what lets a generic client know how to
# use the token without being told separately.
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
