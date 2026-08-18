import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getAllNotices, deleteNotice, setPin } from '../api/notices';
import NoticeForm from './NoticeForm';
import './NoticeList.css';

export default function NoticeList() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Separate from the load error above -- this one's for a failed
  // pin/delete click, shown without wiping out the list that already loaded.
  const [actionError, setActionError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const { isAuthenticated, token } = useAuth();

  useEffect(() => {
    let cancelled = false;

    async function loadNotices() {
      try {
        const data = await getAllNotices();
        if (!cancelled) setNotices(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadNotices();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleCreated(newNotice) {
    // The function form of setNotices: React passes in the CURRENT state
    // (`prev`) at the moment it actually applies the update, rather than
    // us reaching for the `notices` variable from this render, which could
    // theoretically be stale. Prepends the new notice to the top.
    setNotices((prev) => [newNotice, ...prev]);
    setShowForm(false);
  }

  async function handleTogglePin(notice) {
    setActionError(null);
    try {
      const updated = await setPin(notice.id, !notice.is_pinned, token);
      // Replace just the one notice that changed, leave everything else as-is.
      setNotices((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
    } catch (err) {
      setActionError(err.message);
    }
  }

  async function handleDelete(id) {
    setActionError(null);
    try {
      await deleteNotice(id, token);
      setNotices((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      setActionError(err.message);
    }
  }

  const sorted = [...notices].sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned));

  return (
    <div className="notice-board">
      {/* Only show the "+" if you're logged in -- creating requires a token. */}
      {isAuthenticated && (
        <div className="notice-toolbar">
          <button
            type="button"
            className="notice-toolbar__add"
            onClick={() => setShowForm((prev) => !prev)}
            title={showForm ? 'Cancel' : 'New notice'}
          >
            {showForm ? '×' : '+'}
          </button>
        </div>
      )}

      {showForm && <NoticeForm onCreated={handleCreated} />}

      {actionError && <p className="notice-list__error">{actionError}</p>}

      {/* These four blocks replace the old early-return pattern -- now that
          the toolbar/form above need to render no matter what state the
          list itself is in, we can't just `return <p>Loading...</p>` early
          anymore, since that would wipe out the toolbar too. */}
      {loading && <p className="notice-list__status">Loading notices...</p>}

      {!loading && error && (
        <p className="notice-list__status notice-list__status--error">
          Couldn't load notices: {error}
        </p>
      )}

      {!loading && !error && notices.length === 0 && (
        <p className="notice-list__status">No notices yet.</p>
      )}

      {!loading && !error && notices.length > 0 && (
        <ul className="notice-list">
          {sorted.map((notice) => (
            <li key={notice.id} className="notice-row">
              {/* Sibling of .notice-card, not inside it -- that's what puts
                  it visually "outside" the box, to its left. */}
              <button
                type="button"
                className={`pin-toggle ${notice.is_pinned ? 'pin-toggle--active' : ''}`}
                onClick={() => handleTogglePin(notice)}
                disabled={!isAuthenticated}
                title={notice.is_pinned ? 'Unpin' : 'Pin'}
              >
                📌
              </button>

              <div className={`notice-card ${notice.is_pinned ? 'notice-card--pinned' : ''}`}>
                <button
                  type="button"
                  className="delete-button"
                  onClick={() => handleDelete(notice.id)}
                  disabled={!isAuthenticated}
                  title="Delete"
                >
                  ×
                </button>
                {notice.is_pinned && <span className="notice-card__badge">PINNED</span>}
                <p className="notice-card__message">{notice.message}</p>
                <p className="notice-card__meta">
                    {notice.user_email} · {new Date(notice.created_at).toLocaleString()}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}