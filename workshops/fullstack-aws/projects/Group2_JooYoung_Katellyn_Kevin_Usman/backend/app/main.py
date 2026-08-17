import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import notices, uploads
from .db import ensure_table

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
origins = ["*"] if CORS_ORIGINS.strip() == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]

app = FastAPI(title="Notice Board API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Everything the frontend calls lives under /api/* — that's the path pattern
# CloudFront's second cache behavior routes to this instance.
app.include_router(notices.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    ensure_table()


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Local-dev only: serve uploaded images directly when there's no S3 bucket
# configured (see backend/app/uploads.py). In production this path is never
# reached — CloudFront's /uploads/* behavior serves images straight from S3.
if not os.environ.get("S3_UPLOADS_BUCKET"):
    local_dir = Path(uploads.LOCAL_UPLOAD_DIR)
    local_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(local_dir)), name="uploads")
