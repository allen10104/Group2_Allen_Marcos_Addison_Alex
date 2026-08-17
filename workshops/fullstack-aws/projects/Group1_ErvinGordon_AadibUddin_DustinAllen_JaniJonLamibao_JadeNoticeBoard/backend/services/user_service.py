# Import the database module to access the shared connection pool.
from models import database
# Import get_connection, the helper that checks out a connection from the pool.
from models.database import get_connection, pool


# Define an async function that returns every user in the database.
async def get_all_users():
    """Fetch all users from the database."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Query every row in the users table.
        rows = await conn.fetch("SELECT * FROM users")
        # Convert each asyncpg Record into a plain dict before returning.
        return [dict(row) for row in rows]
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)



# Define an async function that inserts a new user with an email and hashed password.
async def create_user(email: str, hashed_password: str):
    """Insert a new user into the database and return the created row."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Insert the user, stamping created_at ourselves since the column has no default.
        row = await conn.fetchrow(
            "INSERT INTO users (email, hash_password, created_at) VALUES ($1, $2, now()) "
            "RETURNING id, email, created_at",
            email,
            hashed_password
        )
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)
    # Convert the inserted row into a plain dict and return it.
    return dict(row)

# Define an async function that fetches a single user by their email.
async def get_user_by_email(email: str):
    """Fetch a single user by their email."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Query for the user matching the given email.
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        # Return the row as a dict, or None if no user was found.
        return dict(row) if row else None
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)
