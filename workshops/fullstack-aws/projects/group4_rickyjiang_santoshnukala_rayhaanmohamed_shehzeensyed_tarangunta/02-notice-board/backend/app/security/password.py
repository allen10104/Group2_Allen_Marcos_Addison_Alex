"""Password hashing. The only module in this codebase that touches raw passwords."""

import bcrypt


def hash_password(raw: str) -> str:
    """Hash a plaintext password for storage.

    bcrypt generates a random salt per password and embeds it in the output, so two
    employees with the identical password get different hashes and a rainbow table is
    useless. It is also deliberately SLOW (~100ms) - that slowness IS the security
    property, because it makes brute force expensive.

    Never store a plain SHA-256 of a password. SHA is designed to be fast, which is
    exactly wrong here: a GPU does billions of SHA-256 hashes per second.
    """
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, stored_hash: str) -> bool:
    """Check a plaintext password against a stored hash.

    checkpw re-hashes `raw` using the salt embedded in `stored_hash` and compares in
    constant time. We never decrypt anything - bcrypt is one-way, and that is the point.

    The try/except guards against a malformed hash in the database (a truncated field,
    a hand-edited value). Without it, one bad row turns every login into a 500 instead
    of a clean "invalid credentials".
    """
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
    