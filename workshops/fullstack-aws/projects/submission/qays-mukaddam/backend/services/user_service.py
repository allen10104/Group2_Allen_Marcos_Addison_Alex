# Session is the type hint for the database session object passed in from
# each controller function, via FastAPI's Depends(get_db).
from sqlalchemy.orm import Session

# Import the User class so we can query and create rows through it.
from backend.models.user import User

# hash_password turns a plain-text password into a secure bcrypt hash.
# verify_password checks a plain-text password against a stored hash.
from backend.core.security import hash_password, verify_password


# Creates a new user tied to a specific organization, with a securely
# hashed password.
# Parameter order: db, username, password, role, organization_id.
def register_user(db: Session, username: str, password: str, role: str, organization_id: int):
    # Build the Python object in memory first — nothing is saved yet.
    # Matches User's constructor order exactly: username, hashed_password,
    # role, organization_id. The password is hashed here, so the raw
    # password never gets written to the database.
    new_user = User(username, hash_password(password), role, organization_id)

    # Stage the new object to be inserted.
    db.add(new_user)
    # Actually write it to PostgreSQL.
    db.commit()
    # Reload the object so it picks up the id PostgreSQL generated.
    db.refresh(new_user)

    return new_user


# Looks up a user by username and checks their password.
# Returns the User if valid, or None if the username doesn't exist or the
# password is wrong. Combining both checks into one return keeps callers
# from being able to tell "wrong username" apart from "wrong password".
def authenticate_user(db: Session, username: str, password: str):
    # Look up the user by their login name.
    user = db.query(User).filter(User.username == username).first()

    # No account with that username exists.
    if user is None:
        return None

    # Compare the typed password against the stored hash. This never
    # decrypts the hash — it re-hashes the input and compares hashes.
    if not verify_password(password, user.hashed_password):
        return None

    # Username exists and password matches.
    return user


# Finds a single user by username. Used to check for duplicates on
# registration.
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


# Finds a single user by id. Used to look up a comment/like author's
# username for display purposes.
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()