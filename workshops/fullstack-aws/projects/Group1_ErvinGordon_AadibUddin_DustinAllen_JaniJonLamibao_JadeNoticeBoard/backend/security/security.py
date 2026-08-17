# Import os so we can read environment variables like SECRET_KEY.
import os
# Import datetime and timedelta to compute token expiry times.
from datetime import datetime, timedelta
# Import jwt from python-jose to encode and decode JSON Web Tokens.
from jose import jwt
# Import bcrypt directly -- passlib's bcrypt backend detection is unmaintained
# and breaks against modern bcrypt releases, so we call bcrypt ourselves instead.
import bcrypt

# Read the JWT signing secret from the environment. No real-looking fallback here on
# purpose -- if SECRET_KEY isn't set, fail loudly instead of silently signing tokens
# with a value that could end up committed to source control.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")
# Set the JWT signing algorithm to HMAC-SHA256.
ALGORITHM = "HS256"
# Set how many minutes an access token stays valid.
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define a function that checks a plain password against a stored hash.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt.checkpw takes and returns bytes, so encode both sides as UTF-8.
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# Define a function that hashes a plain-text password for storage.
def hash_password(password: str) -> str:
    # bcrypt.hashpw returns bytes -- decode back to a str for storing/returning as text.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

# Define a function that builds a signed JWT from a data payload.
def create_access_token(data: dict) -> str:
    # Copy the input dict so the caller's original object isn't mutated.
    to_encode = data.copy()
    # Calculate the absolute expiry time as now plus the configured lifetime.
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Add the expiry as the standard "exp" claim.
    to_encode.update({"exp": expire})
    # Sign and return the token as a JWT string.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Define a function that verifies and decodes an incoming JWT.
def decode_access_token(token: str) -> dict:
    # Return the token's claims, raising an error if it's invalid or expired.
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
