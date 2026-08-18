import { useEffect, useState, type FormEvent } from 'react'
import type { Category } from '../types'
import './NoticeFilterBar.css'

export interface NoticeFilters {
  q: string
  author: string
  category: Category | ''
}

export const EMPTY_FILTERS: NoticeFilters = {
  q: '',
  author: '',
  category: '',
}

const CATEGORIES: Category[] = ['Announcement', 'Event', 'General', 'Other']

interface NoticeFilterBarProps {
  filters: NoticeFilters
  onChange: (filters: NoticeFilters) => void
}

export function NoticeFilterBar({ filters, onChange }: NoticeFilterBarProps) {
  const [draft, setDraft] = useState(filters)

  useEffect(() => {
    setDraft(filters)
  }, [filters])

  function updateDraft(partial: Partial<NoticeFilters>) {
    setDraft((current) => ({ ...current, ...partial }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onChange(draft)
  }

  function handleClear() {
    setDraft(EMPTY_FILTERS)
    onChange(EMPTY_FILTERS)
  }

  const hasActiveFilters = Boolean(
    filters.q.trim() || filters.author.trim() || filters.category,
  )

  return (
    <form className="notice-filter" onSubmit={handleSubmit}>
      <div className="notice-filter__fields">
        <div className="notice-filter__field notice-filter__field--search">
          <label htmlFor="notice-search">Search</label>
          <input
            id="notice-search"
            type="search"
            placeholder="Title or content…"
            value={draft.q}
            onChange={(e) => updateDraft({ q: e.target.value })}
          />
        </div>

        <div className="notice-filter__field">
          <label htmlFor="notice-author">Author</label>
          <input
            id="notice-author"
            type="search"
            placeholder="Author name…"
            value={draft.author}
            onChange={(e) => updateDraft({ author: e.target.value })}
          />
        </div>

        <div className="notice-filter__field">
          <label htmlFor="notice-category">Category</label>
          <select
            id="notice-category"
            value={draft.category}
            onChange={(e) =>
              updateDraft({ category: e.target.value as Category | '' })
            }
          >
            <option value="">All categories</option>
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="notice-filter__actions">
        <button type="submit" className="btn btn--primary btn--small">
          Apply
        </button>
        {hasActiveFilters && (
          <button
            type="button"
            className="btn btn--ghost btn--small"
            onClick={handleClear}
          >
            Clear
          </button>
        )}
      </div>
    </form>
  )
}

export function hasActiveFilters(filters: NoticeFilters): boolean {
  return Boolean(filters.q.trim() || filters.author.trim() || filters.category)
}

export function toListNoticesParams(filters: NoticeFilters) {
  return {
    q: filters.q.trim() || undefined,
    author: filters.author.trim() || undefined,
    category: filters.category || undefined,
  }
}
