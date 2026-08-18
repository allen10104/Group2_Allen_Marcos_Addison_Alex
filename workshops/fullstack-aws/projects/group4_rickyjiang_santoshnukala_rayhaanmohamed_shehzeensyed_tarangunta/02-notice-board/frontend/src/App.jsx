import { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import * as api from './api/client';
import LoginForm from './components/LoginForm';
import NoticeCard from './components/NoticeCard';
import NoticeForm from './components/NoticeForm';
import './index.css';

const CATEGORIES = ['COMPLIANCE', 'SECURITY_ALERT', 'OPERATIONS', 'IT_SYSTEMS', 'HR', 'GENERAL'];

function Board() {
  const { user, signOut } = useAuth();

  const [notices, setNotices] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  // One panel at a time: null | 'login' | 'new'. A single value beats two booleans -
  // it makes "both open at once" unrepresentable rather than something to guard against.
  const [panel, setPanel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * useCallback keeps this function's identity stable across renders. Without it the
   * useEffect below re-runs on EVERY render - an infinite fetch loop. The #1 React
   * data-fetching bug.
   */
  const loadNotices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // No token needed - reads are public. This is what lets the deployed S3 site
      // render content for a visitor who has never logged in.
      setNotices(await api.fetchNotices({ category: categoryFilter || undefined }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [categoryFilter]);

  useEffect(() => { loadNotices(); }, [loadNotices]);

  const handleCreate = async (notice) => {
    await api.createNotice(notice);
    setPanel(null);
    // Reload rather than splicing locally, so the server's canonical ordering
    // (pinned, priority, date) wins.
    loadNotices();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Archive this notice? It will no longer appear on the board.')) return;
    try {
      await api.deleteNotice(id);
      setNotices((prev) => prev.filter((n) => n.id !== id));
    } catch (e) {
      // 401 here means the token expired mid-session. Drop it and reopen the login
      // panel - the board stays visible behind it, because reads never needed auth.
      if (e.status === 401) {
        signOut();
        setPanel('login');
        setError('Your session expired. Please sign in again.');
      } else {
        setError(e.message);
      }
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Notice Board</h1>
          <span className="subtitle">Internal Communications</span>
        </div>

        <div className="user-box">
          {user ? (
            <>
              <div>
                <strong>{user.full_name}</strong>
                <span className="muted"> · {user.department || 'Bank-wide'}</span>
                <div className="muted small">{user.roles.join(', ')}</div>
              </div>
              <button className="ghost" onClick={signOut}>Sign out</button>
            </>
          ) : (
            <>
              <div className="muted small">Viewing as guest</div>
              <button onClick={() => setPanel(panel === 'login' ? null : 'login')}>
                Sign in
              </button>
            </>
          )}
        </div>
      </header>

      <div className="controls">
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
        </select>

        {/* Only signed-in staff can post. The server enforces this independently -
            hiding the button is a UX affordance, not the security control. */}
        {user && user.can_publish && (
          <button onClick={() => setPanel(panel === 'new' ? null : 'new')}>
            {panel === 'new' ? 'Close' : '+ New notice'}
          </button>
        )}

        <button className="ghost" onClick={loadNotices}>Refresh</button>
      </div>

      {panel === 'login' && (
        <LoginForm onSuccess={() => setPanel(null)} onCancel={() => setPanel(null)} />
      )}

      {panel === 'new' && (
        <NoticeForm onCreate={handleCreate} onCancel={() => setPanel(null)} />
      )}

      {error && <div className="alert error">{error}</div>}
      {loading && <p className="muted">Loading notices…</p>}
      {!loading && notices.length === 0 && <p className="muted">No notices on the board.</p>}

      <div className="board">
        {notices.map((n) => (
          <NoticeCard
            key={n.id}
            notice={n}
            /* Delete only shows for signed-in publishers. Guests get a read-only board. */
            canManage={Boolean(user && user.can_publish)}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * No route switching. The board IS the app - login is a panel inside it, not a gate in
 * front of it. That is the whole point of public reads: a visitor lands on content,
 * not a password prompt.
 */
export default function App() {
  return (
    <AuthProvider>
      <Board />
    </AuthProvider>
  );
}
