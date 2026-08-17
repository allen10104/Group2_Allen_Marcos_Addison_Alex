import { noteVisuals } from '../utils/noteVisuals.js'

/**
 * A single sticky note on the corkboard.
 *
 * Renders either the notice's message or an inline edit form, plus a
 * fastener (pin/tape), a corner delete button, and the pin/edit action
 * row — visibility of each action is controlled entirely by the props
 * passed in from App.jsx (which owns permission logic and edit state).
 */
export default function NoteCard({
  notice,
  canManage,
  isAdmin,
  isEditing,
  editText,
  onEditTextChange,
  onStartEdit,
  onCancelEdit,
  onEditSubmit,
  onDelete,
  onTogglePin,
}) {
  const { color, rotation, fastener } = noteVisuals(notice)

  return (
    <li
      className={`sticky-note note-${color}${notice.pinned ? ' is-important' : ''}`}
      style={{ '--rotate': `${rotation}deg` }}
    >
      <span className={`fastener ${fastener}${notice.pinned ? ' important' : ''}`} aria-hidden="true" />
      {notice.pinned && <span className="pin-flag">Important</span>}

      {canManage && (
        <button className="note-delete" onClick={() => onDelete(notice.id)} aria-label="Delete notice">
          ×
        </button>
      )}

      {isEditing ? (
        <form className="edit-form" onSubmit={(e) => onEditSubmit(e, notice.id)}>
          <textarea value={editText} onChange={(e) => onEditTextChange(e.target.value)} rows={3} autoFocus />
          <div className="edit-actions">
            <button type="submit" disabled={!editText.trim()}>
              Save
            </button>
            <button type="button" className="link" onClick={onCancelEdit}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <p className="note-text">{notice.message}</p>
      )}

      <div className="note-footer">
        <span className="note-meta">
          {notice.author ? `${notice.author} · ` : ''}
          {new Date(notice.created_at).toLocaleString()}
          {notice.updated_at ? ' (edited)' : ''}
        </span>
        <div className="note-actions">
          {isAdmin && (
            <button
              onClick={() => onTogglePin(notice)}
              aria-label={notice.pinned ? 'Unpin notice' : 'Pin notice as important'}
            >
              {notice.pinned ? 'Unpin' : 'Pin as important'}
            </button>
          )}
          {canManage && !isEditing && (
            <button onClick={() => onStartEdit(notice)} aria-label="Edit notice">
              Edit
            </button>
          )}
        </div>
      </div>
    </li>
  )
}
