import { useState } from "react";

import {
  Alert,
  Card,
  CardContent,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";

import DeleteIcon from "@mui/icons-material/Delete";

import { deleteNotice } from "../api/notices";
import { useAuth } from "../context/AuthContext";
import ReactionBar from "./ReactionBar";

// Turns the timestamp the backend sends into something readable.
//
// created_at arrives as an ISO string with a UTC offset, because the column
// is timestamptz. new Date parses that and toLocaleString renders it in the
// reader's own timezone, which is the point of storing it that way.
//
// Falls back to the raw string if parsing fails, so a notice with an
// unexpected timestamp still renders instead of showing "Invalid Date" or
// taking the whole list down.
function formatCreatedAt(createdAt) {
  const parsed = new Date(createdAt);

  if (Number.isNaN(parsed.getTime())) {
    return createdAt;
  }

  return parsed.toLocaleString();
}

// One notice, with the button that deletes it.
//
// onDeleted is called after the backend confirms the delete, which tells
// App to refetch. As with the form, nothing is removed from the list here:
// the refetch is what makes the screen agree with the database.
function NoticeCard({ notice, onDeleted }) {
  const { user } = useAuth();

  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  // Whether to show the delete button at all.
  //
  // user is null while logged out, so nobody sees a delete button on a board
  // they are only reading. When signed in, it appears on their own notices
  // and not on anybody else's.
  //
  // user.id is already a number: the token carries it as a string in the
  // "sub" claim, because the JWT spec requires that, and userFromToken
  // converts it. Without that conversion this comparison would be "1" === 1,
  // which is false, and the button would be hidden on every notice
  // including the user's own.
  //
  // This is presentation only and not a security control. Hiding a button
  // stops nobody from calling the API directly, which is why the backend
  // checks ownership again and answers 403. The point here is not to offer
  // an action that is going to be refused.
  const canDelete = user !== null && user.id === notice.user_id;

  const handleDelete = async () => {
    setDeleting(true);
    setError("");

    try {
      await deleteNotice(notice.id);

      onDeleted();
    } catch (err) {
      console.error(err);

      // A 404 here means someone else deleted this notice first, which is
      // worth saying in plainer words than the backend's own "Notice not
      // found". The list is refetched either way, so the stale card
      // disappears on its own.
      setError(err.message);

      // Only re-enabled on failure. On success this component is about to
      // be unmounted by the refetch, and setting state on the way out would
      // be pointless work.
      setDeleting(false);
    }
  };

  return (
    <Card variant="outlined">
      <CardContent>
        {/* justifyContent and alignItems go through sx rather than being
            passed as props. This version of MUI does not accept them as
            Stack props any more: they fall through to the underlying div,
            React warns that it does not recognise them, and the alignment
            silently does not apply. direction and spacing are real Stack
            props and stay where they are. */}
        <Stack
          direction="row"
          spacing={2}
          sx={{ justifyContent: "space-between", alignItems: "flex-start" }}
        >
          <div>
            <Typography variant="subtitle1" fontWeight="bold">
              {notice.name}
            </Typography>

            <Typography variant="caption" color="text.secondary">
              {formatCreatedAt(notice.created_at)}
            </Typography>

            {/* whiteSpace pre-wrap keeps the line breaks someone typed into
                the message box. Without it the browser collapses them and
                every notice renders as one run-on paragraph. */}
            <Typography sx={{ mt: 1, whiteSpace: "pre-wrap" }}>
              {notice.message}
            </Typography>
          </div>

          {/* Hidden rather than disabled on somebody else's notice. A
              disabled button still says "this is an action you might have",
              which is misleading when the answer will always be no. */}
          {canDelete && (
            <Tooltip title="Delete this notice">
              {/* The span is here because MUI's Tooltip needs a child that
                  can hold a ref and fire hover events, and a disabled button
                  fires neither. Without it the tooltip breaks once deleting
                  starts. */}
              <span>
                <IconButton
                  aria-label={`Delete notice from ${notice.name}`}
                  onClick={handleDelete}
                  disabled={deleting}
                  size="small"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          )}
        </Stack>

        {/* The reaction bar sits below the message and spans the card,
            outside the Stack above so it is not squeezed into the same row
            as the delete button.

            reactions is passed straight through from the notice the board
            fetched. ReactionBar keeps its own copy from then on, so a toggle
            redraws only this notice rather than refetching the whole list.

            The fallback covers a notice served by a backend from before
            reactions existed, which would have no reactions field at all.
            Without it the bar would read counts off undefined. */}
        <ReactionBar
          noticeId={notice.id}
          reactions={notice.reactions || { counts: {}, my_reactions: [] }}
        />

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

export default NoticeCard;
