// useState holds the notices list and form state. useEffect fetches
// notices once when the page first loads.
import { useState, useEffect } from 'react';

import { getNotices, createNotice } from '../api/api';
import { useAuth } from '../context/AuthContext';
import NavBar from '../components/NavBar';
import NoticeCard from '../components/NoticeCard';
import Card from '../components/Card';
import Button from '../components/Button';

export default function Dashboard() {
  // token is needed for every API call. user.role decides whether to
  // show the "post a notice" form.
  const { token, user } = useAuth();

  // The list of notices fetched from the backend.
  const [notices, setNotices] = useState([]);
  // Whether the initial fetch is still in progress.
  const [loading, setLoading] = useState(true);
  // Any error from fetching or posting.
  const [error, setError] = useState('');

  // Form state for the admin-only "post a notice" form.
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [posting, setPosting] = useState(false);

  // Runs once, right after the component first renders, to load notices.
  // The empty [] dependency array means this only runs on mount, not on
  // every re-render.
  useEffect(() => {
    loadNotices();
  }, []);

  // Fetches the notice list from the backend and stores it in state.
  async function loadNotices() {
    setLoading(true);
    try {
      const data = await getNotices(token);
      setNotices(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Handles submitting the "post a notice" form (ADMIN only).
  async function handlePostNotice(e) {
    e.preventDefault();
    setPosting(true);

    try {
      await createNotice(name, message, token);
      // Clear the form on success.
      setName('');
      setMessage('');
      // Refetch so the new notice shows up immediately.
      await loadNotices();
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="min-h-screen">
      <NavBar />

      <div className="max-w-2xl mx-auto p-8">
        {/* Only renders the posting form if the logged-in user is an ADMIN.
            The backend also enforces this on its end — this is just UI. */}
        {user?.role === 'ADMIN' && (
          <Card className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">Post a Notice</h2>
            <form onSubmit={handlePostNotice} className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              />
              <textarea
                placeholder="Notice message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              />
              <Button type="submit" disabled={posting}>
                {posting ? 'Posting...' : 'Post Notice'}
              </Button>
            </form>
          </Card>
        )}

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        {/* Three possible states: loading, empty, or showing the list. */}
        {loading ? (
          <p className="text-gray-400 text-center">Loading notices...</p>
        ) : notices.length === 0 ? (
          <p className="text-gray-400 text-center">No notices posted yet.</p>
        ) : (
          <div className="flex flex-col gap-4">
            {/* key={notice.id} is required by React to track each item
                in the list efficiently. */}
            {notices.map((notice) => (
              <NoticeCard key={notice.id} notice={notice} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}