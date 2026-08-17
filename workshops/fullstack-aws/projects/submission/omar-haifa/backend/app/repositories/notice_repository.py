from bson import ObjectId

from app.db.database import notices_collection


# Gets all of the notices currently stored in MongoDB
def get_all_notices():
    notices = []

    # Goes through each MongoDB document and formats it for the API
    for notice in notices_collection.find():
        notices.append(
            {
                # MongoDB ObjectIds need to be converted to strings
                "id": str(notice["_id"]),
                "name": notice["name"],
                "message": notice["message"],

                # Older notices may not have priority yet, so Normal is used by default
                "priority": notice.get("priority", "Normal"),
            }
        )

    return notices


# Creates a new notice and stores it in MongoDB
def create_notice(name: str, message: str, priority: str):
    # Formats the notice before adding it to the database
    notice = {
        "name": name,
        "message": message,
        "priority": priority,
    }

    # Inserts the notice and gives us the ID MongoDB created
    result = notices_collection.insert_one(notice)

    # Returns the newly created notice in a format the API can use
    return {
        "id": str(result.inserted_id),
        "name": name,
        "message": message,
        "priority": priority,
    }


# Deletes a notice using its MongoDB ID
def delete_notice(notice_id: str):
    # Makes sure the ID is valid before trying to use it
    if not ObjectId.is_valid(notice_id):
        return False

    result = notices_collection.delete_one(
        {"_id": ObjectId(notice_id)}
    )

    # Returns True if a notice was actually deleted
    return result.deleted_count > 0