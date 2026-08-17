"""A single, shared MongoClient for the whole process."""

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings


@lru_cache(maxsize=1)
def get_database() -> Database:
    """One MongoClient per process, reused for every request.

    WHY THIS MATTERS MORE THAN IT LOOKS. MongoClient owns a connection pool and does
    a TLS handshake plus a topology scan on first use — roughly 300-800ms against
    Atlas. Creating one per request would add that to every single call. On Lambda,
    where the module stays loaded between warm invocations, this cache is the
    difference between a 60ms response and a 700ms one.

    tz_aware=True is the important flag. BSON stores datetimes as UTC milliseconds
    with no zone, and PyMongo hands them back NAIVE by default. Our domain uses
    timezone-aware UTC, and comparing an aware datetime to a naive one raises
    `TypeError: can't compare offset-naive and offset-aware datetimes` — which would
    blow up inside Notice.is_expired() on the very first board query. This flag makes
    PyMongo return aware UTC datetimes and the problem never exists.

    serverSelectionTimeoutMS: the 30-second default means a bad connection string
    hangs your Lambda until it times out. Five seconds fails fast with a clear error.
    """
    client = MongoClient(
        settings.mongodb_uri,
        tz_aware=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        retryWrites=True,
    )
    return client[settings.mongodb_db]
