import axios from "axios";

// The backend's base URL, read from the environment rather than written in
// here. The API lives on localhost during development and behind API
// Gateway or CloudFront once deployed, and those are facts about a
// particular environment, not about this code.
//
// Vite only exposes variables whose names start with VITE_, and it inlines
// them at build time rather than reading them at runtime. So changing .env
// means restarting the dev server.
//
// The trailing slash is stripped so both "http://localhost:8001" and
// "http://localhost:8001/" work, rather than the second form producing a
// double slash that some servers answer and others reject.
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

// Where the token is kept between page loads.
//
// localStorage rather than a cookie because this API expects the token in an
// Authorization header, not a cookie, and because there is no server
// rendering here that would need to read it. The trade is that anything
// running on the page can read localStorage, so a script injection would
// expose the token. That is acceptable for a training project and is the
// same choice BankingApp made.
const TOKEN_KEY = "access_token";

// Fired when the interceptor below throws a token away, so AuthContext can
// clear its own state and the UI can react. A plain DOM event is used
// because the interceptor lives outside React and has no way to call a hook.
export const UNAUTHORIZED_EVENT = "noticeboard:unauthorized";

// Reads the stored token. Returns null when there is none.
//
// The token is stored verbatim, never JSON.stringify'd. Stringifying wraps
// it in literal double quotes, and it is read straight into the
// Authorization header, so the server would receive Bearer "eyJ..." and
// reject every authenticated request.
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// The one Axios instance the whole app uses.
//
// Everything goes through here so that the token, the base URL and the error
// shaping are all applied in one place. An api module that reached for fetch
// directly would silently skip all three.
const client = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attaches the token to every outgoing request.
//
// Read from storage on each request rather than captured once, so a login or
// a logout takes effect immediately without rebuilding the client.
//
// Requests are left unauthenticated when there is no token, which is what
// makes the public GET /notices work while logged out, and what lets
// /auth/login be called by someone who has no token yet.
client.interceptors.request.use((config) => {
  const token = getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Pulls a readable message out of an error response.
//
// FastAPI sends "detail" in two different shapes and this has to cope with
// both. Our own HTTPException calls send a plain string, but a body that
// fails Pydantic validation produces a list of objects like
// [{ loc, msg, type }] instead. Handing that list to a MUI Alert would crash
// the render with "Objects are not valid as a React child", so the list is
// flattened into one sentence here.
function extractErrorMessage(data, status) {
  const detail = data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg).filter(Boolean);

    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  return `The request failed with status ${status}.`;
}

// Turns every failure into a plain Error carrying a message fit to show a
// user, and a status for the few callers that need to branch on it.
//
// Doing this once here is what lets every component keep the shape it
// already had: catch the error, read err.message, put it in an Alert. None
// of them has to know that the API layer moved from fetch to Axios.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // No response at all means the request never got an answer: the backend
    // is down, the URL is wrong, or CORS blocked it. The browser
    // deliberately hides which, so this message covers all three.
    if (!error.response) {
      const networkError = new Error(
        "Could not reach the API. Check that the backend is running and that VITE_API_URL is correct."
      );
      networkError.status = 0;
      return Promise.reject(networkError);
    }

    const { status, data } = error.response;

    // A 401 on a normal request means the token is missing, expired or no
    // longer matches an account. Throwing it away here prevents the
    // confusing state where the app still looks logged in but every request
    // fails, which is exactly what happens when a 24 hour token runs out
    // while a tab is open.
    //
    // The /auth routes are excluded deliberately. A 401 from /auth/login is
    // an ordinary wrong password, not an expired session, and there is no
    // token to clear.
    const url = error.config?.url || "";

    if (status === 401 && !url.startsWith("/auth/")) {
      clearToken();
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }

    const friendlyError = new Error(extractErrorMessage(data, status));
    friendlyError.status = status;

    return Promise.reject(friendlyError);
  }
);

export default client;
