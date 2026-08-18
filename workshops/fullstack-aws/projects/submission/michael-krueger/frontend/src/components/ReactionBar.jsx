import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Alert, Box, Button, Snackbar, Tooltip, Typography } from "@mui/material";

import FavoriteIcon from "@mui/icons-material/Favorite";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import EmojiEmotionsIcon from "@mui/icons-material/EmojiEmotions";
import EmojiEmotionsOutlinedIcon from "@mui/icons-material/EmojiEmotionsOutlined";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";

import { toggleReaction } from "../api/reactions";
import { useAuth } from "../context/AuthContext";

// The three kinds, paired with their filled and outlined icons and the words
// used in the tooltip.
//
// Kept as one list so the buttons below are rendered by mapping over it
// rather than being written out three times. Adding a fourth kind, once the
// backend allows one, is then a single entry here.
//
// The type strings must match what the backend accepts. Anything else comes
// back as a 422.
const REACTIONS = [
  {
    type: "like",
    label: "Like",
    ActiveIcon: ThumbUpIcon,
    InactiveIcon: ThumbUpOutlinedIcon,
  },
  {
    type: "heart",
    label: "Love",
    ActiveIcon: FavoriteIcon,
    InactiveIcon: FavoriteBorderIcon,
  },
  {
    type: "laugh",
    label: "Laugh",
    ActiveIcon: EmojiEmotionsIcon,
    InactiveIcon: EmojiEmotionsOutlinedIcon,
  },
];

// The row of reaction buttons under one notice.
//
// reactions is the summary the board fetched, { counts, my_reactions }. A
// filled icon means that kind is in my_reactions, so the reader can see at a
// glance which ones are theirs.
function ReactionBar({ noticeId, reactions }) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // The summary this bar is drawing.
  //
  // Held locally so a toggle can redraw from the response without the whole
  // board being refetched, which would make every other notice flicker for
  // the sake of one number.
  const [summary, setSummary] = useState(reactions);

  // Which kind is currently in flight, or null. Storing the type rather than
  // a boolean is what allows only the clicked button to be disabled while
  // the other two stay usable.
  const [pending, setPending] = useState(null);

  const [error, setError] = useState("");

  // Take the summary from the board again whenever it arrives fresh.
  //
  // NoticeList refetches after a create or a delete and hands down new notice
  // objects. Without this the local state above would win forever, and this
  // bar would keep showing the counts from whenever it first mounted,
  // ignoring reactions other people had added since.
  //
  // The dependency is the prop's identity, which only changes when the board
  // actually refetches, so a toggle's own result is not immediately
  // overwritten by a re-render.
  useEffect(() => {
    setSummary(reactions);
  }, [reactions]);

  const handleToggle = async (reactionType) => {
    // Caught here rather than letting the request go and handling the 401.
    // The backend would refuse it anyway, so this only saves a round trip
    // and replaces a failure message with the page that fixes it.
    //
    // Sending the current location along means logging in returns the reader
    // to the board rather than dropping them somewhere generic.
    if (!isAuthenticated) {
      navigate("/login", { state: { from: { pathname: "/" } } });
      return;
    }

    setPending(reactionType);
    setError("");

    try {
      const updated = await toggleReaction(noticeId, reactionType);

      // The response is the whole updated summary, counts and all, so it
      // replaces the local one outright. No arithmetic here means the
      // numbers on screen are the numbers the database holds, including
      // reactions other people added while this request was in flight.
      setSummary(updated);
    } catch (err) {
      console.error(err);

      // A 401 here means the token expired between the page loading and this
      // click. The Axios interceptor has already cleared it, so the app knows
      // it is logged out, and the useful response is the login page rather
      // than an error about it.
      if (err.status === 401) {
        navigate("/login", { state: { from: { pathname: "/" } } });
        return;
      }

      setError(err.message);
    } finally {
      // In a finally block so the button unlocks whether the toggle
      // succeeded or failed. Leaving it out of the catch path would leave
      // one button disabled forever after a single error.
      setPending(null);
    }
  };

  // Defensive defaults. The backend always sends both fields, but a notice
  // that reached here from anywhere else should still render a bar of zeroes
  // rather than crashing the whole list on a missing property.
  const counts = summary?.counts || {};

  // Nothing is "mine" while signed out, whatever the last fetch happened to
  // contain. The backend already sends an empty my_reactions to an
  // anonymous caller, so normally these agree.
  //
  // They come apart when a token expires in an open tab: the notices on
  // screen were fetched while signed in and still carry this reader's
  // reactions, but the app now knows it is logged out. Without this the bar
  // would keep showing filled icons for an account that is no longer
  // signed in, and clicking one would bounce to the login page, which reads
  // as a bug rather than as a session that quietly ended.
  const mine = isAuthenticated ? summary?.my_reactions || [] : [];

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 1 }}>
      {REACTIONS.map(({ type, label, ActiveIcon, InactiveIcon }) => {
        const active = mine.includes(type);
        const Icon = active ? ActiveIcon : InactiveIcon;
        const count = counts[type] ?? 0;

        return (
          // The tooltip explains what an icon on its own does not, and says
          // what clicking will do rather than just naming the reaction.
          <Tooltip
            key={type}
            title={
              isAuthenticated
                ? `${active ? "Remove your" : "Add a"} ${label.toLowerCase()}`
                : `Log in to ${label.toLowerCase()}`
            }
          >
            {/* The span is here because MUI's Tooltip needs a child that can
                hold a ref and fire hover events, and a disabled button fires
                neither. Without it the tooltip breaks mid request. */}
            <span>
              <Button
                // A Button rather than an IconButton, because each one has to
                // show a number beside its icon and IconButton is built to
                // hold a single glyph. size small keeps it close to the
                // footprint an IconButton would have had.
                size="small"
                onClick={() => handleToggle(type)}
                // Only the button being toggled is disabled. The other two
                // stay live, so three quick reactions do not have to be made
                // one at a time.
                disabled={pending === type}
                // Colour is what carries "this one is mine" for anyone who
                // does not notice the difference between a filled and an
                // outlined icon.
                color={active ? "primary" : "inherit"}
                aria-label={`${label}, ${count} so far`}
                // aria-pressed is what tells a screen reader this is a
                // toggle and which state it is in. Without it the button
                // announces as an ordinary action.
                aria-pressed={active}
                startIcon={<Icon fontSize="small" />}
                sx={{ minWidth: 0, px: 1 }}
              >
                <Typography variant="body2" component="span">
                  {count}
                </Typography>
              </Button>
            </span>
          </Tooltip>
        );
      })}

      {/* A Snackbar rather than an inline Alert, so a failed toggle does not
          push the notice below it down the page. It closes itself, since the
          reader can simply click again. */}
      <Snackbar
        open={error !== ""}
        autoHideDuration={5000}
        onClose={() => setError("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="error" onClose={() => setError("")}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ReactionBar;
