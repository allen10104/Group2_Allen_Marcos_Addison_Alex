// Base API URL, injected at build time from the VITE_API_URL env var (e.g. .env, .env.production).
const BASE_URL = import.meta.env.VITE_API_URL;

// Shared fetch wrapper used by every API call in the app.
// path: the endpoint path appended to BASE_URL (e.g. '/notices').
// method: HTTP verb, defaults to GET.
// body: JS object to send as the JSON request body (omitted for GET/DELETE etc.).
// token: optional auth token; when present it's sent as a Bearer token.
export async function request(path, { method = 'GET', body, token } = {}) {
  // Every request sends JSON, so this header is always included.
  const headers = {
    'Content-Type': 'application/json',
  };
  // Only attach the Authorization header when a token was actually passed in.
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // Build the full URL and fire the request; JSON-encode the body if one was given.
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  // fetch() only rejects on network failure, not on HTTP error status codes,
  // so non-2xx responses have to be checked and turned into thrown errors manually.
  if (!response.ok) {
    const error = await response.json();
    // Prefer the backend's error message if it sent one, otherwise fall back to a generic message.
    throw new Error(error.detail || 'Request failed');
  }
  // Success: parse and return the JSON payload to the caller.
  return response.json();
}