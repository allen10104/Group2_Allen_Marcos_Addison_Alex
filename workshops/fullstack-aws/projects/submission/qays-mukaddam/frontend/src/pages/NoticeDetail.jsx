// useState holds page data (notice, comments, form fields, etc).
// useEffect fetches data once when the page loads. useRef holds a value
// that persists across renders without causing a re-render itself —
// used below to prevent double-fetching in development.
import { useState, useEffect, useRef } from 'react';

// useParams reads the :noticeId from the URL. useNavigate redirects
// the browser after deleting a notice.
import { useParams, useNavigate } from 'react-router-dom';

// The API functions that call the backend's notice/comment/like endpoints.
import { getNotice, getComments, postComment, deleteNotice, likeNotice, unlikeNotice } from '../api/api';

// Gives access to the current JWT token and decoded user (role, userId).
import { useAuth } from '../context/AuthContext';

// Reusable UI pieces.
import NavBar from '../components/NavBar';
import Card from '../components/Card';
import Button from '../components/Button';
import CommentList from '../components/CommentList';

export default function NoticeDetail() {
  // Pulls the id straight out of the URL, e.g. /notices/5 -> "5".
  const { noticeId } = useParams();
  // Used to redirect back to the dashboard after deleting a notice.
  const navigate = useNavigate();
  // token is needed on every API call. user tells us the role (for
  // showing the ADMIN-only delete button).
  const { token, user } = useAuth();

  // Holds the single notice object fetched from the backend.
  const [notice, setNotice] = useState(null);
  // Holds the array of comments for this notice.
  const [comments, setComments] = useState([]);
  // Whether the initial fetch is still in progress.
  const [loading, setLoading] = useState(true);
  // Any error message from fetching, posting, or deleting.
  const [error, setError] = useState('');

  // Controlled input for the "write a comment" textarea.
  const [commentText, setCommentText] = useState('');
  // Disables the comment button and shows "Posting..." while submitting.
  const [posting, setPosting] = useState(false);

  // Tracks whether THIS user has liked the notice, within this session.
  // Starts false every page load since the backend only returns a total
  // count, not "did I personally like this".
  const [liked, setLiked] = useState(false);

  // True while a like/unlike request is in flight. Prevents rapid
  // repeat clicks from firing duplicate requests before the first one's
  // response comes back and updates `liked`.
  const [likePending, setLikePending] = useState(false);

  // Tracks which noticeId has already been fetched. React 18's
  // StrictMode intentionally runs effects twice in development, which
  // would otherwise call getNotice() — and therefore increment the view
  // count — twice per visit. This ref stops the second call.
  const fetchedIdRef = useRef(null);

  // Runs when the page loads, and again whenever noticeId changes.
  useEffect(() => {
    // Already fetched this exact notice — skip the duplicate call.
    if (fetchedIdRef.current === noticeId) return;
    // Mark this notice as fetched before the async call starts.
    fetchedIdRef.current = noticeId;
    loadData();
  }, [noticeId]);

  // Fetches both the notice and its comments.
  async function loadData() {
    setLoading(true);
    try {
      // getNotice also increments the view count on the backend side.
      const noticeData = await getNotice(noticeId, token);
      const commentsData = await getComments(noticeId, token);
      setNotice(noticeData);
      setComments(commentsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Toggles liking/unliking the notice itself (not a comment).
  async function handleLikeClick() {
    // Ignore clicks while a request is already running.
    if (likePending) return;

    setLikePending(true);
    try {
      if (liked) {
        // Already liked — this click means "unlike".
        await unlikeNotice(noticeId, token);
        // Update the like_count inside the notice object directly.
        setNotice((n) => ({ ...n, like_count: n.like_count - 1 }));
        setLiked(false);
      } else {
        // Not liked yet — this click means "like".
        await likeNotice(noticeId, token);
        setNotice((n) => ({ ...n, like_count: n.like_count + 1 }));
        setLiked(true);
      }
    } catch (err) {
      // Correct local state if the backend says we're out of sync,
      // instead of leaving the button stuck in the wrong mode.
      if (err.message.includes('already liked')) {
        setLiked(true);
      } else if (err.message.includes("haven't liked")) {
        setLiked(false);
      } else {
        console.error(err.message);
      }
    } finally {
      setLikePending(false);
    }
  }

  // Handles submitting a new comment.
  async function handlePostComment(e) {
    // Stop the browser's default full-page-reload form submission.
    e.preventDefault();
    setPosting(true);
    try {
      await postComment(noticeId, commentText, token);
      // Clear the textarea on success.
      setCommentText('');
      // Refetch comments so the new one shows up immediately.
      const commentsData = await getComments(noticeId, token);
      setComments(commentsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  }

  // ADMIN-only: deletes the whole notice, then returns to the dashboard.
  async function handleDeleteNotice() {
    try {
      await deleteNotice(noticeId, token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    }
  }

  // Passed down into CommentList so a deleted comment disappears from
  // this page's state immediately, without needing a full refetch.
  function handleCommentDeleted(commentId) {
    setComments((prev) => prev.filter((c) => c.id !== commentId));
  }

  // Show a loading message while the initial fetch is in progress.
  if (loading) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <p className="text-gray-400 text-center mt-8">Loading...</p>
      </div>
    );
  }

  // If loading finished but there's still no notice, either it doesn't
  // exist or the fetch failed — show whatever error message we have.
  if (!notice) {
    return (
      <div className="min-h-screen">
        <NavBar />
        <p className="text-red-400 text-center mt-8">{error || 'Notice not found'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <NavBar />
      <div className="max-w-2xl mx-auto p-8">
        {/* The notice itself: name, timestamp, message, view/like counts,
            and (if ADMIN) a delete button. */}
        <Card className="mb-6 text-left">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-semibold text-white">{notice.name}</h1>
            {/* Formats the ISO timestamp into a readable date/time. */}
            <span className="text-xs text-gray-500">{new Date(notice.created_at).toLocaleString()}</span>
          </div>
          <p className="text-gray-300 mb-4">{notice.message}</p>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>👁 {notice.view_count} views</span>
              {/* disabled while a request is running, so rapid clicks
                  can't fire duplicate requests. */}
              <button
                onClick={handleLikeClick}
                disabled={likePending}
                className={`${liked ? 'text-accent' : 'text-gray-400'} hover:text-accent transition-colors disabled:opacity-50`}
              >
                ❤ {notice.like_count}
              </button>
            </div>
            {/* Only rendered at all for ADMIN, matching the backend rule
                that only ADMIN can delete a notice. */}
            {user?.role === 'ADMIN' && (
              <button onClick={handleDeleteNotice} className="text-red-400 hover:text-red-300 text-sm">
                Delete Notice
              </button>
            )}
          </div>
        </Card>

        <h2 className="text-lg font-semibold text-white mb-3">Comments</h2>

        {/* Any logged-in user (ADMIN or MEMBER) can post a comment. */}
        <Card className="mb-4">
          <form onSubmit={handlePostComment} className="flex flex-col gap-3">
            <textarea
              placeholder="Write a comment..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              rows={2}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
            <Button type="submit" disabled={posting}>
              {posting ? 'Posting...' : 'Post Comment'}
            </Button>
          </form>
        </Card>

        {/* Only renders if there's actually an error to show. */}
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        {/* Either "no comments yet" or the actual list. */}
        {comments.length === 0 ? (
          <p className="text-gray-400 text-sm">No comments yet.</p>
        ) : (
          <CommentList comments={comments} token={token} user={user} onCommentDeleted={handleCommentDeleted} />
        )}
      </div>
    </div>
  );
}