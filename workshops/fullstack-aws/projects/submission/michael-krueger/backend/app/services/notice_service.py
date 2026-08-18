# Client is the supabase-py client. It is only used as a type annotation on
# the first argument of every function here.
from supabase import Client

# The request model, used as the argument type on create_notice.
from app.models.notice import NoticeCreate

# Reactions live in their own table and their own service. This module asks
# that one for the counts rather than querying notice_reactions itself, so
# each service still owns exactly one table.
from app.services import reaction_service

# The table this service reads and writes. Named once so a rename is a
# one-line change rather than a search across the file.
TABLE = "notices"

# The columns the API returns, matching the fields on NoticeOut.
#
# Listed explicitly rather than using "*" so that adding a column to the
# table later cannot start leaking it through the API. It also means the
# database sends back only what is actually used.
COLUMNS = "id, user_id, name, message, created_at"


# This module is the only place in the app that talks to the notices table.
#
# Every function takes the client as its first argument rather than reaching
# for get_client() itself. The controller injects it with Depends, which
# keeps the dependency visible at the call site and means these functions
# can be handed a stub client in a test without patching anything.
#
# Nothing here raises HTTPException or knows about status codes. A service
# that returns None or False leaves the controller to decide that "not
# found" means 404, which is what keeps the HTTP concerns in one layer and
# makes these functions reusable from somewhere that is not a web request,
# such as a scheduled cleanup job.


# Raised when a signed-in user tries to delete a notice somebody else posted.
#
# A named exception rather than a bool, because "you may not do that" and
# "there is no such notice" are different answers and the controller has to
# tell them apart to pick between 403 and 404. Returning False for both would
# collapse them into one.
#
# Deliberately not Python's built in PermissionError, which is a subclass of
# OSError and means a filesystem or process permission was refused. Reusing
# it here would make an ownership failure indistinguishable from a genuine
# operating system error in any except block further up.
#
# This is the layer that enforces ownership, and since the backend now holds
# the service_role key it is the only layer that does. Row level security is
# bypassed by that key, so the database will happily delete anybody's row if
# asked. The check below is the whole protection, not a convenience on top of
# a policy.
class NoticeOwnershipError(Exception):
    pass


# Returns every notice, newest first.
#
# The sort is done by the database rather than in Python because Postgres
# can use an index for it, and because sorting here would only ever be
# sorting one page of results once pagination is added.
#
# id descending is a tie breaker. created_at defaults to now() and two
# notices posted in the same instant would otherwise come back in whatever
# order Postgres felt like, which makes the list jump around between
# refreshes. Higher ids are newer, so this keeps the order stable.
#
# current_user_id is who is asking, or None for an anonymous viewer. It only
# affects the my_reactions part of each summary: the counts are the same for
# everybody, so a signed out visitor sees how popular a notice is without
# being told which reactions would be highlighted as theirs.
def list_notices(client: Client, current_user_id=None):
    response = (
        client.table(TABLE)
        .select(COLUMNS)
        .order("created_at", desc=True)
        .order("id", desc=True)
        .execute()
    )

    # supabase-py returns an object with the rows on .data. An empty board
    # is a perfectly normal answer, so an empty list is returned as is
    # rather than being treated as an error.
    notices = response.data or []

    if not notices:
        return notices

    # One query for every notice on the page, not one per notice. See
    # get_summaries_for_notices for why that matters.
    summaries = reaction_service.get_summaries_for_notices(
        client,
        [notice["id"] for notice in notices],
        current_user_id=current_user_id,
    )

    for notice in notices:
        # The fallback should never be reached, since the summaries are keyed
        # by the same ids that were just asked about. It is here so that a
        # surprise produces a notice with no reactions rather than a
        # KeyError that takes down the whole list.
        notice["reactions"] = summaries.get(
            notice["id"],
            reaction_service.empty_summary(),
        )

    return notices


# Finds a single notice by its id.
# Returns None so the caller knows the notice does not exist.
#
# maybe_single() asks for one row and hands back None when there is none.
# The plain single() would raise instead, which would turn an ordinary
# "already deleted" into an exception the controller has to catch.
def get_notice(client: Client, notice_id: int):
    response = (
        client.table(TABLE)
        .select(COLUMNS)
        .eq("id", notice_id)
        .maybe_single()
        .execute()
    )

    # maybe_single can return None for the whole response, not just for
    # .data, depending on how the request was answered. Checking the
    # response first avoids an AttributeError on the miss path.
    if response is None:
        return None

    return response.data


# Creates one notice and returns the row the database wrote, so the caller
# gets the generated id and created_at without a second query.
#
# Raises ValueError if either field is blank once trimmed. Pydantic's
# min_length already rejected the empty string, but "   " passes that check
# and would otherwise be saved as a blank notice that no one can see or
# explain. This is a business rule rather than a shape rule, which is why it
# lives here and not on the model.
#
# ValueError, not HTTPException, on purpose. The service has no opinion on
# what status code a blank name deserves, it just refuses to store one. The
# controller catches this and answers 422.
#
# Returns None if the insert wrote nothing.
#
# user_id is passed in by the controller, which takes it from the verified
# token and never from the request body. That is the point: NoticeCreate has
# no user_id field at all, so there is no way for a caller to post a notice
# in somebody else's name, however the body is crafted.
def create_notice(client: Client, notice: NoticeCreate, user_id: int):
    name = notice.name.strip()
    message = notice.message.strip()

    if not name or not message:
        raise ValueError("name and message cannot be blank")

    # id and created_at are left out so the database fills them in with the
    # identity sequence and now(). See schema.sql.
    response = (
        client.table(TABLE)
        .insert({"name": name, "message": message, "user_id": user_id})
        .execute()
    )

    if not response.data:
        return None

    created = response.data[0]

    # A notice that has just been written cannot have any reactions, but
    # NoticeOut still expects the block, so the empty one is attached here.
    # Building it rather than querying for it saves a round trip whose answer
    # is already known.
    created["reactions"] = reaction_service.empty_summary()

    return created


# Deletes one notice, if the user asking owns it.
#
# Returns True if it was deleted, False if there was no notice with that id.
# Raises NoticeOwnershipError if the notice exists but belongs to somebody
# else, which the controller turns into a 403.
#
# requesting_user_id comes from the verified token by way of the controller.
# The read has to happen before the delete either way, so checking ownership
# costs nothing extra: the row is already in hand.
#
# The order of the two checks matters and is deliberate. Missing is reported
# as missing even to a user who does not own it, so 404 comes before any
# ownership test. The alternative, answering 403 for a notice that does not
# exist, would let anyone probe which ids are real by watching the status
# code change.
#
# Two callers deleting the same notice at the same moment could both pass the
# check and one would get a True for a row the other removed. That does not
# matter on a notice board: the outcome the caller cares about, the notice
# being gone, is true either way. Ownership is not subject to that race,
# because a notice's user_id never changes after it is written.
def delete_notice(client: Client, notice_id: int, requesting_user_id: int):
    notice = get_notice(client, notice_id)

    if notice is None:
        return False

    if notice["user_id"] != requesting_user_id:
        raise NoticeOwnershipError("You can only delete your own notices")

    client.table(TABLE).delete().eq("id", notice_id).execute()

    return True
