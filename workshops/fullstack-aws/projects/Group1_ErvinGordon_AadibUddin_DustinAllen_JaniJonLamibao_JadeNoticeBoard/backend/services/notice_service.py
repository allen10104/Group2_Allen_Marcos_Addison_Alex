# Import UUID for typing notice and user IDs.
from uuid import UUID
# Import datetime for typing expiration timestamps.
from datetime import datetime
# Import Optional for typing optional parameters.
from typing import Optional
# Import the database module to access the shared connection pool.
from models import database
# Import get_connection, the helper that checks out a connection from the pool.
from models.database import get_connection


# Define an async function that returns every notice in the database.
async def get_all_notices():
    """Fetch all notices from the database, including each creator's email."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Join users so we can include the creator's email alongside each
        # notice -- notices.* pulls every notices column, and users.email is
        # added under its own alias so it doesn't collide with anything.
        rows = await conn.fetch(
            "SELECT notices.*, users.email AS user_email "
            "FROM notices "
            "JOIN users ON notices.user_id = users.id "
            "WHERE notices.expires_at IS NULL OR notices.expires_at > now() "
            "ORDER BY notices.is_pinned DESC, notices.created_at DESC"
        )
        # Convert each asyncpg Record into a plain dict before returning.
        return [dict(row) for row in rows]
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)


# Define an async function that inserts a new notice for a given user.
async def create_notice(user_id: UUID, user_email: str, message: str, is_pinned: bool = False, expires_at: Optional[datetime] = None):
    """Insert a new notice into the database and return the created row.

    user_email isn't a notices column -- it's passed in by the caller
    (who already has it from the authenticated user's JWT) and attached to
    the returned dict below, so notice_Out has what it needs without a
    second query to look the email back up.
    """
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Insert the notice and return the newly created row's columns.
        row = await conn.fetchrow(
            "INSERT INTO notices (user_id, message, is_pinned, expires_at) VALUES ($1, $2, $3, $4) "
            "RETURNING id, user_id, message, is_pinned, expires_at, created_at",
            user_id,
            message,
            is_pinned,
            expires_at
        )
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)
    # Convert the inserted row into a plain dict, attach the email, and return it.
    result = dict(row)
    result["user_email"] = user_email
    return result


# Define an async function that fetches a single notice by its ID.
async def get_notice_by_id(notice_id: UUID):
    """Fetch a single notice by its ID, including its creator's email."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Same join as get_all_notices, scoped to one notice.
        row = await conn.fetchrow(
            "SELECT notices.*, users.email AS user_email "
            "FROM notices "
            "JOIN users ON notices.user_id = users.id "
            "WHERE notices.id = $1",
            notice_id
        )
        # Return the row as a dict, or None if no notice was found.
        return dict(row) if row else None
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)


# Define an async function that deletes a notice only if it belongs to the given user.
async def delete_notice(notice_id: UUID, user_id: UUID):
    """Delete a notice by id, but only if it belongs to the given user."""
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Delete the notice only when both the id and owning user match, returning its id if deleted.
        row = await conn.fetchrow(
            "DELETE FROM notices WHERE id = $1 AND user_id = $2 RETURNING id",
            notice_id,
            user_id
        )
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)
    # Return the deleted row's id as a dict, or None if nothing matched.
    return dict(row) if row else None

async def set_notice_pin(notice_id: UUID, user_id: UUID, user_email: str, is_pinned: bool):
    """Set the pinned status of a notice, but only if it belongs to the given user.

    Same reasoning as create_notice: the caller (the owner, since the WHERE
    clause enforces that) already knows their own email, so it's passed in
    and attached below instead of joining users again.
    """
    # Check out a connection from the pool.
    conn = await get_connection()
    # Use try/finally so the connection is always released, even on error.
    try:
        # Update the notice's pinned status only when both the id and owning user match, returning its id if updated.
        row = await conn.fetchrow(
            "UPDATE notices SET is_pinned = $1 WHERE id = $2 AND user_id = $3 "
            "RETURNING id, user_id, message, is_pinned, expires_at, created_at",
            is_pinned,
            notice_id,
            user_id
        )
    finally:
        # Sanity-check that the pool exists before trying to release into it.
        assert database.pool is not None, "Database pool not initialized"
        # Return the connection to the pool.
        await database.pool.release(conn)
    # Return the updated row (with email attached) as a dict, or None if nothing matched.
    if row is None:
        return None
    result = dict(row)
    result["user_email"] = user_email
    return result