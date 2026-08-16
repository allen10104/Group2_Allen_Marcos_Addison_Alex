from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.notice_router import router as notice_router

# Creates the main FastAPI application
app = FastAPI(
    title="Group 3 Notice Board API"
)

# Allows the local React frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adds all of the notice routes to the main application
app.include_router(notice_router)


# Simple route used to make sure the backend is running
@app.get("/")
def root():
    return {
        "message": "Notice Board API is running"
    }