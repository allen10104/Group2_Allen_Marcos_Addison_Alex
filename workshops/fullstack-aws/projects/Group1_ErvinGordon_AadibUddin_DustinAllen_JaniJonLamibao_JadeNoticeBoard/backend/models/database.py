# asyncpg: async PostgreSQL driver used to talk to the Supabase database
from typing import Optional

import asyncpg
# os: used to read environment variables (keeps secrets out of source code)
import os
# load_dotenv: pulls key/value pairs from a local .env file into the environment
from dotenv import load_dotenv


# Load variables from .env into the process environment before we read them
load_dotenv()

# Read the DATABASE_URL from the environment, which is set in .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Module-level connection pool, shared across all requests.
# Starts as None until connect_to_db() initializes it.
pool: Optional[asyncpg.Pool] = None

async def connect_to_db():
    """Create the shared connection pool once, on app startup.

    Uses a global so every part of the app reuses the same pool instead of
    opening a new connection per request. Safe to call multiple times --
    it only creates the pool if one doesn't already exist.
    """
    global pool
    if pool is None:
        # Connect to the database and create a connection pool.(.create_pool() is an async context manager that returns a pool object.)
        # statement_cache_size=0: Supabase's pooler runs in transaction mode (pgbouncer),
        # which doesn't support asyncpg's prepared-statement caching -- disabling it here
        # avoids "prepared statement already exists" errors on repeated queries.
        pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)

async def disconnect_from_db():
    """Close the shared connection pool cleanly, e.g. on app shutdown.

    Guards against calling close() on a pool that was never created or
    was already closed.
    """
    #global keyword allows us to modify the module-level pool variable from within this function.
    global pool
    if pool is not None:
        # Close the connection pool and set it back to None.
        await pool.close()
        pool = None

async def get_connection():
    """Get a connection from the shared pool.

    Raises an error if the pool hasn't been initialized yet.
    """
    if pool is None:
        raise RuntimeError("Database connection pool not initialized. Call connect_to_db() first.")
    
    # .aquire() is an async context manager that returns a connection object.
    return await pool.acquire()
