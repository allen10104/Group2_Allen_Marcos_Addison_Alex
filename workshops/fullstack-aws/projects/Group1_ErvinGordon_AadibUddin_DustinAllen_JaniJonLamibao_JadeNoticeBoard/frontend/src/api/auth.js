// Import the shared JSON-fetch helper from client.js.
import { request } from './client';

// Registers a new user account.
export function register(email, password) {
  // Delegate to the shared request() helper, which JSON-encodes the body and handles errors.
  return request('/auth/register', {
    // Registration is a POST since it creates a new resource.
    method: 'POST',
    // Send email/password as the JSON request body.
    body: { email, password },
  });
}

// Logs a user in and returns the auth token response.
export async function login(email, password) {
    // OAuth2's password-grant login endpoint expects form-urlencoded data, not JSON,
    // and expects the email under the field name "username" — hence the manual fetch below
    // instead of using the shared request() helper.
    const formBody = new URLSearchParams({
        username: email,
        password: password,
    });

    // Call the login endpoint directly with a form-encoded body.
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
    // Login is a POST since it's submitting credentials to be processed.
    method: 'POST',
    headers: {
      // Content type must match the URLSearchParams body format, not JSON.
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    // Attach the form-encoded credentials as the request body.
    body: formBody,
    });

    // fetch() doesn't throw on HTTP error statuses, so check response.ok manually.
    if (!response.ok) {
    // Try to read a JSON error body; fall back to an empty object if parsing fails.
    const errorBody = await response.json().catch(() => ({}));
    // Prefer the backend's error detail message, otherwise report the raw HTTP status.
    throw new Error(errorBody.detail || `Login failed with status ${response.status}`);
    }
  // Success: parse and return the JSON response (expected to contain the auth token).
  return response.json();
}