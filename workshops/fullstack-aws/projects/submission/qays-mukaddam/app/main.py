# FastAPI is the class we use to create the actual application instance,
# and the framework that turns our controller functions into real HTTP
# routes (GET, POST, DELETE, etc).
from fastapi import FastAPI

# CORSMiddleware controls which websites/origins are allowed to call this
# API from a browser. Without it, the React frontend running on a different
# port (like localhost:5173) would get blocked by the browser's CORS policy.
from fastapi.middleware.cors import CORSMiddleware

# Import the router that holds the /notices endpoints.
from backend.controllers.notice_controller import router as notice_router

# Import the router that holds the /register and /login endpoints.
from backend.controllers.auth_controller import router as auth_router

# Base is what our models (like Notice, User) inherit from. engine is the
# connection to PostgreSQL. Together they let us auto-create tables.
from backend.database.base import Base
from backend.database.session import engine

# Import the routers that hold the comment and like endpoints.
from backend.controllers.comment_controller import router as comment_router
from backend.controllers.like_controller import router as like_router

# Creates all tables defined by models inheriting from Base, if they
# don't already exist yet. Importing auth_router above (which imports
# the User model, indirectly) is what makes SQLAlchemy aware of the
# "users" table before this line runs.
Base.metadata.create_all(bind=engine)

# Create the FastAPI application.
app = FastAPI()

# Allow the React frontend (running on localhost during development) to
# call this API. We'll narrow allow_origins to the real deployed frontend
# URL once we know it.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_origins=["http://student-qays-noticeboard.s3-website-us-east-1.amazonaws.com", "https://d1iv7abo9yxszk.cloudfront.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register both routers so their routes become part of the app.
app.include_router(notice_router)
app.include_router(auth_router)

# Register the comment and like routers so their routes become part of the app.
app.include_router(comment_router)
app.include_router(like_router)