"""
Notice Board - Lambda backend (MongoDB edition, corkboard UI)

Routes (API Gateway HTTP API, payload format 2.0):
  GET    /notices        -> list all notices
  POST   /notices        -> create a notice   {title, content, bg_color, text_color}
  PUT    /notices/{id}   -> partially update a notice (position, colors, title, content)
  DELETE /notices/{id}   -> delete a notice by id

Board rules enforced here (mirror the frontend corkboard UI):
  - Max MAX_NOTICES notices on the board at once
  - New notices are dropped near the top-left corner with a slight cascade
    offset so they don't perfectly overlap
  - Each notice tracks x/y (percentage position on the board) and z
    (stacking order), bumped on every create/move so the most recently
    touched notice sits on top

MongoDB connection settings come from environment variables (set by
Terraform on the Lambda function):
  MONGO_HOST      - private IP / DNS name of the EC2 box running MongoDB
  MONGO_PORT      - defaults to 27017
  MONGO_DB        - defaults to "noticeboard"
  MONGO_USER      - optional, if MongoDB auth is enabled
  MONGO_PASSWORD  - optional, if MongoDB auth is enabled

The Mongo client is created at module scope so warm Lambda invocations
reuse the same connection instead of reconnecting every request.
"""

import json
import logging
import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_DB = os.environ.get("MONGO_DB", "noticeboard")
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")

MAX_NOTICES = 15
DEFAULT_BG_COLOR = "#fff59d"
DEFAULT_TEXT_COLOR = "#1c1e21"

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}

_client = None


def _get_collection():
    """Lazily create (and reuse) the MongoDB client across warm invocations."""
    global _client
    if _client is None:
        if MONGO_USER and MONGO_PASSWORD:
            uri = (
                f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@"
                f"{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
            )
        else:
            uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
        logger.info("Connecting to MongoDB at %s:%s", MONGO_HOST, MONGO_PORT)
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000,
        )
    return _client[MONGO_DB]["notices"]


def _response(status_code, body=None):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body) if body is not None else "",
    }


def _serialize(doc):
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def _next_z(collection):
    top = collection.find_one(sort=[("z", -1)])
    return (top.get("z", 0) if top else 0) + 1


def handler(event, context):
    try:
        method = event["requestContext"]["http"]["method"]
        raw_path = event["requestContext"]["http"]["path"]
    except KeyError:
        # Fall back for local testing / REST API (v1) style events.
        method = event.get("httpMethod", "GET")
        raw_path = event.get("path", "/")

    logger.info("%s %s", method, raw_path)

    if method == "OPTIONS":
        return _response(200)

    try:
        collection = _get_collection()

        if method == "GET" and raw_path.rstrip("/") == "/notices":
            docs = list(collection.find().sort("z", 1))
            return _response(200, [_serialize(d) for d in docs])

        if method == "POST" and raw_path.rstrip("/") == "/notices":
            count = collection.count_documents({})
            if count >= MAX_NOTICES:
                return _response(400, {"error": f"board is full ({MAX_NOTICES} notices max)"})

            payload = json.loads(event.get("body") or "{}")
            title = (payload.get("title") or "").strip()
            content = (payload.get("content") or "").strip()

            if not title:
                return _response(400, {"error": "title is required"})

            # Slight cascade near the top-left corner so new notices don't
            # perfectly stack on top of each other before the user moves them.
            step = count % 5
            doc = {
                "title": title,
                "content": content,
                "bg_color": payload.get("bg_color") or DEFAULT_BG_COLOR,
                "text_color": payload.get("text_color") or DEFAULT_TEXT_COLOR,
                "x": 3 + step * 3,
                "y": 4 + step * 3,
                "z": _next_z(collection),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            result = collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return _response(201, _serialize(doc))

        if method in ("PUT", "PATCH"):
            path_params = event.get("pathParameters") or {}
            notice_id = path_params.get("id")
            if not notice_id:
                return _response(400, {"error": "missing notice id"})
            try:
                oid = ObjectId(notice_id)
            except InvalidId:
                return _response(400, {"error": "invalid notice id"})

            payload = json.loads(event.get("body") or "{}")
            updates = {}

            if "title" in payload:
                title = (payload.get("title") or "").strip()
                if not title:
                    return _response(400, {"error": "title cannot be empty"})
                updates["title"] = title
            if "content" in payload:
                updates["content"] = (payload.get("content") or "").strip()
            if "bg_color" in payload:
                updates["bg_color"] = payload["bg_color"]
            if "text_color" in payload:
                updates["text_color"] = payload["text_color"]
            if "x" in payload:
                updates["x"] = float(payload["x"])
            if "y" in payload:
                updates["y"] = float(payload["y"])
            if "z" in payload:
                updates["z"] = int(payload["z"])

            if not updates:
                return _response(400, {"error": "no fields to update"})

            updated = collection.find_one_and_update(
                {"_id": oid},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
            )
            if not updated:
                return _response(404, {"error": "notice not found"})
            return _response(200, _serialize(updated))

        if method == "DELETE":
            path_params = event.get("pathParameters") or {}
            notice_id = path_params.get("id")
            if not notice_id:
                return _response(400, {"error": "missing notice id"})
            try:
                oid = ObjectId(notice_id)
            except InvalidId:
                return _response(400, {"error": "invalid notice id"})

            result = collection.delete_one({"_id": oid})
            if result.deleted_count == 0:
                return _response(404, {"error": "notice not found"})
            return _response(200, {"deleted": notice_id})

        return _response(404, {"error": f"no route for {method} {raw_path}"})

    except PyMongoError as exc:
        logger.exception("MongoDB error")
        return _response(502, {"error": "database unavailable", "detail": str(exc)})
    except Exception as exc:  # noqa: BLE001 - top-level Lambda safety net
        logger.exception("Unhandled error")
        return _response(500, {"error": "internal server error", "detail": str(exc)})