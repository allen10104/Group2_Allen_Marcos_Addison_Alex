# APIRouter lets us define routes separately and plug them into main.py's app.
# HTTPException lets us return proper error responses like 400/401.
# Depends is how FastAPI injects a database session into an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# BaseModel defines the shape of the incoming request body.
from pydantic import BaseModel

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual user logic.
from backend.services.user_service import register_user, authenticate_user, get_user_by_username

# Import the service functions that contain the actual organization logic.
from backend.services.organization_service import create_organization, get_organization_by_code

# create_access_token builds a signed JWT for a logged-in user.
from backend.core.security import create_access_token


# Create a router for auth-related endpoints. main.py will register this
# with app.include_router(...).
router = APIRouter()


# Request body for creating a brand-new organization. The requester
# automatically becomes its founding ADMIN.
class CreateOrganizationRequest(BaseModel):
    # Defaults to None so we can return our own 400 error when missing.
    organization_name: str = None
    username: str = None
    password: str = None


# Request body for joining an existing organization as a MEMBER, using
# the org_code its admin shared.
class JoinOrganizationRequest(BaseModel):
    org_code: str = None
    username: str = None
    password: str = None


# Request body for logging in.
class LoginRequest(BaseModel):
    username: str = None
    password: str = None


# POST /organizations/create
# Creates a new organization AND registers the requester as its founding
# ADMIN in one step. Returns the org_code so the frontend can display it
# prominently — this is the ONLY time it's shown.
@router.post("/organizations/create", status_code=201)
def create_org_and_admin(request: CreateOrganizationRequest, db: Session = Depends(get_db)):
    # All three fields are required to create an organization.
    if not request.organization_name or not request.username or not request.password:
        raise HTTPException(status_code=400, detail="organization_name, username, and password are required")

    # Reject duplicate usernames before creating anything.
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="username already taken")

    # Create the organization first, so we have its id to link the user to.
    new_org = create_organization(db, request.organization_name)

    # Register the requester as ADMIN of the org just created.
    # Argument order: db, username, password, role ("ADMIN"), organization_id.
    new_user = register_user(db, request.username, request.password, "ADMIN", new_org.id)

    # Return everything the frontend needs, including the org_code to
    # display to the new admin.
    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
        "organization_id": new_org.id,
        "organization_name": new_org.name,
        "org_code": new_org.org_code,
    }


# POST /organizations/join
# Registers a new MEMBER under an EXISTING organization, identified by
# its org_code.
@router.post("/organizations/join", status_code=201)
def join_org_as_member(request: JoinOrganizationRequest, db: Session = Depends(get_db)):
    # All three fields are required to join an organization.
    if not request.org_code or not request.username or not request.password:
        raise HTTPException(status_code=400, detail="org_code, username, and password are required")

    # Look up the organization by its code. If nothing matches, the code
    # is wrong — reject rather than silently creating an orphaned user.
    org = get_organization_by_code(db, request.org_code)
    if org is None:
        raise HTTPException(status_code=400, detail="Invalid organization code")

    # Reject duplicate usernames before creating anything.
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="username already taken")

    # Register the requester as a MEMBER of the organization found above.
    # Argument order: db, username, password, role ("MEMBER"), organization_id.
    new_user = register_user(db, request.username, request.password, "MEMBER", org.id)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
        "organization_id": org.id,
        "organization_name": org.name,
    }


# POST /login
# Works the same regardless of which organization the user belongs to,
# since organization_id lives on the User row itself, not in anything
# login-specific.
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Both fields are required to attempt a login.
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="username and password are required")

    # Look up the user and verify their password in one call.
    user = authenticate_user(db, request.username, request.password)

    # If either the username doesn't exist or the password is wrong,
    # authenticate_user returns None.
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # "sub" (subject) holds the user's id — get_current_user reads this
    # back out of the token later. We also embed role for convenience.
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    # token_type "bearer" tells the client how to send this token back:
    # in the Authorization header as "Bearer <token>".
    return {"access_token": access_token, "token_type": "bearer"}