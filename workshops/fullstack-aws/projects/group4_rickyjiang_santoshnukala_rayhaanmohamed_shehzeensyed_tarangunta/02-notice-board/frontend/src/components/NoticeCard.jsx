/**
 * One notice on the board. Presentational — receives data and callbacks, holds no
 * state. The parent owns all data flow ("lifting state up", the standard React shape).
 */
export default function NoticeCard({ notice, canManage, onDelete }) {
  const prio = `priority-${notice.priority.toLowerCase()}`;
  const when = new Date(notice.created_at).toLocaleString('en-US', {
    dateStyle: 'medium', timeStyle: 'short',
  });

  return (
    <article className={`card notice ${prio}`}>
      <header className="notice-head">
        <div className="badges">
          {/* category_label and acknowledgement_required are computed SERVER-side in
              NoticeResponse.from_domain, so React never needs its own copy of the
              enum rules and the two can't drift apart. */}
          <span className="badge category">{notice.category_label}</span>
          <span className={`badge prio ${prio}`}>{notice.priority}</span>
          {notice.pinned && <span className="badge pinned">PINNED</span>}
          {notice.acknowledgement_required && (
            <span className="badge ack">ACKNOWLEDGEMENT REQUIRED</span>
          )}
        </div>

        {canManage && (
          <button className="danger small" onClick={() => onDelete(notice.id)}
                  aria-label={`Delete notice: ${notice.title}`}>
            Delete
          </button>
        )}
      </header>

      <h2>{notice.title}</h2>
      {/* Plain text via JSX interpolation — React escapes it, so a body containing
          <script> renders harmlessly. Never dangerouslySetInnerHTML on user content. */}
      <p className="body">{notice.body}</p>

      <footer className="notice-foot">
        <span>{notice.author_name || notice.author_employee_id}</span>
        <span>·</span>
        <span>{notice.department || 'Bank-wide'}</span>
        <span>·</span>
        <span>{when}</span>
      </footer>
    </article>
  );
}
