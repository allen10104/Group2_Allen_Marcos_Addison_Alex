// useState tracks the like count, whether THIS user has liked it, and
// whether a like/unlike request is currently in progress.
import { useState } from 'react';

// Link makes the whole card clickable, navigating to the notice's detail page.
import { Link } from 'react-router-dom';

// The API functions that call the backend's like/unlike endpoints.
import { likeNotice, unlikeNotice } from '../api/api';

// Gives access to the current JWT token, needed for authenticated requests.
import { useAuth } from '../context/AuthContext';

// Reusable glass-panel container.
import Card from './Card';

// Displays one notice in the list: name, message, date, view count, and
// a like button. Receives the notice object as a prop.
export default function NoticeCard({ notice }) {
  // Need the token to make authenticated like/unlike requests.
  const { token } = useAuth();

  // Local copy of the like count, so clicking Like updates instantly
  // without waiting for a full page refetch.
  const [likeCount, setLikeCount] = useState(notice.like_count);

  // Whether THIS user has liked this notice, tracked only for the
  // current session (the backend doesn't tell us this on page load,
  // only the total count).
  const [liked, setLiked] = useState(false);

  // True while a like/unlike request is in flight. Prevents rapid
  // repeat clicks from firing duplicate requests before the first
  // one's response comes back and updates `liked`.
  const [likePending, setLikePending] = useState(false);

  // Handles clicking the like button.
  async function handleLikeClick(e) {
    // Stop the click from also triggering the surrounding <Link>'s
    // navigation to the detail page.
    e.preventDefault();
    e.stopPropagation();

    // Ignore clicks while a request is already running.
    if (likePending) return;

    // Mark a request as in progress, disabling the button via JSX below.
    setLikePending(true);
    try {
      if (liked) {
        // Already liked — this click means "unlike".
        await unlikeNotice(notice.id, token);
        setLikeCount((count) => count - 1);
        setLiked(false);
      } else {
        // Not liked yet — this click means "like".
        await likeNotice(notice.id, token);
        setLikeCount((count) => count + 1);
        setLiked(true);
      }
    } catch (err) {
      // If the backend says we're out of sync with reality (e.g. this
      // was already liked from a previous session, or already unliked),
      // correct our local state to match instead of leaving the button
      // stuck in the wrong mode.
      if (err.message.includes('already liked')) {
        setLiked(true);
      } else if (err.message.includes("haven't liked")) {
        setLiked(false);
      } else {
        // Some other, unexpected error — log it rather than crash the page.
        console.error(err.message);
      }
    } finally {
      // Always clear the pending flag, whether the request succeeded or failed.
      setLikePending(false);
    }
  }

  return (
    // The whole card is a link to the notice's detail page.
    <Link to={`/notices/${notice.id}`}>
      <Card className="hover:border-accent/40 transition-colors cursor-pointer text-left">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-white">{notice.name}</h2>
          {/* Formats the ISO timestamp into a readable date. */}
          <span className="text-xs text-gray-500">{new Date(notice.created_at).toLocaleDateString()}</span>
        </div>

        <p className="text-gray-300 mb-4">{notice.message}</p>

        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>👁 {notice.view_count} views</span>
          {/* Color changes to the accent color once liked, giving clear
              visual feedback. disabled while a request is running, so
              rapid clicks can't fire duplicate requests. */}
          <button
            onClick={handleLikeClick}
            disabled={likePending}
            className={`flex items-center gap-1 ${liked ? 'text-accent' : 'text-gray-400'} hover:text-accent transition-colors disabled:opacity-50`}
          >
            ❤ {likeCount}
          </button>
        </div>
      </Card>
    </Link>
  );
}