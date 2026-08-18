# APIRouter lets us define these routes in their own file and plug them into
# main.py's app. Depends is how FastAPI hands the Supabase client and the
# signed-in user to an endpoint. HTTPException is how we return a chosen
# status code instead of letting an error surface as a 500.
from fastapi import APIRouter, Depends, HTTPException

# Client is only used as a type annotation on the injected argument.
from supabase import Client

# get_client builds the Supabase client once and returns the same one after.
from app.db import get_client

# get_current_user verifies the JWT and identifies who is calling.
# CurrentUser is what it hands back once the check passes.
from app.dependencies import CurrentUser, get_current_user

# The request and response shapes, kept in one place so the controller stays
# about routing.
from app.models.reaction import ReactionSummary, ReactionToggle

# notice_service is asked whether the notice in the path exists.
# reaction_service does the toggling.
from app.services import notice_service, reaction_service

# Reactions hang off a notice, so they sit under the same /notices prefix.
# They get their own router and their own file because they are a separate
# concern with a separate service behind them, and their own tag keeps them
# grouped separately on the /docs page.
router = APIRouter(prefix="/notices", tags=["reactions"])


# POST /notices/{notice_id}/reactions
# Turns one reaction on, or off if the caller already had it on.
#
# Requires a valid token. Adding get_current_user to the signature is what
# makes that true: FastAPI runs the dependency first and answers 401 without
# ever entering this function if the token is missing, expired or forged.
#
# 200 rather than 201, because this is a toggle. Half the calls delete a row
# rather than create one, and answering 201 for those would be a lie.
#
# The whole updated summary comes back rather than just an acknowledgement,
# so the caller can render the new counts without a follow up GET.
@router.post("/{notice_id}/reactions", response_model=ReactionSummary)
def toggle_reaction(
    notice_id: int,
    reaction: ReactionToggle,
    client: Client = Depends(get_client),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Checked here rather than in reaction_service, which owns only the
    # notice_reactions table. A missing thing named in the URL path is what
    # 404 is for, so mapping it is fair work for the controller.
    #
    # Without this the insert would fail on the foreign key and surface as an
    # unexplained 500 instead.
    #
    # There is a gap between this check and the write, so a notice deleted in
    # between would still produce that 500. It needs the notice to be removed
    # in the same instant somebody reacts to it, and the answer either way is
    # that the reaction did not happen.
    if notice_service.get_notice(client, notice_id) is None:
        raise HTTPException(status_code=404, detail="Notice not found")

    # The service refuses a reaction kind it does not recognise with a
    # ValueError. The model should have caught that first, so this is the
    # belt and braces path, mapped to the same 422 FastAPI would have used.
    try:
        return reaction_service.toggle_reaction(
            client,
            notice_id,
            user_id=current_user.user_id,
            reaction_type=reaction.reaction_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
