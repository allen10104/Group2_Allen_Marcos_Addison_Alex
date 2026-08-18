
# Import the user_service module, which holds the database logic for users.
from services import user_service
# Import FastAPI's router, exception, and HTTP status-code helpers.
from fastapi import APIRouter, HTTPException, status
# Import our password-hashing helper from the security module.
from security.security import hash_password
# Import the Pydantic request/response models used for validation.
from models import schemas
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from security.security import verify_password, create_access_token

# Create a router for auth endpoints, prefixing all its routes with "/auth".
router = APIRouter(prefix="/auth")
# Register this function as the handler for POST /auth/register, returning a User_Out on success.
@router.post("/register", response_model=schemas.User_Out)
# Define the async handler, taking a validated User_Create body as input.
async def register_user(user: schemas.User_Create):
    """
    Register a new user.
    """
    # Look up whether a user with this email already exists in the database.
    existing = await user_service.get_user_by_email(user.email)
    # If a matching user was found, block the registration.
    if existing:
        # Raise a 400 error telling the client the email is already taken.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the plain-text password before it ever touches the database.
    hashed = hash_password(user.password)
    # Insert the new user record using the email and hashed password.
    new_user = await user_service.create_user(user.email, hashed)
    # Return the newly created user, shaped by the User_Out response model.
    return new_user


@router.post("/login", response_model=schemas.token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Log in and receive a JWT access token.
    """
    # OAuth2PasswordRequestForm always calls the identifier field "username" --
    # we're treating it as the email, since that's what we log in with.
    user = await user_service.get_user_by_email(form_data.username)

    # Same generic error whether the email doesn't exist or the password is
    # wrong -- don't reveal which one failed, so an attacker can't use this
    # endpoint to figure out which emails are registered.
    if user is None or not verify_password(form_data.password, user["hash_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}