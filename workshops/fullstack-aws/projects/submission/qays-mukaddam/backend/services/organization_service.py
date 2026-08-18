# secrets generates cryptographically random strings — used to create
# unpredictable, hard-to-guess organization codes.
import secrets

from sqlalchemy.orm import Session

from backend.models.organization import Organization


# Generates a random, readable organization code, e.g. "A1B2C3D4".
# token_hex(4) gives 8 hex characters; .upper() makes it easier to read
# and type out loud when sharing it with members.
def generate_org_code() -> str:
    return secrets.token_hex(4).upper()


# Creates a new organization with a freshly generated, unique code.
def create_organization(db: Session, name: str):
    # Keep generating codes until we get one that isn't already taken.
    # Collisions are extremely unlikely with 8 hex characters, but this
    # guards against it instead of assuming it can never happen.
    while True:
        code = generate_org_code()
        existing = db.query(Organization).filter(Organization.org_code == code).first()
        if existing is None:
            break

    new_org = Organization(name, code)

    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    return new_org


# Looks up an organization by its code. Used when someone signs up as a
# MEMBER — the code tells us which organization to join.
def get_organization_by_code(db: Session, org_code: str):
    return db.query(Organization).filter(Organization.org_code == org_code).first()


# Looks up an organization by id. Used when scoping notices to whichever
# organization the current user belongs to.
def get_organization_by_id(db: Session, organization_id: int):
    return db.query(Organization).filter(Organization.id == organization_id).first()