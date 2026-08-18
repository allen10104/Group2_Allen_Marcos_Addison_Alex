import client from "./client";

// POST /notices/{noticeId}/reactions
//
// Turns one reaction on, or off if this user already had it on. The backend
// decides which of the two it is by looking for an existing row, so there is
// no separate add and remove call to choose between here.
//
// Returns the notice's updated summary, { counts, my_reactions }, which is
// what lets the bar redraw from the response rather than guessing at the new
// numbers or refetching the whole board.
//
// Goes through the shared Axios client, so the token is attached
// automatically. That matters more here than on the public list call: this
// endpoint answers 401 without one.
//
// Errors are already shaped into a plain Error with a readable message and a
// status by the response interceptor, so nothing is caught here. ReactionBar
// catches and decides what to show.
export async function toggleReaction(noticeId, reactionType) {
  const response = await client.post(`/notices/${noticeId}/reactions`, {
    reaction_type: reactionType,
  });

  return response.data;
}
