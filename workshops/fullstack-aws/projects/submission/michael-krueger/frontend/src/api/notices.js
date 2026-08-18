import client from "./client";

// Every call goes through the shared Axios client, which attaches the token
// to the request automatically. That is the whole reason this file moved off
// fetch: posting and deleting now need an Authorization header, and putting
// it on by hand at three call sites is three chances to forget.
//
// Errors are already shaped into a plain Error with a readable message by
// the response interceptor, so nothing here catches. Each component catches
// and shows err.message, exactly as it did before.

// GET /notices
// Returns the notices as an array of
// { id, user_id, name, message, created_at }, already sorted newest first by
// the backend.
//
// Public, so this works whether or not anyone is signed in. The interceptor
// simply sends no Authorization header when there is no token.
export async function listNotices() {
  const response = await client.get("/notices");

  return response.data;
}

// POST /notices
// Creates one notice and returns the created row, including the user_id the
// backend took from the token.
//
// Requires a token. Note that the author is not sent in the body and cannot
// be: the backend reads it from the token and ignores anything the body says
// about it, so there is no way to post under another account from here.
export async function createNotice({ name, message }) {
  const response = await client.post("/notices", { name, message });

  return response.data;
}

// DELETE /notices/{id}
// Returns nothing on success.
//
// Requires a token, and the backend only allows it for whoever posted the
// notice. A 403 for somebody else's notice and a 404 for one that is already
// gone both arrive here as a thrown Error carrying the backend's message.
export async function deleteNotice(id) {
  await client.delete(`/notices/${id}`);

  return null;
}
