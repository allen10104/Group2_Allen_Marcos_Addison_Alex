from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.notice_router import router as notice_router

# Creates the main FastAPI application
app = FastAPI(
    title="QMMO Notice Board API"
)

# Allows both the local React frontend and the deployed CloudFront
# frontend to send requests to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://d1qrvfuf1egg8d.cloudfront.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adds all of the notice endpoints to the main application
app.include_router(notice_router)


# Simple route used to confirm that the backend is running
@app.get("/")
def root():
    return {
        "message": "Notice Board API is running"
    }