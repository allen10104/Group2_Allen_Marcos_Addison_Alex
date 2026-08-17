import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

S3_BUCKET = os.environ.get("S3_UPLOADS_BUCKET")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
# Local-dev fallback so image uploads work without any AWS credentials.
# main.py mounts this directory at /uploads when S3_BUCKET isn't set.
LOCAL_UPLOAD_DIR = os.environ.get("LOCAL_UPLOAD_DIR", str(Path(__file__).resolve().parents[1] / "_local_uploads"))

CONTENT_TYPE_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}
MAX_BYTES = 5 * 1024 * 1024  # 5MB


@router.post("/uploads", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in CONTENT_TYPE_EXT:
        raise HTTPException(400, f"unsupported content type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(400, "file too large (max 5MB)")

    key = f"{uuid.uuid4().hex}.{CONTENT_TYPE_EXT[file.content_type]}"

    if S3_BUCKET:
        import boto3  # imported lazily so local dev without boto3-configured creds still works

        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=contents, ContentType=file.content_type)
    else:
        Path(LOCAL_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        (Path(LOCAL_UPLOAD_DIR) / key).write_bytes(contents)

    return {"key": key}
