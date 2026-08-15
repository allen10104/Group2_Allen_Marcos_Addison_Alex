import { useEffect, useState, type FormEvent } from 'react'
import { useAuth, getApiErrorMessage } from '../context/AuthContext'
import { createNotice, deleteNotice, getNotices, updateNotice } from '../api/notices'
import type { Notice } from '../types/notice'

export function BoardPage() {
  const { user, logout } = useAuth()

  const [notices, setNotices] = useState<Notice[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [isPosting, setIsPosting] = useState(false)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')

  useEffect(() => {
    let cancelled = false

    getNotices()
      .then((data) => {
        if (!cancelled) setNotices(data)
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err, 'Could not load notices.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsPosting(true)
    try {
      const notice = await createNotice({ title, content })
      setNotices((prev) => [notice, ...prev])
      setTitle('')
      setContent('')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not post notice.'))
    } finally {
      setIsPosting(false)
    }
  }

  function startEditing(notice: Notice) {
    setEditingId(notice.notice_id)
    setEditTitle(notice.title)
    setEditContent(notice.content)
  }

  function cancelEditing() {
    setEditingId(null)
    setEditTitle('')
    setEditContent('')
  }

  async function handleUpdate(noticeId: string) {
    setError(null)
    try {
      const updated = await updateNotice(noticeId, { title: editTitle, content: editContent })
      setNotices((prev) => prev.map((notice) => (notice.notice_id === noticeId ? updated : notice)))
      cancelEditing()
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not update notice.'))
    }
  }

  async function handleDelete(noticeId: string) {
    setError(null)
    try {
      await deleteNotice(noticeId)
      setNotices((prev) => prev.filter((notice) => notice.notice_id !== noticeId))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not delete notice.'))
    }
  }

  return (
    <div className="board-page">
      <header className="board-header">
        <h1>Notice Board</h1>
        <div className="board-header-user">
          <span>{user?.email}</span>
          <button type="button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      {error && <p className="form-error">{error}</p>}

      <form className="notice-form" onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />
        <textarea
          placeholder="What's on your mind?"
          value={content}
          onChange={(event) => setContent(event.target.value)}
          required
        />
        <button type="submit" disabled={isPosting}>
          {isPosting ? 'Posting...' : 'Post notice'}
        </button>
      </form>

      {isLoading ? (
        <p>Loading notices...</p>
      ) : notices.length === 0 ? (
        <p>No notices yet -- be the first to post one.</p>
      ) : (
        <ul className="notice-list">
          {notices.map((notice) => {
            const isOwner = notice.user_id === user?.user_id
            const isEditing = editingId === notice.notice_id

            return (
              <li key={notice.notice_id} className="notice-card">
                {isEditing ? (
                  <div className="notice-edit-form">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(event) => setEditTitle(event.target.value)}
                    />
                    <textarea
                      value={editContent}
                      onChange={(event) => setEditContent(event.target.value)}
                    />
                    <div className="notice-actions">
                      <button type="button" onClick={() => handleUpdate(notice.notice_id)}>
                        Save
                      </button>
                      <button type="button" onClick={cancelEditing}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <h2>{notice.title}</h2>
                    <p>{notice.content}</p>
                    <p className="notice-meta">
                      Posted {new Date(notice.created_at).toLocaleString()}
                    </p>
                    {isOwner && (
                      <div className="notice-actions">
                        <button type="button" onClick={() => startEditing(notice)}>
                          Edit
                        </button>
                        <button type="button" onClick={() => handleDelete(notice.notice_id)}>
                          Delete
                        </button>
                      </div>
                    )}
                  </>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}