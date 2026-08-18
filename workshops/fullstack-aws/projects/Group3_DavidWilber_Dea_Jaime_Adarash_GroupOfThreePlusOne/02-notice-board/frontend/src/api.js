// Replace with your API Gateway Invoke URL after terraform apply
const API_URL = import.meta.env.VITE_API_URL || ''

export async function getNotices() {
  const res = await fetch(`${API_URL}/notices`)
  return res.json()
}

export async function createNotice(notice) {
  const res = await fetch(`${API_URL}/notices`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(notice),
  })
  return res.json()
}

export async function deleteNotice(id) {
  const res = await fetch(`${API_URL}/notices/${id}`, { method: 'DELETE' })
  return res.json()
}
