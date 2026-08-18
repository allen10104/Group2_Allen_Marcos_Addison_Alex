// useEffect loads the notices when the list mounts and again whenever App
// asks for a refresh, useState holds them once they come back.
import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

import { listNotices } from "../api/notices";
import NoticeCard from "./NoticeCard";

// The list of notices.
//
// refreshKey is how App triggers a refetch. App changes the number after a
// successful create or delete, the effect below sees a new dependency value
// and loads the list again. Passing a number rather than a function keeps
// this component in charge of its own fetching, and avoids the loop that
// comes from putting a freshly created callback in a dependency array.
//
// onDeleted is passed straight down to each card, so a delete refreshes the
// list the same way a create does.
function NoticeList({ refreshKey, onDeleted }) {
  const [notices, setNotices] = useState([]);

  // Starts true because this component fetches as soon as it mounts, so the
  // spinner shows immediately instead of a flash of "No notices yet" before
  // the first response lands.
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Set when this effect is cleaned up, which happens if refreshKey
    // changes again while a request is still in flight, or if the component
    // unmounts. Without it a slow first response could land after a faster
    // second one and put stale notices back on screen.
    let cancelled = false;

    const loadNotices = async () => {
      setError("");

      try {
        const data = await listNotices();

        if (!cancelled) {
          setNotices(data);
        }
      } catch (err) {
        console.error(err);

        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadNotices();

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  // The spinner only replaces the list on the very first load, because
  // loading is never set back to true. A refetch after a create leaves the
  // existing notices on screen until the new ones arrive, which avoids the
  // whole page blinking every time someone posts.
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // A failed load is shown on its own, since there is nothing to list. A
  // failed refetch after a create shows this too, which is the honest
  // outcome: we no longer know what the board holds.
  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (notices.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
        No notices yet
      </Typography>
    );
  }

  return (
    <Stack spacing={2}>
      {notices.map((notice) => (
        // Keyed by id rather than by array index. React uses the key to
        // decide which card is which between renders, and an index would
        // make deleting the first notice look like every card changed.
        <NoticeCard key={notice.id} notice={notice} onDeleted={onDeleted} />
      ))}
    </Stack>
  );
}

export default NoticeList;
