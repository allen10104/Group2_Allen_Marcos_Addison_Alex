# DeclarativeBase is the modern SQLAlchemy 2.x starting point for models.
from sqlalchemy.orm import DeclarativeBase


# Every model class in app/models will inherit from Base. This is what
# turns a normal Python class into a database table SQLAlchemy knows about.
class Base(DeclarativeBase):
    pass