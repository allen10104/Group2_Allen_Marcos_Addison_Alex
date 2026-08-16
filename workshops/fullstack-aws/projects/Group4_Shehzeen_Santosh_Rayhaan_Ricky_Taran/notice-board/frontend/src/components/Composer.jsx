/**
 * The "write a new notice" form, styled as a blank sticky note.
 * Only rendered for logged-in users; App.jsx swaps in the login CTA otherwise.
 */
export default function Composer({ message, onMessageChange, onSubmit, submitting }) {
  return (
    <div className="composer-wrap">
      <form className="composer" onSubmit={onSubmit}>
        <textarea
          value={message}
          onChange={(e) => onMessageChange(e.target.value)}
          placeholder="Write a notice..."
          rows={4}
        />
        <button type="submit" disabled={submitting || !message.trim()}>
          {submitting ? 'Posting…' : 'Post it ↦'}
        </button>
      </form>
    </div>
  )
}
