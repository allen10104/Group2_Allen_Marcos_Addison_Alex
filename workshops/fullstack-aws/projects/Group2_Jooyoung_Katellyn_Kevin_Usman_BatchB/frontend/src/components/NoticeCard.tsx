import type { Notice, User } from '../types'
import './NoticeCard.css'

interface NoticeCardProps {
  notice: Notice
  currentUser: User | null
  onEdit: (notice: Notice) => void
  onDelete: (notice: Notice) => void
}

function canModify(user: User | null, notice: Notice): boolean {
  if (!user) return false
  return user.is_admin || user.id === notice.author_id
}

function categoryClass(category: string): string {
  return `notice-card--${category.toLowerCase().replace(/\s+/g, '-')}`
}

function formatDate(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function NoticeCard({
  notice,
  currentUser,
  onEdit,
  onDelete,
}: NoticeCardProps) {
  const editable = canModify(currentUser, notice)
  const tilt = (notice.id % 5) + 1

  return (
    <article
      className={`notice-card ${categoryClass(notice.category)} notice-card--tilt-${tilt}`}
    >
      <span className="notice-card__pin" aria-hidden="true" />
      <div className="notice-card__header">
        <h2 className="notice-card__title">{notice.title}</h2>
        <span className="notice-card__category">{notice.category}</span>
      </div>

      <p className="notice-card__content">{notice.content}</p>

      <div className="notice-card__meta">
        <span>By {notice.author || 'Unknown'}</span>
        <span>{formatDate(notice.date)}</span>
      </div>

      {editable && (
        <div className="notice-card__actions">
          <button
            type="button"
            className="btn btn--ghost btn--small"
            onClick={() => onEdit(notice)}
          >
            Edit
          </button>
          <button
            type="button"
            className="btn btn--danger btn--small"
            onClick={() => onDelete(notice)}
          >
            Delete
          </button>
        </div>
      )}
    </article>
  )
}
