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
import LoginForm from './components/LoginForm.jsx'
import Composer from './components/Composer.jsx'
import NoteCard from './components/NoteCard.jsx'

/**
 * Top-level app state and data flow. Owns auth state, the notice list,
 * and edit-in-progress state; delegates rendering of the note grid to
 * NoteCard and the write-a-notice form to Composer.
 */
export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn())
  const [username, setUsername] = useState(getUsername())
  const [isAdmin, setIsAdmin] = useState(getIsAdmin())
  const [showAuth, setShowAuth] = useState(false)

  const [notices, setNotices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [message, setMessage] = useState('')
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
        // Keep pinned-first, newest-first ordering client-side too, so the
        // toggle doesn't wait on a full reload to move the note into place.
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
      {authed && (
        <div className="account-corner">
          <button className="link" onClick={handleLogout}>
            Log out ({username})
          </button>
        </div>
      )}

      <header className="header">
        <h1>Notice Board</h1>
        <p>
          A shared corkboard for updates, reminders, and shoutouts — pin what matters, edit or take down your own
          notices anytime.
        </p>
      </header>

      {authed ? (
        <Composer message={message} onMessageChange={setMessage} onSubmit={handleSubmit} submitting={submitting} />
      ) : (
        <div className="login-prompt">
          <button className="login-cta" onClick={() => setShowAuth(true)}>
            Log in to post a notice
          </button>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {loading ? (
        <p className="empty">Loading notices…</p>
      ) : notices.length === 0 ? (
        <p className="empty">No notices yet. Be the first to post one.</p>
      ) : (
        <ul className="board">
          {notices.map((n) => (
            <NoteCard
              key={n.id}
              notice={n}
              canManage={authed && (n.author === username || isAdmin)}
              isAdmin={isAdmin}
              isEditing={editingId === n.id}
              editText={editText}
              onEditTextChange={setEditText}
              onStartEdit={startEdit}
              onCancelEdit={cancelEdit}
              onEditSubmit={handleEditSubmit}
              onDelete={handleDelete}
              onTogglePin={handleTogglePin}
            />
          ))}
        </ul>
      )}
    </div>
  )
}
