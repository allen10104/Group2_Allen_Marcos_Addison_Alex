# Import FastAPI's dependency injection helper, exception class, and status codes.
from fastapi import Depends, HTTPException, status
# Import OAuth2PasswordBearer, which extracts a Bearer token from the Authorization header.
from fastapi.security import OAuth2PasswordBearer
# Import our JWT decoding function.
from security.security import decode_access_token
# Import user_service to look up users in the database.
from services import user_service

# Create a scheme that tells FastAPI where clients should go to obtain a token, for docs/OpenAPI purposes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Define a dependency that resolves the current user from a request's bearer token.
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Pre-build a reusable 401 error to raise whenever the token can't be validated.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Attempt to decode the token and extract the user's identity from it.
    try:
        # Decode and verify the JWT, getting back its claims.
        payload = decode_access_token(token)
        # Read the "sub" (subject) claim, which we use to store the user's email.
        email = payload.get("sub")
        # If there's no email in the token, treat it as invalid.
        if email is None:
            raise credentials_exception
    # Catch any decoding failure, e.g. bad signature or expired token.
    except Exception:
        # Convert any decoding error into the same 401 response.
        raise credentials_exception

    # Look up the user in the database using the email from the token.
    user = await user_service.get_user_by_email(email)
    # If no matching user exists (e.g. account was deleted), reject the request.
    if user is None:
        raise credentials_exception

    # Return the authenticated user object to whatever route depends on this function.
    return user
