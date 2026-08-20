import json
import os
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from datetime import datetime, timezone

MONGO_HOST = os.environ["MONGO_HOST"]
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))

REACTION_EMOJIS = {"fire", "heart", "thumbsup"}


def get_collection():
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, serverSelectionTimeoutMS=5000)
    return client["noticeboard"]["notices"]


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path   = event.get("rawPath", "/")

    print(f"Request: {method} {path}")

    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": "",
        }

    try:
        if method == "GET" and path == "/notices":
            return get_notices()

        if method == "POST" and path == "/notices":
            body = json.loads(event.get("body") or "{}")
            return create_notice(body)

        if method == "POST" and path.startswith("/notices/") and path.endswith("/react"):
            notice_id = path.split("/")[-2]
            body = json.loads(event.get("body") or "{}")
            return react_to_notice(notice_id, body)

        if method == "DELETE" and path.startswith("/notices/"):
            notice_id = path.split("/")[-1]
            return delete_notice(notice_id)

        return response(404, {"error": f"Route not found: {method} {path}"})

    except Exception as e:
        print(f"Error: {e}")
        return response(500, {"error": str(e)})


def get_notices():
    notices = list(get_collection().find({}, {"_id": 1, "name": 1, "message": 1, "created_at": 1, "reactions": 1}))
    for n in notices:
        n["id"] = str(n.pop("_id"))
        n.setdefault("reactions", {emoji: 0 for emoji in REACTION_EMOJIS})
    return response(200, {"notices": notices})

def create_notice(data):
    name = data.get("name", "").strip()
    message = data.get("message", "").strip()
    if not name or not message:
        return response(400, {"error": "Missing 'name' or 'message' in request body"})

    notice = {
        "name": name,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reactions": {emoji: 0 for emoji in REACTION_EMOJIS},
    }

    get_collection().insert_one(notice)
    notice["id"] = str(notice.pop("_id"))
    return response(201, {"notice": notice})


def react_to_notice(notice_id, data):
    emoji = data.get("emoji", "")
    action = data.get("action", "")
    if emoji not in REACTION_EMOJIS:
        return response(400, {"error": f"Invalid emoji: {emoji}"})
    if action not in ("add", "remove"):
        return response(400, {"error": f"Invalid action: {action}"})

    try:
        object_id = ObjectId(notice_id)
    except InvalidId:
        return response(400, {"error": f"Invalid notice id: {notice_id}"})

    delta = 1 if action == "add" else -1
    result = get_collection().find_one_and_update(
        {"_id": object_id},
        {"$inc": {f"reactions.{emoji}": delta}},
        return_document=True,
    )
    if result is None:
        return response(404, {"error": "Notice not found"})

    # Clamp at zero in case of duplicate remove calls
    if result["reactions"][emoji] < 0:
        get_collection().update_one({"_id": object_id}, {"$set": {f"reactions.{emoji}": 0}})
        result["reactions"][emoji] = 0

    return response(200, {"id": notice_id, "reactions": result["reactions"]})


def delete_notice(notice_id):
    try:
        object_id = ObjectId(notice_id)
    except InvalidId:
        return response(400, {"error": f"Invalid notice id: {notice_id}"})

    result = get_collection().delete_one({"_id": object_id})
    if result.deleted_count == 0:
        return response(404, {"error": "Notice not found"})
    return response(200, {"deleted": notice_id})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
