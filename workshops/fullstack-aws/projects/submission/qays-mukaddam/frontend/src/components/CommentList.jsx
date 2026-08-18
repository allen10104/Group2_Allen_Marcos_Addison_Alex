import { useState } from 'react';
import { likeComment, unlikeComment, deleteComment } from '../api/api';
import Card from './Card';

// Renders the full list of comments for a notice. Receives the array
// plus a callback to update the parent's state when one gets deleted.
export default function CommentList({ comments, token, user, onCommentDeleted }) {
  return (
    <div className="flex flex-col gap-3">
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          token={token}
          user={user}
          onDeleted={onCommentDeleted}
        />
      ))}
    </div>
  );
}

// One individual comment: author, text, timestamp, like button, and a
// delete button that only shows if you're allowed to delete it.
function CommentItem({ comment, token, user, onDeleted }) {
  // Local like count, so clicking updates instantly.
  const [likeCount, setLikeCount] = useState(comment.like_count);
  // Same session-only limitation as NoticeCard's like button.
  const [liked, setLiked] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // True while a like/unlike request is in flight. Prevents rapid
  // repeat clicks from firing multiple requests before the first one's
  // response comes back and updates `liked`.
  const [likePending, setLikePending] = useState(false);

  // Mirrors the exact rule the backend enforces: author OR admin.
  const canDelete = user?.userId === String(comment.user_id) || user?.role === 'ADMIN';

  async function handleLikeClick() {
    // Ignore clicks while a request is already running.
    if (likePending) return;

    setLikePending(true);
    try {
      if (liked) {
        await unlikeComment(comment.id, token);
        setLikeCount((c) => c - 1);
        setLiked(false);
      } else {
        await likeComment(comment.id, token);
        setLikeCount((c) => c + 1);
        setLiked(true);
      }
    } catch (err) {
      // If the backend says we're out of sync, correct our local state
      // to match reality instead of leaving it stuck wrong.
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

  async function handleDeleteClick() {
    setDeleting(true);
    try {
      await deleteComment(comment.id, token);
      onDeleted(comment.id);
    } catch (err) {
      console.error(err.message);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Card className="text-left py-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-accent">{comment.username}</span>
        <span className="text-xs text-gray-500">{new Date(comment.created_at).toLocaleString()}</span>
      </div>
      <p className="text-gray-300 text-sm mb-2">{comment.text}</p>
      <div className="flex items-center gap-4 text-xs text-gray-400">
        <button onClick={handleLikeClick} disabled={likePending} className={`${liked ? 'text-accent' : 'text-gray-400'} hover:text-accent transition-colors disabled:opacity-50`}>
          ❤ {likeCount}
        </button>
        {canDelete && (
          <button onClick={handleDeleteClick} disabled={deleting} className="text-red-400 hover:text-red-300 disabled:opacity-50">
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        )}
      </div>
    </Card>
  );
}