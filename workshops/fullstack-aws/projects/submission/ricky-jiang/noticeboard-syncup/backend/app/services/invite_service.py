# THis file contains the business logic for generating, validating, and consuming invite codes. 
# It uses the `secrets` module to generate secure random codes, and interacts with the database
# through the `invite_codes_repo` module.

import secrets

from bson import ObjectId

from app.data.invite_codes_repo import create_invite_code, get_invite_code_by_code, mark_code_used
from app.models.invite_code import InviteCodeInDB
from app.models.user import UserInDB


# a private function that generates a secure random code string using the `secrets` module.
def _generate_code_string() -> str:
    return secrets.token_urlsafe(6).upper()

# This function generates a new invite code for the specified target email and manager.
async def generate_code(target_email: str, manager: UserInDB) -> InviteCodeInDB:
    code = _generate_code_string()
    return await create_invite_code(code=code, target_email=target_email, created_by=manager.id)

# This function validates an invite code by checking that it exists, is associated with the specified email, and has not been used yet.
async def validate_code(email: str, code: str) -> InviteCodeInDB | None:
    invite = await get_invite_code_by_code(code)
    if invite is None:
        return None
    if invite.target_email.lower() != email.lower():
        return None
    if invite.used_by is not None:
        return None
    return invite

# This function consumes an invite code by marking it as used by the specified user.
async def consume_code(code: str, used_by: ObjectId) -> None:
    await mark_code_used(code, used_by)