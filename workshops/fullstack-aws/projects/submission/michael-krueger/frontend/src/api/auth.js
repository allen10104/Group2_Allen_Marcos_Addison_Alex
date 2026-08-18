import client from "./client";

// POST /auth/signup
// Creates an account and returns { id, username }.
//
// No token comes back from this call. The backend keeps signing up and
// logging in separate so there is one path that mints a token, so the caller
// has to log in afterwards to get one. AuthContext.signup does exactly that.
//
// A taken username arrives as a 409, which the response interceptor has
// already turned into an Error carrying the backend's own wording.
export async function signup(username, password) {
  const response = await client.post("/auth/signup", { username, password });

  return response.data;
}

// POST /auth/login
// Exchanges a username and password for a token.
//
// Returns the raw token string rather than the whole { access_token,
// token_type } body, because token_type is always "bearer" and the request
// interceptor in client.js is the only thing that ever needs to know that.
//
// Wrong credentials arrive as a 401 with a deliberately vague message, which
// the login page shows as is rather than guessing which half was wrong.
export async function login(username, password) {
  const response = await client.post("/auth/login", { username, password });

  return response.data.access_token;
}
