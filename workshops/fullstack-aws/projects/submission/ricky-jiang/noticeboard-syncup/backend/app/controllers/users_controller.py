# This files only contains one endpoint for creating employee users.

# THE FLOW:
# POST /users (with a manager's Bearer token) → users_controller.create_employee()
#   → Depends chain: get_current_user() → require_roles checks role == MANAGER
#   → user_service.create_employee()
#   → UserOut conversion → response
from fastapi import APIRouter, Depends, status

from app.models.user import Role, UserCreate, UserInDB, UserOut
from app.security.deps import require_roles
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

# The `create_employee` endpoint allows a manager to create a new employee user by providing their email and password.
# It checks that the current user has the manager role and delegates the actual creation logic to the `user_service.create_employee` function.
# If the creation is successful, it returns the newly created user's
@router.post("", response_model=UserOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: UserCreate,
    manager: UserInDB = Depends(require_roles(Role.MANAGER)),
) -> UserOut:
    user = await user_service.create_employee(payload.email, payload.password, manager)
    return UserOut(**user.model_dump(by_alias=True))