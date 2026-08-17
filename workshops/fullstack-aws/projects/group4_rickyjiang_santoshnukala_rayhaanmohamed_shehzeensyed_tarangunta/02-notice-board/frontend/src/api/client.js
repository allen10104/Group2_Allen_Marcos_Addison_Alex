/**
 * One place that talks to the backend.
 *
 * Every component calls these functions instead of using fetch() directly, so the
 * Authorization header, the base URL, JSON parsing, and error shaping are each
 * defined exactly once. When Tier 1 changes the base URL, or when a token expires and
 * everyone needs redirecting to login, there's a single file to touch.
 *
 * NOTE THE FIELD NAMES: the FastAPI backend returns snake_case (author_name,
 * category_label, access_token). We use them as-is rather than converting to
 * camelCase — one less transformation layer to get wrong, and what you see in
 * /docs is exactly what you see here.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'nb_token';
const USER_KEY = 'nb_user';

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  getUser: () => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setUser: (u) => localStorage.setItem(USER_KEY, JSON.stringify(u)),
};

/**
 * localStorage survives a refresh, which is what makes "stay logged in" work.
 *
 * The honest trade-off: localStorage is readable by any JavaScript on the page, so an
 * XSS bug means token theft. The more secure pattern is an httpOnly SameSite cookie
 * the JS can never read — but that needs the API and frontend to share a site (they
 * don't: CloudFront vs API Gateway) plus CSRF protection. For a workshop app with a
 * one-hour token this is the right call, and being able to explain the trade-off is
 * worth more than the trade-off itself.
 */

async function request(path, options = {}) {
  const token = tokenStore.get();

  const headers = { 'Content-Type': 'application/json', ...options.headers };
  // Only attach when we actually have one — sending "Bearer null" makes the server
  // reject a request that should have been treated as anonymous.
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  // 204 No Content (our DELETE) has an empty body; calling .json() on it throws
  // "Unexpected end of JSON input". Handle it before parsing.
  if (response.status === 204) return null;

  // Tolerate a non-JSON response (e.g. an API Gateway error page). Without the
  // catch you get a confusing parse error instead of the actual HTTP status.
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    // 401 = missing or expired token. Clear it so the app falls back to login
    // rather than looping on requests that will never succeed.
    if (response.status === 401) tokenStore.clear();

    const error = new Error(payload?.message || `Request failed with status ${response.status}`);
    error.status = response.status;
    error.fieldErrors = payload?.field_errors || null;   // snake_case from FastAPI
    throw error;
  }

  return payload;
}

// ---------------------------------------------------------------- auth

export async function login(username, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  tokenStore.set(data.access_token);
  const user = {
    username: data.username,
    full_name: data.full_name,
    department: data.department,
    roles: data.roles,
    can_publish: data.can_publish,
  };
  tokenStore.setUser(user);
  return user;
}

export function logout() {
  // Purely client-side: with stateless JWTs there's no server session to destroy.
  // The token stays technically valid until it expires — the trade-off documented in
  // jwt_service.py. Short expiry is the mitigation.
  tokenStore.clear();
}

// ---------------------------------------------------------------- notices

export function fetchNotices({ category } = {}) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  const q = params.toString();
  return request(`/api/notices${q ? `?${q}` : ''}`);
}

export const createNotice = (n) =>
  request('/api/notices', { method: 'POST', body: JSON.stringify(n) });

export const deleteNotice = (id) =>
  request(`/api/notices/${id}`, { method: 'DELETE' });

export const health = () => request('/api/health');
