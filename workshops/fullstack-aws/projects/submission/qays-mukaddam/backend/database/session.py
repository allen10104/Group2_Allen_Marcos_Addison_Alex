# os.getenv reads environment variables, which is how we pick up DATABASE_URL.
import os

# load_dotenv copies the values out of the .env file into the environment,
# so the password never has to be written in the source code.
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fail loudly and early if the variable is missing, instead of a confusing
# error later.
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
    )

# The engine manages the pool of connections to PostgreSQL.
engine = create_engine(DATABASE_URL, echo=False)

# A Session is what we run queries through. autocommit=False means nothing
# is saved until we explicitly call db.commit().
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Hands a database session to a FastAPI endpoint and closes it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()