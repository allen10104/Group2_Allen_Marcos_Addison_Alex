# Client is the supabase-py client. It is only used as a type annotation on
# the first argument of every function here.
from supabase import Client

# The three allowed kinds, and the request model's own list of them, so this
# module and the API agree on the vocabulary without repeating it.
from app.models.reaction import REACTION_TYPES

# The table this service reads and writes. Named once so a rename is a
# one-line change rather than a search across the file.
TABLE = "notice_reactions"

# The columns every read here needs. id is left out on purpose for the
# summary queries: counting does not need it, and a narrower select means
# less to send back for what can be a lot of rows.
SUMMARY_COLUMNS = "notice_id, user_id, reaction_type"


# This module is the only place in the app that talks to the notice_reactions
# table, the same way notice_service owns notices and auth_service owns
# users.
#
# Nothing here raises HTTPException or knows about status codes. Whether a
# missing notice is a 404 is the controller's decision, and this module is
# never told about it.
#
# Note what is deliberately absent: there is no check here that the notice
# exists. That check needs the notices table, and doing it from this module
# would either duplicate notice_service's queries or create an import cycle
# between the two services. The controller does it instead, which is a fair
# place for it: a missing thing named in the URL path is what 404 is for.


# The empty summary: every kind at zero, nothing of the caller's own.
#
# Used for a notice that has just been created, which cannot have reactions
# yet, so the response still carries a full reactions block rather than a
# hole the frontend has to guard against.
def empty_summary():
    return {
        "counts": {reaction: 0 for reaction in REACTION_TYPES},
        "my_reactions": [],
    }


# Turns raw reaction rows for one notice into the summary shape.
#
# Private to this module, since it takes rows that have already been fetched
# and is only useful to the two functions below.
#
# current_user_id is None for an anonymous viewer, and then my_reactions
# stays empty. That is the only difference between what a signed in caller
# and a signed out caller are told: the counts are the same either way.
#
# counts is built from the known kinds first, so all three are always
# present, then incremented with .get so a value the database somehow holds
# that this code has not heard of is still counted rather than silently
# dropped or crashing on a missing key.
def _summarise(rows, current_user_id):
    counts = {reaction: 0 for reaction in REACTION_TYPES}
    mine = set()

    for row in rows:
        reaction = row["reaction_type"]

        counts[reaction] = counts.get(reaction, 0) + 1

        if current_user_id is not None and row["user_id"] == current_user_id:
            mine.add(reaction)

    # Sorted so the list comes back in a stable order. The unique constraint
    # already rules out duplicates, so the set is about deterministic output
    # rather than deduplication.
    return {"counts": counts, "my_reactions": sorted(mine)}


# The summary for one notice.
def get_reaction_summary(client: Client, notice_id: int, current_user_id=None):
    response = (
        client.table(TABLE)
        .select(SUMMARY_COLUMNS)
        .eq("notice_id", notice_id)
        .execute()
    )

    return _summarise(response.data or [], current_user_id)


# The summaries for a whole page of notices, in one query.
#
# This is what keeps listing the board from becoming N+1 queries. Asking per
# notice would be simpler to write and would mean twenty round trips to show
# twenty notices, each one costing a network hop to Supabase. One "in" query
# fetches every reaction for the batch, and the grouping happens here in
# memory, which is free by comparison.
#
# Returns a dict keyed by notice id, with an entry for every id that was
# asked about, including the ones nobody has reacted to. That way the caller
# can attach a summary to every notice without checking whether the key is
# there.
#
# The empty guard matters: an "in" filter with an empty list is a query that
# can only return nothing, so it is a round trip with a guaranteed answer.
def get_summaries_for_notices(client: Client, notice_ids, current_user_id=None):
    notice_ids = list(notice_ids)

    if not notice_ids:
        return {}

    response = (
        client.table(TABLE)
        .select(SUMMARY_COLUMNS)
        .in_("notice_id", notice_ids)
        .execute()
    )

    rows_by_notice = {notice_id: [] for notice_id in notice_ids}

    for row in response.data or []:
        # A row for a notice that was not asked about cannot normally happen,
        # since the filter above is what selected them. Guarded anyway so a
        # surprise cannot raise a KeyError in the middle of building a list
        # the caller is about to return.
        rows_by_notice.setdefault(row["notice_id"], []).append(row)

    return {
        notice_id: _summarise(rows, current_user_id)
        for notice_id, rows in rows_by_notice.items()
    }


# Adds a reaction, or removes it if the same user already has that kind
# active on that notice.
#
# Returns the notice's summary as it stands afterwards, so one request tells
# the caller both that it worked and what the counts now are, with no follow
# up read from the frontend.
#
# The toggle is a read then a write rather than one statement, because the
# two directions are different operations. The unique constraint on
# (notice_id, user_id, reaction_type) is what makes the read conclusive:
# there is either exactly one matching row or none.
#
# Two clicks arriving at the same instant could both read "no row" and both
# try to insert, and the second would be refused by that unique constraint
# with a 500 rather than a tidy answer. It needs a double click on a slow
# connection to happen at all, and the outcome the user wanted, the reaction
# being on, is true either way.
#
# Reactions are per user, so two people can each hold their own like on the
# same notice: the constraint includes user_id, and the delete below is
# filtered by it. Nobody can toggle anybody else's reaction off.
def toggle_reaction(
    client: Client,
    notice_id: int,
    user_id: int,
    reaction_type: str,
):
    # The model already restricts this to the three kinds, so this only
    # catches a caller that reached the service some other way, such as a
    # test or a future background job. Cheap, and it keeps the rule true of
    # the service rather than only of the HTTP layer.
    if reaction_type not in REACTION_TYPES:
        raise ValueError(
            f"reaction_type must be one of: {', '.join(REACTION_TYPES)}"
        )

    existing = (
        client.table(TABLE)
        .select("id")
        .eq("notice_id", notice_id)
        .eq("user_id", user_id)
        .eq("reaction_type", reaction_type)
        .maybe_single()
        .execute()
    )

    # maybe_single can return None for the whole response rather than just
    # for .data, depending on how the request was answered, so the response
    # is checked before its data is.
    found = existing.data if existing is not None else None

    if found:
        # Deleted by primary key rather than by the three way filter again,
        # which is both cheaper and immune to matching anything other than
        # the exact row just read.
        client.table(TABLE).delete().eq("id", found["id"]).execute()
    else:
        client.table(TABLE).insert(
            {
                "notice_id": notice_id,
                "user_id": user_id,
                "reaction_type": reaction_type,
            }
        ).execute()

    # Re-read rather than adjusting a number in memory. It costs one more
    # query and it means the counts returned are what the database actually
    # holds, including reactions other people added while this one was in
    # flight.
    return get_reaction_summary(client, notice_id, current_user_id=user_id)
