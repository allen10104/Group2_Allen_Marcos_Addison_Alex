# This file handles the database connection and provides utility functions 
# for interacting with the MongoDB database.
# It is the only file that knows about the database connection and 
# the database name, so other parts of the application should use the 
# `get_db()` function to access the database.

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

# model level variables to hold the database client and database instance
# designed to be created one time and reused throughout the application
# start as none because at import time, the database connection has not been established yet

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


# Defines the function that opens the connection
def connect() -> None:
    global _client, _db
    # creates the actual connection object usign teh atlas url in .env/config
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    # then from the database client, we get the database instance using the name in .env/config
    _db = _client[settings.mongodb_db_name]

# Defines the function that closes the connection
def disconnect() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None

# Defines the function that returns the database instance
# This is the function that every other part of the application should use to access the database
def get_db() -> AsyncIOMotorDatabase:
    # If someone tries to query the database before the connection has been established, 
    # we raise an error
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect() during app startup.")
    return _db

# Function ia async becasue Motor operations are all awaitable
# Non blocking I/O operations which is why we are using Motor 
async def ensure_indexes() -> None:
    db = get_db()
    # access the user collection and create a unique index on the email field
    await db.users.create_index("email", unique=True)
    # exist for query seed
    # status (used for approval query to fllter PENDING/APPROVED/REJECTED) 
    await db.notices.create_index("status")
    # and author_id get queried often. Having this speeds up process
    await db.notices.create_index("author_id")
    # ensures each invite code is unique and can only be used once.
    await db.invite_codes.create_index("code", unique=True)
    