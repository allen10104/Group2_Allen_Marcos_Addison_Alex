import { useState, type FormEvent } from 'react'
import type { Category, Notice, NoticeCreate } from '../types'
import './NoticeForm.css'

const CATEGORIES: Category[] = ['Announcement', 'Event', 'General', 'Other']

interface NoticeFormProps {
  initial?: Notice | null
  submitLabel: string
  onSubmit: (payload: NoticeCreate) => Promise<void>
  onCancel?: () => void
}

export function NoticeForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: NoticeFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')
  const [category, setCategory] = useState<Category>(
    (initial?.category as Category) || 'General',
  )
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (!title.trim() || !content.trim()) {
      setError('Title and content are required.')
      return
    }

    setSaving(true)
    try {
      await onSubmit({
        title: title.trim(),
        content: content.trim(),
        category,
      })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to save notice.'
      setError(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="notice-form" onSubmit={handleSubmit}>
      <div className="notice-form__field">
        <label htmlFor="notice-title">Title</label>
        <input
          id="notice-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div className="notice-form__field">
        <label htmlFor="notice-category">Category</label>
        <select
          id="notice-category"
          value={category}
          onChange={(e) => setCategory(e.target.value as Category)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="notice-form__field">
        <label htmlFor="notice-content">Content</label>
        <textarea
          id="notice-content"
          rows={5}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
        />
      </div>

      {error && <p className="notice-form__error">{error}</p>}

      <div className="notice-form__actions">
        {onCancel && (
          <button type="button" className="btn btn--ghost" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn btn--primary" disabled={saving}>
          {saving ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  )
}
