import { useEffect, useState } from 'react'
import {
  fetchNotices,
  postNotice,
  deleteNotice,
  editNotice,
  setNoticePinned,
  isLoggedIn,
  getUsername,
  getIsAdmin,
  logout,
} from './api.js'
import LoginForm from './LoginForm.jsx'

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn())
  const [username, setUsername] = useState(getUsername())
  const [isAdmin, setIsAdmin] = useState(getIsAdmin())
  const [showAuth, setShowAuth] = useState(false)
  const [notices, setNotices] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editText, setEditText] = useState('')

  async function load() {
    try {
      setLoading(true)
      setNotices(await fetchNotices())
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!message.trim()) return
    try {
      setSubmitting(true)
      await postNotice(message.trim())
      setMessage('')
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteNotice(id)
      setNotices((prev) => prev.filter((n) => n.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  function startEdit(notice) {
    setEditingId(notice.id)
    setEditText(notice.message)
  }

  function cancelEdit() {
    setEditingId(null)
    setEditText('')
  }

  async function handleEditSubmit(e, id) {
    e.preventDefault()
    if (!editText.trim()) return
    try {
      const updated = await editNotice(id, editText.trim())
      setNotices((prev) => prev.map((n) => (n.id === id ? updated : n)))
      cancelEdit()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleTogglePin(notice) {
    try {
      const updated = await setNoticePinned(notice.id, !notice.pinned)
      setNotices((prev) => {
        const next = prev.map((n) => (n.id === notice.id ? updated : n))
        next.sort((a, b) => {
          if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
          return new Date(b.created_at) - new Date(a.created_at)
        })
        return next
      })
    } catch (err) {
      setError(err.message)
    }
  }

  function handleLogout() {
    logout()
    setAuthed(false)
    setUsername(null)
    setIsAdmin(false)
  }

  if (showAuth && !authed) {
    return (
      <LoginForm
        onAuthed={() => {
          setAuthed(true)
          setUsername(getUsername())
          setIsAdmin(getIsAdmin())
          setShowAuth(false)
        }}
        onCancel={() => setShowAuth(false)}
      />
    )
  }

  return (
    <div className="page">
      <header className="header">
        <div className="header-row">
          <h1>Notice Board</h1>
          {authed ? (
            <button className="link" onClick={handleLogout}>
              Log out
            </button>
          ) : (
            <button className="link" onClick={() => setShowAuth(true)}>
              Log in
            </button>
          )}
        </div>
        <p>Post something. It sticks around until someone takes it down.</p>
      </header>

      {authed ? (
        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Write a notice..."
            rows={3}
          />
          <button type="submit" disabled={submitting || !message.trim()}>
            {submitting ? 'Posting…' : 'Post Notice'}
          </button>
        </form>
      ) : (
        <p className="empty">
          <button className="link" onClick={() => setShowAuth(true)}>
            Log in
          </button>{' '}
          to post a notice.
        </p>
      )}

      {error && <div className="error">{error}</div>}

      {loading ? (
        <p className="empty">Loading notices…</p>
      ) : notices.length === 0 ? (
        <p className="empty">No notices yet. Be the first to post one.</p>
      ) : (
        <ul className="board">
          {notices.map((n) => {
            const canManage = authed && (n.author === username || isAdmin)
            return (
              <li key={n.id} className={`notice${n.pinned ? ' pinned' : ''}`}>
                {n.pinned && <span className="pin-badge">📌 Important</span>}
                {editingId === n.id ? (
                  <form className="edit-form" onSubmit={(e) => handleEditSubmit(e, n.id)}>
                    <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={3} autoFocus />
                    <div className="edit-actions">
                      <button type="submit" disabled={!editText.trim()}>
                        Save
                      </button>
                      <button type="button" className="link" onClick={cancelEdit}>
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <p>{n.message}</p>
                )}
                <div className="notice-footer">
                  <span>
                    {n.author ? `${n.author} · ` : ''}
                    {new Date(n.created_at).toLocaleString()}
                    {n.updated_at ? ' (edited)' : ''}
                  </span>
                  <div className="notice-actions">
                    {isAdmin && (
                      <button onClick={() => handleTogglePin(n)} aria-label={n.pinned ? 'Unpin notice' : 'Pin notice as important'}>
                        {n.pinned ? 'Unpin' : 'Pin'}
                      </button>
                    )}
                    {canManage && editingId !== n.id && (
                      <button onClick={() => startEdit(n)} aria-label="Edit notice">
                        Edit
                      </button>
                    )}
                    {canManage && (
                      <button onClick={() => handleDelete(n.id)} aria-label="Delete notice">
                        ✕
                      </button>
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
