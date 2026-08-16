from app.repositories.notice_repository import (
    create_notice,
    delete_notice,
    get_all_notices,
)


# Handles the request to get all notices
def list_notices():
    return get_all_notices()


# Handles the logic for creating a new notice
def add_notice(name: str, message: str, priority: str):
    return create_notice(name, message, priority)


# Handles the logic for removing a notice
def remove_notice(notice_id: str):
    return delete_notice(notice_id)