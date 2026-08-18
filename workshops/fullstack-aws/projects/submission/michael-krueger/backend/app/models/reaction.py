# Literal is what restricts reaction_type to the three values the database
# allows. get_args reads those values back out, so the tuple below and the
# type above can never disagree.
from typing import Literal, get_args

# BaseModel defines the shape of a request or response body. Field is used
# here for the default factories, since a mutable default like {} or []
# cannot be written directly on a model.
from pydantic import BaseModel, Field


# The three kinds of reaction. Declared as a Literal rather than a plain str
# so FastAPI rejects anything else with a 422 before the request reaches the
# service, and so the accepted values appear on the /docs page.
#
# This must stay in step with the CHECK constraint on
# notice_reactions.reaction_type. The database is the final word: a value
# that got past this would still be refused there.
ReactionType = Literal["like", "heart", "laugh"]

# The same three values as a tuple, derived from the type rather than typed
# out a second time. Anything iterating over the reaction kinds, such as the
# counting in reaction_service, reads this.
REACTION_TYPES = get_args(ReactionType)


# The shape of the body POST /notices/{notice_id}/reactions expects.
#
# notice_id is not in here. It comes from the URL, and user_id comes from the
# token, so the body carries only the one thing the caller actually chooses.
# That is what makes it impossible to react on somebody else's behalf.
class ReactionToggle(BaseModel):
    reaction_type: ReactionType


# How a notice's reactions are reported.
#
# counts is every reaction kind against the number of people who picked it,
# across all users. All three keys are always present, including the ones
# nobody has used, so a frontend can render a row of buttons with numbers
# without checking whether each key exists.
#
# my_reactions is which kinds the person asking has active right now. It is
# empty for an anonymous viewer, who still sees the counts. That split is the
# whole point of the optional authentication on GET /notices: everybody sees
# the same totals, and only a signed in caller learns which of them are
# theirs.
#
# The defaults exist so a notice with no reactions still validates against
# this model without the service having to build the empty case by hand.
class ReactionSummary(BaseModel):
    counts: dict[str, int] = Field(
        default_factory=lambda: {reaction: 0 for reaction in REACTION_TYPES}
    )
    my_reactions: list[str] = Field(default_factory=list)
