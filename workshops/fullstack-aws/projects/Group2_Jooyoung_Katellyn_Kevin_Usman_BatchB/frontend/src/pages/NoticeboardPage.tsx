import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'
import * as noticesApi from '../api/notices'
import {
  EMPTY_FILTERS,
  hasActiveFilters,
  NoticeFilterBar,
  toListNoticesParams,
  type NoticeFilters,
} from '../components/NoticeFilterBar'
import { NoticeCard } from '../components/NoticeCard'
import { NoticeForm } from '../components/NoticeForm'
import { useAuth } from '../context/AuthContext'
import type { Notice, NoticeCreate } from '../types'
import './NoticeboardPage.css'

function apiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  if (err instanceof Error) return err.message
  return fallback
}

export function NoticeboardPage() {
  const { user, isAuthenticated } = useAuth()
  const [notices, setNotices] = useState<Notice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [editing, setEditing] = useState<Notice | null>(null)
  const [filters, setFilters] = useState<NoticeFilters>(EMPTY_FILTERS)

  const loadNotices = useCallback(async (activeFilters: NoticeFilters = filters) => {
    setLoading(true)
    setError(null)
    try {
      const data = await noticesApi.listNotices(toListNoticesParams(activeFilters))
      setNotices(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load notices.'))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    void loadNotices(filters)
  }, [filters, loadNotices])

  function handleFiltersChange(nextFilters: NoticeFilters) {
    setFilters(nextFilters)
  }

  async function handleCreate(payload: NoticeCreate) {
    try {
      await noticesApi.createNotice(payload)
      setShowCreate(false)
      await loadNotices(filters)
    } catch (err) {
      throw new Error(apiErrorMessage(err, 'Failed to create notice.'))
    }
  }

  async function handleUpdate(payload: NoticeCreate) {
    if (!editing) return
    try {
      await noticesApi.updateNotice(editing.id, payload)
      setEditing(null)
      await loadNotices(filters)
    } catch (err) {
      throw new Error(apiErrorMessage(err, 'Failed to update notice.'))
    }
  }

  async function handleDelete(notice: Notice) {
    const confirmed = window.confirm(
      `Delete notice "${notice.title}"? This cannot be undone.`,
    )
    if (!confirmed) return

    try {
      await noticesApi.deleteNotice(notice.id)
      if (editing?.id === notice.id) setEditing(null)
      await loadNotices(filters)
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to delete notice.'))
    }
  }

  return (
    <section className="noticeboard">
      <div className="noticeboard__header">
        <p className="noticeboard__subtitle">
          {isAuthenticated
            ? user?.is_admin
              ? 'You can create, edit, and delete any notice.'
              : 'You can create notices and edit or delete your own.'
            : 'Browsing as a guest — view only. Log in to post or manage notices.'}
        </p>

        {isAuthenticated && (
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => {
              setEditing(null)
              setShowCreate((open) => !open)
            }}
          >
            {showCreate ? 'Close form' : 'New notice'}
          </button>
        )}
      </div>

      {showCreate && isAuthenticated && (
        <div className="noticeboard__form-wrap">
          <h2>Create notice</h2>
          <NoticeForm
            submitLabel="Create"
            onSubmit={handleCreate}
            onCancel={() => setShowCreate(false)}
          />
        </div>
      )}

      {editing && (
        <div className="noticeboard__form-wrap">
          <h2>Edit notice</h2>
          <NoticeForm
            initial={editing}
            submitLabel="Save changes"
            onSubmit={handleUpdate}
            onCancel={() => setEditing(null)}
          />
        </div>
      )}

      {error && <p className="noticeboard__error">{error}</p>}

      <NoticeFilterBar filters={filters} onChange={handleFiltersChange} />

      <div className="noticeboard__board" aria-live="polite">
        {loading ? (
          <p className="noticeboard__status">Loading notices…</p>
        ) : notices.length === 0 ? (
          <p className="noticeboard__status">
            {hasActiveFilters(filters)
              ? 'No notices match your filters.'
              : 'No notices yet.'}
          </p>
        ) : (
          <div className="noticeboard__list">
            {notices.map((notice) => (
              <NoticeCard
                key={notice.id}
                notice={notice}
                currentUser={user}
                onEdit={(n) => {
                  setShowCreate(false)
                  setEditing(n)
                }}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
