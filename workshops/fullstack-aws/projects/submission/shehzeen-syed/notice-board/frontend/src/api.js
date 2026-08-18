// Every network call the frontend makes goes through this module.
// The JWT is decoded client-side (never verified) just to read the
// username/is_admin claims for UI purposes — the backend re-verifies
// the signature on every protected request, so this is display-only.

const API_URL = import.meta.env.VITE_API_URL

async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message =
      typeof body.detail === 'string' ? body.detail : body.detail ? JSON.stringify(body.detail) : `Request failed: ${res.status}`
    throw new Error(message)
  }
  if (res.status === 204) return null
  return res.json()
}

export function fetchNotices() {
  return request('/notices')
}

export function postNotice(message) {
  return request('/notices', { method: 'POST', body: JSON.stringify({ message }) })
}

export function deleteNotice(id) {
  return request(`/notices/${id}`, { method: 'DELETE' })
}

export function editNotice(id, message) {
  return request(`/notices/${id}`, { method: 'PUT', body: JSON.stringify({ message }) })
}

export function setNoticePinned(id, pinned) {
  return request(`/notices/${id}/pin`, { method: 'PATCH', body: JSON.stringify({ pinned }) })
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem('token', data.access_token)
  return data
}

export async function register(username, email, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
  localStorage.setItem('token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('token')
}

export function isLoggedIn() {
  return !!localStorage.getItem('token')
}

export function getUsername() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub || null
  } catch {
    return null
  }
}

export function getIsAdmin() {
  const token = localStorage.getItem('token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return !!payload.is_admin
  } catch {
    return false
  }
}
