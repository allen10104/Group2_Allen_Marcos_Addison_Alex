# os.getenv reads environment variables, this is how we pick up JWT_SECRET_KEY.
import os

# datetime/timedelta are used to set how long a token stays valid.
from datetime import datetime, timedelta

# load_dotenv copies the values out of the .env file into the environment.
from dotenv import load_dotenv

# CryptContext handles hashing and verifying passwords using bcrypt.
from passlib.context import CryptContext

# jwt encodes/decodes JSON Web Tokens. JWTError is raised when a token is
# invalid, expired, or tampered with.
from jose import jwt, JWTError

load_dotenv()

# The secret key used to sign tokens. Anyone with this key could forge a
# valid token, so it lives only in .env, never in the source code.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Copy .env.example to .env and fill it in."
    )

# The signing algorithm used to create/verify tokens.
ALGORITHM = "HS256"

# How long a login stays valid before the user has to log in again.
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# schemes=["bcrypt"] tells passlib to use bcrypt for hashing passwords.
# deprecated="auto" lets it phase out older schemes automatically if we
# ever add one later.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hashes a plain-text password before it's stored in the database.
# We never store or compare raw passwords directly.
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


# Checks a plain-text password (typed at login) against the stored hash.
# Returns True if they match, False otherwise.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Creates a signed JWT containing the given data (e.g. user id, role).
# The token also embeds an expiration time ("exp"), after which it's
# automatically rejected during verification.
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Decodes and verifies a JWT. Returns the payload (a dict) if valid.
# Returns None if the token is invalid, tampered with, or expired.
def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None