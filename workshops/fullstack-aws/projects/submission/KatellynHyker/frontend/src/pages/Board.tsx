import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { AppNav } from '../components/AppNav'
import { useAuth, getApiErrorMessage } from '../context/AuthContext'
import { createNotice, deleteNotice, getNotices, updateNotice } from '../api/notices'
import { getFollowing } from '../api/users'
import type { Notice } from '../types/notice'

type FilterMode = 'all' | 'mine' | 'following'
type SortOrder = 'newest' | 'oldest'

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function wasEdited(notice: Notice): boolean {
  return new Date(notice.updated_at).getTime() > new Date(notice.created_at).getTime()
}

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

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [filterMode, setFilterMode] = useState<FilterMode>('all')
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest')
  const [followingIds, setFollowingIds] = useState<Set<string>>(new Set())

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

  useEffect(() => {
    if (!user) return
    let cancelled = false

    getFollowing(user.user_id)
      .then((data) => {
        if (!cancelled) setFollowingIds(new Set(data.map((u) => u.user_id)))
      })
      .catch(() => {
        // Non-fatal -- the "Following" filter just shows nothing until a
        // retry succeeds; the rest of the board still works.
      })

    return () => {
      cancelled = true
    }
  }, [user])

  const visibleNotices = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()

    let result = notices
    if (filterMode === 'mine') {
      result = result.filter((notice) => notice.user_id === user?.user_id)
    } else if (filterMode === 'following') {
      result = result.filter((notice) => followingIds.has(notice.user_id))
    }
    if (query) {
      result = result.filter(
        (notice) =>
          notice.title.toLowerCase().includes(query) ||
          notice.content.toLowerCase().includes(query) ||
          notice.author_email.toLowerCase().includes(query)
      )
    }
    return [...result].sort((a, b) => {
      const aTime = new Date(a.created_at).getTime()
      const bTime = new Date(b.created_at).getTime()
      return sortOrder === 'newest' ? bTime - aTime : aTime - bTime
    })
  }, [notices, searchQuery, filterMode, sortOrder, user?.user_id, followingIds])

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
      setConfirmDeleteId(null)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not delete notice.'))
    }
  }

  const totalCount = notices.length
  const visibleCount = visibleNotices.length
  const isFiltered = filterMode !== 'all' || searchQuery.trim() !== ''

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

      <AppNav />

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
 
      <div className="board-toolbar">
        <input
          type="search"
          className="board-search"
          placeholder="Search notices..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
 
        <div className="board-toolbar-controls">
          <div className="segmented-control" role="group" aria-label="Filter notices">
            <button
              type="button"
              className={filterMode === 'all' ? 'active' : ''}
              onClick={() => setFilterMode('all')}
            >
              All
            </button>
            <button
              type="button"
              className={filterMode === 'mine' ? 'active' : ''}
              onClick={() => setFilterMode('mine')}
            >
              Mine
            </button>
            <button
              type="button"
              className={filterMode === 'following' ? 'active' : ''}
              onClick={() => setFilterMode('following')}
            >
              Following
            </button>
          </div>
 
          <select
            className="board-sort"
            value={sortOrder}
            onChange={(event) => setSortOrder(event.target.value as SortOrder)}
            aria-label="Sort notices"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
          </select>
        </div>
      </div>
 
      <p className="board-count">
        {isFiltered ? `Showing ${visibleCount} of ${totalCount} notices` : `${totalCount} notice${totalCount === 1 ? '' : 's'}`}
      </p>
 
      {isLoading ? (
        <p>Loading notices...</p>
      ) : totalCount === 0 ? (
        <p>No notices yet -- be the first to post one.</p>
      ) : visibleCount === 0 ? (
        <p>No notices match your search/filter.</p>
      ) : (
        <ul className="notice-list">
          {visibleNotices.map((notice) => {
            const isOwner = notice.user_id === user?.user_id
            const isEditing = editingId === notice.notice_id
            const isConfirmingDelete = confirmDeleteId === notice.notice_id
 
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
                      <button type="button" className="notice-action-secondary" onClick={cancelEditing}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <h2>{notice.title}</h2>
                    <p className="notice-content">{notice.content}</p>
                    <p className="notice-meta">
                      Posted by {isOwner ? 'you' : notice.author_email} &middot;{' '}
                      {formatTimestamp(notice.created_at)}
                      {wasEdited(notice) && <span className="notice-edited"> (edited)</span>}
                    </p>
                    {isOwner && (
                      <div className="notice-actions">
                        {isConfirmingDelete ? (
                          <>
                            <span className="notice-confirm-text">Delete this notice?</span>
                            <button
                              type="button"
                              className="notice-action-danger"
                              onClick={() => handleDelete(notice.notice_id)}
                            >
                              Yes, delete
                            </button>
                            <button
                              type="button"
                              className="notice-action-secondary"
                              onClick={() => setConfirmDeleteId(null)}
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button type="button" onClick={() => startEditing(notice)}>
                              Edit
                            </button>
                            <button
                              type="button"
                              className="notice-action-danger"
                              onClick={() => setConfirmDeleteId(notice.notice_id)}
                            >
                              Delete
                            </button>
                          </>
                        )}
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