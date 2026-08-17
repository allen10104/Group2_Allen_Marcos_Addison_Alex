// Import the shared JSON-fetch helper from client.js.
import { request } from './client';

// Fetches every notice on the board. No auth required — read access is public.
export function getAllNotices() {
  return request('/notices/');
}

// Fetches a single notice by its id. Also public.
export function getNotice(id) {
  return request(`/notices/${id}`);
}

// Creates a new notice. Requires an auth token since posting is a write action.
// isPinned and expiresInDays default so callers only need to pass what they care about.
export function createNotice({ message, isPinned = false, expiresInDays = null }, token) {
  return request('/notices/', {
    method: 'POST',
    body: {
      message,
      // Translate the JS camelCase params into the snake_case keys the API expects.
      is_pinned: isPinned,
      expires_in_days: expiresInDays,
    },
    token,
  });
}

// Deletes a notice by id. Requires auth since deleting is a write action.
export function deleteNotice(id, token) {
  return request(`/notices/${id}`, {
    method: 'DELETE',
    token,
  });
}

// Pins or unpins an existing notice. PATCH because it's a partial update
// (only the pinned flag changes), not a full replacement of the notice.
export function setPin(id, isPinned, token) {
  return request(`/notices/${id}/pin`, {
    method: 'PATCH',
    body: { is_pinned: isPinned },
    token,
  });
}